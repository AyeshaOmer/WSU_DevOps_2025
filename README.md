# WSU_DevOps_2025

This is a repo for the 2025 batch of DevOps Course.

## Week 10: Pipeline Stages and Testing

What was added/changed:
- Added multi‑stage CDK Pipeline: `Beta` → `Gamma` → `Staging` → `Prod`.
- Inserted a manual approval gate before deploying to `Prod`.
- Post‑deploy test steps now run for all stages (including `Staging`).
- Added unit tests for the web crawler logic (`WHLambda.crawl_url`).
- Added CDK assertion tests for the WebHealth stack resources.
- Pipeline runs unit tests before synthesis to fail fast.

### Files of interest
- Pipeline definition: `Thomas/thomas/thomas_stack.py`
- Web crawler code: `DangQuocToan/modules/WHLambda.py`
- Crawler unit tests: `DangQuocToan/tests/unit/test_whlambda.py`
- CDK infra tests: `DangQuocToan/tests/unit/test_infra.py`
- Stage tests: `Thomas/tests/{beta,gamma,staging,prod}/test_dummy.py`

### Run tests locally
From the repo root:

```
pip install -r Thomas/requirements.txt
pytest DangQuocToan/tests/unit -q
pytest Thomas/tests/unit -q
```

### Synthesize and deploy
```
cd Thomas
cdk synth
cdk deploy ThomasStack
```

### How the approval works
The pipeline includes a `ManualApprovalStep` before `Prod`. After `Staging` passes, a human must approve the change in CodePipeline for the `Prod` stage to run.

### Notes
- The crawler tests stub network calls and `boto3` so they run offline.
- Adjust websites in `DangQuocToan/modules/website.json` to change monitored URLs.

## Week 11: Ops Metrics and Rollback

Added in Week 11:
- Operational CloudWatch alarms on the crawler Lambda: `Errors`, `Throttles`, `p99 Duration`, `Invocations (low)`, and `MaxMemoryUsed`.
- SNS notifications wired to the same alarm topic as URL health.
- Lambda version + `live` alias, and a CodeDeploy `LambdaDeploymentGroup` with `CANARY_10PERCENT_5MINUTES` traffic shifting.
- Automatic rollback: CodeDeploy monitors alarms and rolls back if they breach during deployment.

Where to look:
- Lambda + alarms + CodeDeploy: `DangQuocToan/dang_quoc_toan/dang_quoc_toan_stack.py`
- Infra tests covering alias/CodeDeploy: `DangQuocToan/tests/unit/test_infra.py`

Validate locally:
```
pip install -r Thomas/requirements.txt
pytest DangQuocToan/tests/unit -q
```

Deploy notes:
- Pipeline deploys the stack and uses CodeDeploy for Lambda traffic shifting.
- Prod requires manual approval (Week 10) and will rollback automatically (Week 11) if alarms breach.

CodeDeploy in CI/CD:
- The pipeline synthesizes with `-c enable_code_deploy=false` to avoid account/region subscription issues.
- To enable CodeDeploy, synthesize/deploy with context: `cd Thomas && cdk synth -c enable_code_deploy=true` and then `cdk deploy ThomasStack -c enable_code_deploy=true`.
- You may need to visit the CodeDeploy console once in your target region to initialize the service and ensure the service-linked role exists.
