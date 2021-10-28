"""Update or create a stack given a name and template + params"""

from __future__ import division, print_function, unicode_literals

import json
import logging
import os
import sys
from datetime import datetime

import boto3
import botocore
from botocore.exceptions import ClientError, WaiterError

log = logging.getLogger('deploy.cf.create_or_update')  # pylint: disable=C0103


class Scheduler(object):
    """QS SPICE Dataset Schedule Optimization Class."""

    def __init__(self):
        """Constructor."""
        self.__author__ = 'sabtahiz[at]amazon[dot]com'
        self._name = 'scheduler'
        self.__debug_level = 5
        self.__debug_info_level = 3
        self.LOGGER = logging.getLogger()
        self.LOGGER.setLevel(logging.INFO)

        self.__load_config()

        try:
            self._today = datetime.now().strftime("%Y-%m-%d-%H-%M-%S")
        except ValueError:
            self._index_error = True

        try:
            self._session = boto3.Session(profile_name=self.aws_profile, region_name=self.aws_region)
            self._qs = self._session.client('quicksight')
            self.cf = self._session.client('cloudformation')
            self.sns = self._session.client('sns')
        except ClientError:
            self._index_error = True

    def __load_config(self):
        """Load configuration parameters."""
        # self.__config_file = '../configuration/config.json'

        try:
            for root, dirs, files in os.walk('..', topdown=False):
                for file in files:
                    if file == 'config.json':
                        self.__config_file = os.path.join(root, file)
        except (OSError, KeyError):
            pass

        try:
            with open(self.__config_file, 'r') as f:
                config = json.load(f)
                self.deployment = config["deployment"]
                self.datasets = config["datasets"]
                self.aws_profile = config["aws_profile"]
                self.aws_region = config["aws_region"]
                self.stack_name = config["stackname"]
                self.ignore = config["ignore"]
                self.account = config["account"]
                self.search = config["search"]
            if not self.account:
                print('-- You need to provide AWS Account ID in config file!')
                sys.exit(1)
            if not self.datasets:
                print('-- You need to provide datasets interval in config file!')
                sys.exit(1)
            for k, v in self.datasets.items():
                self.LOGGER.info('-- Dataset: %s | Target schedule rate: %s', k, v)
        except IOError as e:
            raise e

    def __write_config(self, _ans):
        """Write new configuration to the config file."""
        try:
            with open(self.__config_file, 'r') as f:
                config = json.load(f)
            # config["target_datasets"] = _ans
            for k, v in _ans.items():
                self.LOGGER.info('-- Dataset: %s | Target schedule rate: %s', k, v)
            with open(self.__config_file, 'w') as json_file:
                json.dump(config, json_file)
                self.LOGGER.info('-- Config file updated successfully.')
        except IOError as e:
            raise e

    def main(self, template, parameters):
        'Update or create stack'
        template_data = self._parse_template(template)
        parameter_data = self._parse_parameters(parameters)

        params = {
            'StackName': self.stack_name,
            'TemplateBody': template_data,
            'Parameters': parameter_data,
            'Capabilities': ["CAPABILITY_IAM"]
        }

        try:
            if self._stack_exists():
                print('Updating {}'.format(self.stack_name))
                stack_result = self.cf.update_stack(**params)
                waiter = self.cf.get_waiter('stack_update_complete')
            else:
                print('Creating {}'.format(self.stack_name))
                stack_result = self.cf.create_stack(**params)
                waiter = self.cf.get_waiter('stack_create_complete')
            print("...waiting for stack to be ready...")
            try:
                waiter.wait(StackName=self.stack_name)
            except WaiterError:
                log.info('-- Waiter in process ...')
        except botocore.exceptions.ClientError as ex:
            error_message = ex.response['Error']['Message']
            if error_message == 'No updates are to be performed.':
                print("No changes")
            else:
                raise
        else:
            print(json.dumps(
                self.cf.describe_stacks(StackName=stack_result['StackId']),
                indent=2,
                default=self.json_serial
            ))

    def _parse_template(self, template):
        with open(template) as template_fileobj:
            template_data = template_fileobj.read()
        self.cf.validate_template(TemplateBody=template_data)
        return template_data

    def _stack_exists(self):
        stacks = self.cf.list_stacks()['StackSummaries']
        for stack in stacks:
            if stack['StackStatus'] == 'DELETE_COMPLETE':
                continue
            if self.stack_name == stack['StackName']:
                return True
        return False

    def _pile_up_stack(self, _ans):
        with open(self.deployment + "temp_stack.yaml", "w") as file_temp_stack:
            with open(self.deployment + "stack.yaml", "r") as file_stack:
                file_temp_stack.write(file_stack.read())
                with open(self.deployment + "event.yaml", "r") as file_event:
                    content = file_event.read()
                    for k, v in _ans.items():
                        file_temp_stack.write(self.replace_rate(content, k, v))
        return True

    def _auto_fetch(self):
        """Fetches dataset info from QS API."""
        ans = list()
        final = dict()
        try:
            response = self._qs.list_data_sets(AwsAccountId=self.account)
            while True:
                for res in response['DataSetSummaries']:
                    if res["Name"] not in self.ignore:
                        ans.append(res["Name"])
                try:
                    response = self._qs.list_data_sets(AwsAccountId=self.account, NextToken=response["NextToken"])
                except KeyError:
                    break
        except Exception as e:
            self.LOGGER.error(e)
        if not ans:
            self.LOGGER.info('-- ERROR! No dataset found for this account.')
            sys.exit(0)
        else:
            print('\n')
            print('-' * 91)
            for ds in ans:
                print('-- Target dataset: ' + str(ds))
            print('-' * 91)

            for k, v in self.datasets.items():
                if k in ans:
                    final[k] = self._build_schedule(v)
                    print('-- New schedule interval for dataset: ' + str(k) + ' is going to be: ' + str(v))
                else:
                    print('-- WARNING! Dataset does not exist: ' + str(k))

        print('-' * 91)
        return final

    @staticmethod
    def _parse_parameters(parameters):
        with open(parameters) as parameter_fileobj:
            parameter_data = json.load(parameter_fileobj)
        return parameter_data

    @staticmethod
    def json_serial(_obj):
        """JSON serializer for objects not serializable by default json code"""
        if isinstance(_obj, datetime):
            serial = _obj.isoformat()
            return serial
        raise TypeError("Type not serializable")

    @staticmethod
    def replace_rate(stack_content, target, rate):
        target_append = target.lower().replace(' ', '').replace('_', '')
        return stack_content.replace("_TARGET", target).replace("_RATE", rate) \
            .replace("ScheduledRule", "ScheduledRule" + target_append.replace('-', '')) \
            .replace("PermissionInvoke", "PermissionInvoke" + target_append.replace('-', ''))

    @staticmethod
    def _build_schedule(_value):
        """Build Cron expression.
           Every X minute past X minutes of the hour.
        """
        return 'cron(' + str(_value) + '-59/' + str(_value) + ' * * * ? *' + ')'

    def _launch(self):
        """Launch app."""
        # Cleanup temp stack
        tmp_path = self.deployment + 'temp_stack.yaml'
        try:
            os.remove(tmp_path)
        except FileNotFoundError:
            pass

        ans = self._auto_fetch()
        self.LOGGER.info('-- Launching stack ...')
        if self._pile_up_stack(ans):
            print('-- Temporary stack solution is created.')
        else:
            print('-- Error creating temporary stack!')

        self.LOGGER.info('-- Deployment in process ...')
        self.main(self.deployment + "temp_stack.yaml", self.deployment + "params.json")
        self.LOGGER.info('-- Updating config file based on user input.')
        self.__write_config(ans)
        print('-- Done.')
        sys.exit(0)


if __name__ == '__main__':
    obj = Scheduler()
    obj._launch()
