"""Execute Unit Tests for the App source code."""

from __future__ import division, print_function, unicode_literals

import json
import os
from unittest import TestCase

from scheduler import Scheduler


class Test(TestCase):
    """The main class that inherits unittest.TestCase."""
    sc = Scheduler()

    def test_0_config(self):
        """Tests config file."""
        _config_file = 'config.json'
        self.assertTrue(os.path.exists('config.json'))

        try:
            for root, dirs, files in os.walk('.', topdown=False):
                for file in files:
                    if file == 'config.json':
                        _config_file = os.path.join(root, file)
        except (OSError, KeyError):
            pass

        try:
            with open(_config_file, 'r') as f:
                config = json.load(f)
                self.assertIsNotNone(config["targets"])
                self.assertIsNotNone(config["aws_profile"])
                self.assertIsNotNone(config["aws_region"])
                self.assertIsNotNone(config["stackname"])
                self.assertIsNotNone(config["ignore"])
                self.assertIsNotNone(config["account"])
                self.assertIsNotNone(config["env"])
                self.assertIsNotNone(config["MIN"])
                self.assertIsNotNone(config["MAX"])
        except IOError as e:
            raise e

    def test_1_cft_path(self):
        """CFT & Lambda directory should exist and remain unchanged."""
        self.assertTrue(os.path.exists('../cft/event.yaml'))
        self.assertTrue(os.path.exists('../cft/stack.yaml'))
        self.assertTrue(os.path.exists('../cft/params.json'))
        self.assertTrue(os.path.exists('../lambda_source/index.py'))

    def test_2_scheduler_vars(self):
        """Test variables of the scheduler class."""
        obj = Scheduler()
        self.assertIsNotNone(obj._name)
        self.assertIsNotNone(obj._session)
        self.assertIsNotNone(obj._qs)
        self.assertIsNotNone(obj.LOGGER)
        self.assertIsNotNone(obj.cf)
        self.assertIsNotNone(obj.sns)
