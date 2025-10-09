@echo off
call cdk destroy --all --force
call cdk synth
call cdk -a "python app.py" deploy PatDowdPipelineStack --require-approval=never