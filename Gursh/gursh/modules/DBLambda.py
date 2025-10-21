# Filename: modules/DBLambda.py
import os
import json
import re
from datetime import datetime, timezone
from decimal import Decimal
import boto3

TABLE_NAME = os.environ["TABLE_NAME"]
NAMESPACE = os.environ.get("URL_NAMESPACE", "")
DIMENSION_NAME = os.environ.get("DIMENSION_NAME", "URL")

ddb = boto3.resource("dynamodb").Table(TABLE_NAME)


VALUE_RE = re.compile(r"datapoints\s*\[\s*([-+]?\d*\.?\d+)\s*\]", re.IGNORECASE)


def _now_iso():
    return datetime.now(timezone.utc).isoformat()


def _to_decimal(v):
    if isinstance(v, (int, float)):
        return Decimal(str(v))
    if isinstance(v, str):
        try:
            return Decimal(v)
        except Exception:
            return v
    return v


def _parse_observed_value(state_reason: str):
    if not state_reason:
        return None
    m = VALUE_RE.search(state_reason)
    if not m:
        return None
    try:
        return float(m.group(1))
    except Exception:
        return None


def _dimensions_to_dict(trigger_dims):
    out = {}
    if isinstance(trigger_dims, list):
        for d in trigger_dims:
            n = d.get("name") or d.get("Name")
            v = d.get("value") or d.get("Value")
            if n:
                out[n] = v
    return out


def _put_item(item: dict):

    item = {k: v for k, v in item.items() if v is not None}
    ddb.put_item(Item=item)


def lambda_handler(event, context):
    records = event.get("Records") or []

    # SNS path (CloudWatch Alarms -> SNS -> this Lambda)
    if records and records[0].get("EventSource") == "aws:sns":
        for r in records:
            msg_raw = r["Sns"]["Message"]
            msg = json.loads(msg_raw) if isinstance(msg_raw, str) else msg_raw

           
            alarm_name = msg.get("AlarmName", "UnknownAlarm")
            alarm_state = msg.get("NewStateValue", "UNKNOWN")
            state_reason = msg.get("NewStateReason", "")

            trig = msg.get("Trigger", {}) or {}
            metric_name = trig.get("MetricName")
            threshold = trig.get("Threshold")
            cmp = trig.get("ComparisonOperator")
            dims_map = _dimensions_to_dict(trig.get("Dimensions"))

            url = dims_map.get(DIMENSION_NAME)
            observed = _parse_observed_value(state_reason)

            latency_ms = observed if metric_name == "URL_MONITOR_LATENCY" else None
            availability = observed if metric_name == "URL_MONITOR_AVAILABILITY" else None

            item = {
                "pk": f"{alarm_name}#{_now_iso()}",
                "timestamp": _now_iso(),
                "source": "CloudWatchAlarm/SNS",
                "alarm_name": alarm_name,
                "alarm_state": alarm_state,
                "alarm_description": state_reason,
                "metric_name": metric_name,
                "observed_value": _to_decimal(observed) if observed is not None else None,
                "latency_ms": _to_decimal(latency_ms) if latency_ms is not None else None,
                "availability": _to_decimal(availability) if availability is not None else None,
                "threshold": _to_decimal(threshold) if threshold is not None else None,
                "comparison_operator": cmp,
                "url": url,
                "namespace": NAMESPACE,
                "dimensions": dims_map,
            }
            _put_item(item)

        return {"statusCode": 200, "body": "SNS messages processed"}

    # Direct invoke (manual testing)
    alarm_name = event.get("AlarmName", "ManualTest")
    alarm_state = event.get("NewStateValue", "ALARM")
    state_reason = event.get("NewStateReason") or event.get("Reason", "manual invoke")
    metric_name = event.get("MetricName")
    observed = event.get("Observed")
    url = event.get("url")

    item = {
        "pk": f"{alarm_name}#{_now_iso()}",
        "timestamp": _now_iso(),
        "source": "DirectInvoke",
        "alarm_name": alarm_name,
        "alarm_state": alarm_state,
        "alarm_description": state_reason,
        "metric_name": metric_name,
        "observed_value": _to_decimal(observed) if observed is not None else None,
        "url": url,
        "namespace": NAMESPACE,
        # >>> SIMPLIFIED: minimal parity only
        "dimensions": {DIMENSION_NAME: url} if url else None,
    }
    _put_item(item)
    return {"statusCode": 200, "body": "Direct test stored"}
