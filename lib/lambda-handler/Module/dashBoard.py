import aws_cdk.aws_cloudwatch as cw
import ObtainMetrics
from aws_cdk import Duration

def create_dashboard(self, URL_metrics,
                     
    default_interval=Duration.minutes(1),
    variables = [cw.DashboardVariable(
                    id= "URL",
                    type= cw.VariableType.STRING,
    )]
):
    dashboard = cw.Dashboard(self, "PhuocTaiTranDashboard",
                             dashboard_name="PhuocTaiTranDashboard",
                             start="-PT3H",
                             period_override=cw.PeriodOverride.AUTO,
                             default_interval=default_interval,
                             variables=variables
                             )
    
    availability_widget = cw.GraphWidget(
        title="URL Availability",
        left=[URL_metrics[ObtainMetrics.URL_MONITOR_AVAILABILITY]],
        left_y_axis=cw.YAxisProps(min=0, max=1),
        width=24,
        height=6,
    )

    latency_widget = cw.GraphWidget(
        title="URL Latency",
        left=[URL_metrics[ObtainMetrics.URL_MONITOR_LATENCY]],
        left_y_axis=cw.YAxisProps(min=0),
        width=24,
        height=6,
    )

    dashboard.add_widgets(availability_widget)
    dashboard.add_widgets(latency_widget)

    return dashboard