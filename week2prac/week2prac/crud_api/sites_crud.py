import json
import boto3
import uuid
import os
from datetime import datetime
from typing import Dict, Any, Optional
from botocore.exceptions import ClientError

# Initialize AWS resources
dynamodb = boto3.resource('dynamodb')
cloudwatch = boto3.client('cloudwatch')
table_name = os.environ.get('SITES_TABLE_NAME', 'Sites')
table = dynamodb.Table(table_name)

# Environment variables for CloudWatch operations
METRIC_NAMESPACE = os.environ.get('METRIC_NAMESPACE', 'NYTMonitor')
SNS_TOPIC_ARN = os.environ.get('SNS_TOPIC_ARN', '')
DASHBOARD_NAME = os.environ.get('DASHBOARD_NAME', 'WebHealthDashboard')


def lambda_handler(event: Dict[str, Any], context) -> Dict[str, Any]:
    """
    Lambda function to handle CRUD operations for website targets.
    
    Expected API Gateway event structure:
    - httpMethod: GET, POST, PUT, DELETE
    - pathParameters: {site_id} for individual operations
    - body: JSON payload for POST/PUT operations
    """
    try:
        http_method = event.get('httpMethod', '')
        path_parameters = event.get('pathParameters') or {}
        site_id = path_parameters.get('site_id')
        
        # Parse request body if present
        body = {}
        if event.get('body'):
            try:
                body = json.loads(event['body'])
            except json.JSONDecodeError:
                return error_response(400, 'Invalid JSON in request body')
        
        # Route to appropriate CRUD operation
        if http_method == 'GET':
            if site_id:
                return get_site(site_id)
            else:
                return list_sites()
        elif http_method == 'POST':
            return create_site(body)
        elif http_method == 'PUT':
            if not site_id:
                return error_response(400, 'site_id is required for PUT operations')
            return update_site(site_id, body)
        elif http_method == 'DELETE':
            if not site_id:
                return error_response(400, 'site_id is required for DELETE operations')
            return delete_site(site_id)
        else:
            return error_response(405, f'Method {http_method} not allowed')
            
    except Exception as e:
        print(f"Unexpected error: {str(e)}")
        return error_response(500, 'Internal server error')


def get_site(site_id: str) -> Dict[str, Any]:
    """Get a single site by ID."""
    try:
        response = table.get_item(Key={'site_id': site_id})
        
        if 'Item' not in response:
            return error_response(404, f'Site with ID {site_id} not found')
            
        return success_response(response['Item'])
        
    except ClientError as e:
        print(f"DynamoDB error getting site {site_id}: {e.response['Error']['Message']}")
        return error_response(500, 'Failed to retrieve site')


def list_sites() -> Dict[str, Any]:
    """List all sites with optional filtering."""
    try:
        response = table.scan()
        sites = response['Items']
        
        # Sort by created_at for consistent ordering
        sites.sort(key=lambda x: x.get('created_at', ''))
        
        return success_response({
            'sites': sites,
            'count': len(sites)
        })
        
    except ClientError as e:
        print(f"DynamoDB error listing sites: {e.response['Error']['Message']}")
        return error_response(500, 'Failed to retrieve sites')


def create_site(data: Dict[str, Any]) -> Dict[str, Any]:
    """Create a new site."""
    # Validate required fields
    if not data.get('url'):
        return error_response(400, 'url is required')
    
    url = data['url'].strip()
    if not url:
        return error_response(400, 'url cannot be empty')
    
    # Validate URL format (basic check)
    if not (url.startswith('http://') or url.startswith('https://')):
        return error_response(400, 'url must start with http:// or https://')
    
    try:
        # Check if URL already exists
        existing_sites = table.scan(
            FilterExpression='#url = :url',
            ExpressionAttributeNames={'#url': 'url'},
            ExpressionAttributeValues={':url': url}
        )
        
        if existing_sites['Items']:
            return error_response(409, f'Site with URL {url} already exists')
        
        # Create new site
        site_id = str(uuid.uuid4())
        timestamp = datetime.utcnow().isoformat() + 'Z'
        
        site_item = {
            'site_id': site_id,
            'url': url,
            'name': data.get('name', url),  # Use URL as default name
            'description': data.get('description', ''),
            'tags': data.get('tags', []),
            'enabled': data.get('enabled', True),
            'created_at': timestamp,
            'updated_at': timestamp
        }
        
        table.put_item(Item=site_item)
        
        # Create CloudWatch alarms for the new site
        create_cloudwatch_alarms(url, site_item['name'])
        
        # Update CloudWatch dashboard
        update_cloudwatch_dashboard()
        
        return success_response(site_item, 201)
        
    except ClientError as e:
        print(f"DynamoDB error creating site: {e.response['Error']['Message']}")
        return error_response(500, 'Failed to create site')


