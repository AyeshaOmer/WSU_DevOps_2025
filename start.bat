@echo off
call cdk synth
call cdk deploy --require-approval never