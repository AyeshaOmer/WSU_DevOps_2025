import boto3

client = boto3.client("cloudwatch")

def publish(namespace, metricName,  url, value):
  response = client.put_metric_data(
          Namespace=namespace,
          MetricData=[
              {
                  "MetricName": metricName,
                  "Dimensions": [
                      {
                          "Name": "URL",
                          "Value": url
                      }
                  ],
                  "Value": value,
              },
          ]
      )