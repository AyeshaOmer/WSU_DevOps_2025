import urllib3
import time
import json
import os
import boto3
from datetime import datetime

# Import optional modules for memory tracking
try:
    import resource
    HAS_RESOURCE = True
except ImportError:
    HAS_RESOURCE = False

try:
    import psutil
    HAS_PSUTIL = True
except ImportError:
    HAS_PSUTIL = False

# AWS clients
cloudwatch = boto3.client("cloudwatch")
dynamodb = boto3.resource('dynamodb')

# Environment variables
NAMESPACE = os.getenv("METRIC_NAMESPACE", "NYTMonitor")
SITES_TABLE_NAME = os.getenv("SITES_TABLE_NAME", "Sites")

def _put_metrics(site: str, latency_ms: float | None, status_code: int | None, available: int):
    """
    Publish metrics to CloudWatch for a single website.
    """
    metric_data = [
        {
            "MetricName": "Availability",
            "Dimensions": [{"Name": "Site", "Value": site}],
            "Value": available,
            "Unit": "Count",
        }
    ]

    if latency_ms is not None:
        metric_data.append({
            "MetricName": "Latency",
            "Dimensions": [{"Name": "Site", "Value": site}],
            "Value": latency_ms,
            "Unit": "Milliseconds",
        })

    if status_code is not None:
        metric_data.append({
            "MetricName": "StatusCode",
            "Dimensions": [{"Name": "Site", "Value": site}, {"Name": "Code", "Value": str(status_code)}],
            "Value": 1,
            "Unit": "Count",
        })

    cloudwatch.put_metric_data(Namespace=NAMESPACE, MetricData=metric_data)

def _put_operational_metrics(execution_time_ms: float, memory_used_mb: float, sites_processed: int):
    """
    Publish operational health metrics for the crawler itself.
    """
    metric_data = [
        {
            "MetricName": "CrawlerExecutionTime",
            "Dimensions": [{"Name": "Function", "Value": "WebCrawler"}],
            "Value": execution_time_ms,
            "Unit": "Milliseconds",
        },
        {
            "MetricName": "CrawlerMemoryUsage", 
            "Dimensions": [{"Name": "Function", "Value": "WebCrawler"}],
            "Value": memory_used_mb,
            "Unit": "Megabytes",
        },
        {
            "MetricName": "SitesProcessed",
            "Dimensions": [{"Name": "Function", "Value": "WebCrawler"}],
            "Value": sites_processed,
            "Unit": "Count",
        }
    ]
    
    cloudwatch.put_metric_data(Namespace=NAMESPACE, MetricData=metric_data)

def _get_memory_usage_mb():
    """
    Get current memory usage in MB. Uses different methods based on what's available.
    """
    # Try psutil first (works on Windows)
    if HAS_PSUTIL:
        try:
            process = psutil.Process()
            memory_info = process.memory_info()
            return memory_info.rss / (1024 * 1024)  # Convert bytes to MB
        except Exception:
            pass
    
    # Try resource module (Unix/Linux only)
    if HAS_RESOURCE:
        try:
            memory_usage_kb = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
            # On Linux, ru_maxrss is in KB, on macOS it's in bytes
            import platform
            if platform.system() == 'Darwin':  # macOS
                return memory_usage_kb / (1024 * 1024)  # Convert bytes to MB
            else:  # Linux (Lambda environment)
                return memory_usage_kb / 1024  # Convert KB to MB
        except Exception:
            pass
    
    # Fallback: try reading /proc/self/status (Linux only)
    try:
        with open('/proc/self/status', 'r') as f:
            for line in f:
                if line.startswith('VmRSS:'):
                    # Extract memory value in KB
                    memory_kb = int(line.split()[1])
                    return memory_kb / 1024  # Convert to MB
    except Exception:
        pass
    
    # Final fallback: return 0 if we can't measure memory
    return 0.0


def _get_sites_from_dynamodb():
    """
    Get enabled sites from DynamoDB. Falls back to sites.json if DynamoDB is unavailable.
    """
    try:
        table = dynamodb.Table(SITES_TABLE_NAME)
        
        # Scan for enabled sites only
        response = table.scan(
            FilterExpression='#enabled = :enabled',
            ExpressionAttributeNames={'#enabled': 'enabled'},
            ExpressionAttributeValues={':enabled': True}
        )
        
        sites = []
        for item in response['Items']:
            # Use the URL for monitoring
            sites.append(item['url'])
            
        if sites:
            print(f"Retrieved {len(sites)} enabled sites from DynamoDB")
            return sites
        else:
            print("No enabled sites found in DynamoDB, falling back to sites.json")
            return _get_sites_from_json()
            
    except Exception as e:
        print(f"Error accessing DynamoDB: {str(e)}, falling back to sites.json")
        return _get_sites_from_json()


def _get_sites_from_json():
    """
    Fallback method to read sites from sites.json file.
    """
    try:
        sites_path = os.path.join(os.path.dirname(__file__), "sites.json")
        with open(sites_path, "r", encoding="utf-8") as f:
            sites = json.load(f)
        print(f"Retrieved {len(sites)} sites from sites.json")
        return sites
    except Exception as e:
        print(f"Error reading sites.json: {str(e)}")
        return []

def lambda_handler(event, context):
    """
    Lambda handler to crawl multiple websites and publish metrics.
    """
    # Start operational metrics tracking
    start_time = time.time()
    initial_memory = _get_memory_usage_mb()
    
    # Get sites from DynamoDB (with fallback to sites.json)
    sites = _get_sites_from_dynamodb()

    http = urllib3.PoolManager()

    for site in sites:
        start = time.time()
        latency_ms = None
        status_code = None
        available = 0

        try:
            resp = http.request(
                "GET",
                site,
                timeout=urllib3.Timeout(connect=3.0, read=10.0),
                retries=False
            )
            latency_ms = (time.time() - start) * 1000
            status_code = resp.status
            available = 1 if status_code == 200 else 0
        except Exception:
            available = 0

        _put_metrics(site, latency_ms, status_code, available)

    # Calculate and publish operational metrics
    end_time = time.time()
    execution_time_ms = (end_time - start_time) * 1000
    final_memory = _get_memory_usage_mb()
    max_memory_used = max(initial_memory, final_memory)
    
    # Publish operational health metrics
    _put_operational_metrics(execution_time_ms, max_memory_used, len(sites))

    return {
        "ok": True, 
        "sites_checked": len(sites),
        "execution_time_ms": execution_time_ms,
        "memory_used_mb": max_memory_used
    }
