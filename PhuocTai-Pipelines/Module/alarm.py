import aws_cdk.aws_cloudwatch as cloudwatch
import ObtainMetrics 


threshold_avail = ObtainMetrics.avail
threshold_latency = ObtainMetrics.latency

def create_alarms(self, URL_metrics):
    alarm_avail = cloudwatch.Alarm(self, "AvailabilityAlarm",
                                   alarm_name="AvailabilityAlarm",
                                   metric=URL_metrics[ObtainMetrics.URL_MONITOR_AVAILABILITY],
                                   threshold=threshold_avail,
                                   evaluation_periods=1,
                                   comparison_operator=cloudwatch.ComparisonOperator.LESS_THAN_THRESHOLD,
                                   treat_missing_data=cloudwatch.TreatMissingData.BREACHING
                                   )

    alarm_latency = cloudwatch.Alarm(self, "LatencyAlarm",
                                     alarm_name="LatencyAlarm",
                                     metric=URL_metrics[ObtainMetrics.URL_MONITOR_LATENCY],
                                     threshold=threshold_latency,
                                     evaluation_periods=1,
                                     comparison_operator=cloudwatch.ComparisonOperator.GREATER_THAN_THRESHOLD,
                                     treat_missing_data=cloudwatch.TreatMissingData.BREACHING
                                     )
    
    return alarm_avail, alarm_latency
