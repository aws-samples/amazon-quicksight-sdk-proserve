#!/usr/bin/env python3

from aws_cdk import core

from administrative_dashboard.administrative_dashboard_stack import QuickSightStack


app = core.App()
QuickSightStack(app, "QuickSightStack", env={'region': 'us-east-1'})

app.synth()