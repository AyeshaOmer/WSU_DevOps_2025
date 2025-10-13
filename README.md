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
