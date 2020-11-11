#!/usr/bin/env python3

from aws_cdk import core

from granular_access.granular_access_stack import GranularAccessStack


app = core.App()
GranularAccessStack(app, "granular-access")

app.synth()
