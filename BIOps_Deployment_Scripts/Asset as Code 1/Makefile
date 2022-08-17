# This makefile is used to update a pipeline and all the resources  with it. This includes
# the CodePipeline and the associated CodeBuild jobs.
#
#
# Enviroment variables: AWS_DEFAULT_PROFILE and AWS_DEFAULT_REGION
#
#
# Commands:
# make get-pipeline - Will pull down the pipeline and associated parameters. There will be
# 	two parameter files in addtion to the CodePipeline/pipeline.yml.
#		CodePipeline/pipeline.yml: contains the CloudFormation for the pipeline and the
#			associated CodeBuild jobs. Make edits in this file to change the properties of
#			the resources.
#		CodePipeline/currentparams.json: contains the current values for the parameters
#			for the pipeline
#		CodePipeline/newparams.json: determines whether or not the parameter values should be
#			updated	if you want to update a value. Change it in this file.
# make put-pipeline - This will update the pipeline with the CodePipeline/pipeline.yml
#		file and the parameters in CodePipeline/newparams.json
#
#
# Example use cases:
# AWS_DEFAULT_PROFILE=<profilename> AWS_DEFAULT_REGION=us-east-1 make get-pipeline
# AWS_DEFAULT_PROFILE=<profilename> AWS_DEFAULT_REGION=us-east-1 make put-pipeline

CFN_TEMPLATES := $(wildcard CloudFormation/*.template)
PIPELINE_CFN_NAME := 'pr-biat-content-pipeline-PRPipeline'
PIPELINE_NAME := 'biat-content'

help:
	@echo "Targets:"
	@echo "    get-pipeline  -- Download the pipline CFN template for into CodePipeline/pipeline.yml"
	@echo "    put-pipeline  -- Update the pipeline with CodePipeline/pipeline.yml"

get-pipeline:
	@echo "Downloading pipeline template"
	@mkdir -p CodePipeline
	@aws cloudformation get-template --stack-name $(PIPELINE_CFN_NAME) \
		--query 'TemplateBody' --output text > CodePipeline/pipeline.yml
	@echo "Downloading current pipeline stack params"
	@aws cloudformation describe-stacks --stack-name $(PIPELINE_CFN_NAME) \
		--query 'Stacks[0].Parameters' > CodePipeline/currentparams.json
	@echo "Setting UsePreviousValue to true for all new params"
	# Replace all ParameterValues with UsePreviousValue.
	@sed  's/.*"ParameterValue":.*,/        "UsePreviousValue": true,/' CodePipeline/currentparams.json > \
		CodePipeline/newparams.json.tmp
	# Sort parameter objects, jq formats json properly and removes extra commas from previous command
	@jq 'walk(if type == "object" then to_entries | sort | from_entries else . end)' CodePipeline/newparams.json.tmp \
	>> CodePipeline/newparams.json
	@rm -f CodePipeline/newparams.json.tmp

put-pipeline:
	@echo "Updating pipeline"
	@if aws codepipeline get-pipeline-state --name $(PIPELINE_NAME) | grep -q '"status": "InProgress"';then \
		echo "ERROR: Pipeline is in progress, please wait until it's complete before updating."; \
		exit 1; \
	else \
	        true; \
	fi
	@aws cloudformation update-stack --stack-name $(PIPELINE_CFN_NAME) \
		--template-body file://CodePipeline/pipeline.yml \
		--parameters file://CodePipeline/newparams.json
	@aws cloudformation wait stack-update-complete --stack-name $(PIPELINE_CFN_NAME)
	@aws cloudformation describe-stacks --stack-name $(PIPELINE_CFN_NAME) --output text --query 'Stacks[0].StackStatus'

cloudformation:
	@for f in $(CFN_TEMPLATES); do \
		echo $$f; \
		aws cloudformation validate-template --template-body file://$$f || break; \
	done

.PHONY: pipeline cloudformation