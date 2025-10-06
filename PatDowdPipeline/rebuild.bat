@echo off
call cdk destroy --all --force
call cdk synth
call cdk deploy --require-approval never