def update_site(site_id: str, data: Dict[str, Any]) -> Dict[str, Any]:
    """Update an existing site."""
    try:
        # Check if site exists
        existing_response = table.get_item(Key={'site_id': site_id})
        if 'Item' not in existing_response:
            return error_response(404, f'Site with ID {site_id} not found')
        
        existing_site = existing_response['Item']
        
        # Validate URL if provided
        if 'url' in data:
            url = data['url'].strip()
            if not url:
                return error_response(400, 'url cannot be empty')
            if not (url.startswith('http://') or url.startswith('https://')):
                return error_response(400, 'url must start with http:// or https://')
            
            # Check if new URL conflicts with existing sites (excluding current site)
            existing_urls = table.scan(
                FilterExpression='#url = :url AND site_id <> :site_id',
                ExpressionAttributeNames={'#url': 'url'},
                ExpressionAttributeValues={':url': url, ':site_id': site_id}
            )
            
            if existing_urls['Items']:
                return error_response(409, f'Another site with URL {url} already exists')
        
        # Build update expression
        update_expression = "SET updated_at = :updated_at"
        expression_values = {':updated_at': datetime.utcnow().isoformat() + 'Z'}
        expression_names = {}
        
        # Update allowed fields
        updatable_fields = ['url', 'name', 'description', 'tags', 'enabled']
        for field in updatable_fields:
            if field in data:
                if field == 'url':  # url is a reserved keyword
                    update_expression += ", #url = :url"
                    expression_names['#url'] = 'url'
                    expression_values[':url'] = data[field]
                else:
                    update_expression += f", {field} = :{field}"
                    expression_values[f':{field}'] = data[field]
        
        # Perform update
        response = table.update_item(
            Key={'site_id': site_id},
            UpdateExpression=update_expression,
            ExpressionAttributeValues=expression_values,
            ExpressionAttributeNames=expression_names if expression_names else None,
            ReturnValues='ALL_NEW'
        )
        
        return success_response(response['Attributes'])
        
    except ClientError as e:
        print(f"DynamoDB error updating site {site_id}: {e.response['Error']['Message']}")
        return error_response(500, 'Failed to update site')


def delete_site(site_id: str) -> Dict[str, Any]:
    """Delete a site."""
    try:
        # Check if site exists
        existing_response = table.get_item(Key={'site_id': site_id})
        if 'Item' not in existing_response:
            return error_response(404, f'Site with ID {site_id} not found')
        
        # Get site name before deletion for alarm cleanup
        site_name = existing_response['Item'].get('name', 'Unknown')
        
        # Delete the site
        table.delete_item(Key={'site_id': site_id})
        
        # Delete CloudWatch alarms for the site
        delete_cloudwatch_alarms(site_name)
        
        # Update CloudWatch dashboard
        update_cloudwatch_dashboard()
        
        return success_response({
            'message': f'Site {site_id} deleted successfully',
            'site_id': site_id
        })
        
    except ClientError as e:
        print(f"DynamoDB error deleting site {site_id}: {e.response['Error']['Message']}")
        return error_response(500, 'Failed to delete site')


def success_response(data: Any, status_code: int = 200) -> Dict[str, Any]:
    """Generate a successful API response."""
    return {
        'statusCode': status_code,
        'headers': {
            'Content-Type': 'application/json',
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Headers': 'Content-Type',
            'Access-Control-Allow-Methods': 'GET,POST,PUT,DELETE,OPTIONS'
        },
        'body': json.dumps(data, default=str)
    }


def error_response(status_code: int, message: str) -> Dict[str, Any]:
    """Generate an error API response."""
    return {
        'statusCode': status_code,
        'headers': {
            'Content-Type': 'application/json',
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Headers': 'Content-Type',
            'Access-Control-Allow-Methods': 'GET,POST,PUT,DELETE,OPTIONS'
        },
        'body': json.dumps({
            'error': message,
            'statusCode': status_code
        })
    }


def create_alarm_description(metric_type: str, site: str, severity: str = "warning"):
    """Create alarm description with embedded tags for filtering"""
    return f"[METRIC_TYPE:{metric_type}][SEVERITY:{severity}][SITE:{site}] Alarm for {site}"


def create_cloudwatch_alarms(site_url: str, site_name: str) -> None:
    """Create CloudWatch alarms for a new site."""
    try:
        # Create availability alarm
        availability_alarm_name = f"AvailabilityAlarm-{site_name}"
        cloudwatch.put_metric_alarm(
            AlarmName=availability_alarm_name,
            ComparisonOperator='LessThanThreshold',
            EvaluationPeriods=1,
            MetricName='Availability',
            Namespace=METRIC_NAMESPACE,
            Period=300,
            Statistic='Average',
            Threshold=1.0,
            ActionsEnabled=True,
            AlarmActions=[SNS_TOPIC_ARN] if SNS_TOPIC_ARN else [],
            AlarmDescription=create_alarm_description('availability', site_name, 'critical'),
            Dimensions=[
                {
                    'Name': 'Site',
                    'Value': site_name
                }
            ]
        )
        
        # Create latency alarm
        latency_alarm_name = f"LatencyAlarm-{site_name}"
        cloudwatch.put_metric_alarm(
            AlarmName=latency_alarm_name,
            ComparisonOperator='GreaterThanThreshold',
            EvaluationPeriods=1,
            MetricName='Latency',
            Namespace=METRIC_NAMESPACE,
            Period=300,
            Statistic='Average',
            Threshold=2000.0,
            ActionsEnabled=True,
            AlarmActions=[SNS_TOPIC_ARN] if SNS_TOPIC_ARN else [],
            AlarmDescription=create_alarm_description('latency', site_name, 'warning'),
            Dimensions=[
                {
                    'Name': 'Site',
                    'Value': site_name
                }
            ]
        )
        
        print(f"Created CloudWatch alarms for site: {site_name}")
        
    except Exception as e:
        print(f"Error creating CloudWatch alarms for {site_name}: {str(e)}")
        # Don't fail the API call if alarm creation fails


