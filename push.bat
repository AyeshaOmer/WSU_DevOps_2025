@echo off
call git add .
call git commit -m "scripted"
call git push
call cdk destroy --all --force
call cdk synth PatDowdPipelineStack
call cdk deploy PatDowdPipelineStack --require-approval=never 