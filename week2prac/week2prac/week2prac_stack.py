from aws_cdk import (
    Duration,
    Stack,
    aws_iam as iam,
)
from aws_cdk.aws_synthetics_alpha import Canary, Schedule, Runtime, Code, Test
from constructs import Construct

class Week2PracStack(Stack):

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        canary = Canary(self, "WebMonitorCanary",
            canary_name="nytimes-monitor",
            runtime=Runtime.SYNTHETICS_NODEJS_PUPPETEER_3_9,
            test=Test.custom(
                code=Code.from_inline("""
                    const synthetics = require('Synthetics');
                    const log = require('SyntheticsLogger');

                    const pageLoadBlueprint = async function () {
                        let page = await synthetics.getPage();  
                        const url = 'https://www.nytimes.com';
                        const response = await page.goto(url, { waitUntil: 'load', timeout: 30000 });

                        const status = response.status();
                        log.info("HTTP Status Code: " + status);

                        if (status !== 200) {
                            throw new Error("Failed to load page with status: " + status);
                        }
                    };

                    exports.handler = async () => {
                        return await pageLoadBlueprint();
                    };
                """),
                handler="index.handler"
            ),
            schedule=Schedule.rate(Duration.minutes(5)),
            start_after_creation=True
        )

        canary.role.add_managed_policy(
            iam.ManagedPolicy.from_aws_managed_policy_name("CloudWatchSyntheticsFullAccess")
        )