def delete_cloudwatch_alarms(site_name: str) -> None:
    """Delete CloudWatch alarms for a site."""
    try:
        alarm_names = [
            f"AvailabilityAlarm-{site_name}",
            f"LatencyAlarm-{site_name}"
        ]
        
        # Check if alarms exist before trying to delete
        existing_alarms = cloudwatch.describe_alarms(
            AlarmNames=alarm_names,
            MaxRecords=100
        )
        
        alarms_to_delete = [alarm['AlarmName'] for alarm in existing_alarms['MetricAlarms']]
        
        if alarms_to_delete:
            cloudwatch.delete_alarms(AlarmNames=alarms_to_delete)
            print(f"Deleted CloudWatch alarms for site: {site_name}")
        else:
            print(f"No CloudWatch alarms found for site: {site_name}")
            
    except Exception as e:
        print(f"Error deleting CloudWatch alarms for {site_name}: {str(e)}")
        # Don't fail the API call if alarm deletion fails


def update_cloudwatch_dashboard() -> None:
    """Update CloudWatch dashboard with current sites from DynamoDB."""
    try:
        # Get all enabled sites from DynamoDB
        response = table.scan(
            FilterExpression='#enabled = :enabled',
            ExpressionAttributeNames={'#enabled': 'enabled'},
            ExpressionAttributeValues={':enabled': True}
        )
        
        enabled_sites = [item for item in response['Items']]
        
        # Build dashboard widgets for each site
        widgets = []
        
        for i, site in enumerate(enabled_sites):
            site_name = site.get('name', site.get('url', 'Unknown'))
            
            # Calculate widget positions (2 columns)
            row = i * 6  # Each site takes 2 rows (availability + latency)
            
            # Availability widget
            availability_widget = {
                "type": "metric",
                "x": 0,
                "y": row,
                "width": 12,
                "height": 6,
                "properties": {
                    "metrics": [
                        [METRIC_NAMESPACE, "Availability", "Site", site_name]
                    ],
                    "view": "timeSeries",
                    "stacked": False,
                    "region": "us-east-1",
                    "title": f"Availability - {site_name}",
                    "period": 300
                }
            }
            
            # Latency widget
            latency_widget = {
                "type": "metric",
                "x": 12,
                "y": row,
                "width": 12,
                "height": 6,
                "properties": {
                    "metrics": [
                        [METRIC_NAMESPACE, "Latency", "Site", site_name]
                    ],
                    "view": "timeSeries",
                    "stacked": False,
                    "region": "us-east-1",
                    "title": f"Latency (p95 ms) - {site_name}",
                    "period": 300,
                    "stat": "p95"
                }
            }
            
            widgets.extend([availability_widget, latency_widget])
        
        # Add operational metrics widgets
        operational_row = len(enabled_sites) * 6
        
        execution_time_widget = {
            "type": "metric",
            "x": 0,
            "y": operational_row,
            "width": 12,
            "height": 6,
            "properties": {
                "metrics": [
                    [METRIC_NAMESPACE, "CrawlerExecutionTime", "Function", "WebCrawler"]
                ],
                "view": "timeSeries",
                "stacked": False,
                "region": "us-east-1",
                "title": "Crawler Execution Time",
                "period": 300
            }
        }
        
        memory_widget = {
            "type": "metric",
            "x": 12,
            "y": operational_row,
            "width": 12,
            "height": 6,
            "properties": {
                "metrics": [
                    [METRIC_NAMESPACE, "CrawlerMemoryUsage", "Function", "WebCrawler"]
                ],
                "view": "timeSeries",
                "stacked": False,
                "region": "us-east-1",
                "title": "Crawler Memory Usage",
                "period": 300,
                "stat": "Maximum"
            }
        }
        
        widgets.extend([execution_time_widget, memory_widget])
        
        # Update dashboard
        dashboard_body = {
            "widgets": widgets
        }
        
        cloudwatch.put_dashboard(
            DashboardName=DASHBOARD_NAME,
            DashboardBody=json.dumps(dashboard_body)
        )
        
        print(f"Updated CloudWatch dashboard: {DASHBOARD_NAME}")
        
    except Exception as e:
        print(f"Error updating CloudWatch dashboard: {str(e)}")
        # Don't fail the API call if dashboard update fails
