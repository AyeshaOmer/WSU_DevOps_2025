@echo off
call cdk destroy --all --force
call cdk synth PatDowdPipelineStack
call cdk deploy PatDowdPipelineStack --require-approval=never 