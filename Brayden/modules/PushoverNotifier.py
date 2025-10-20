import json
import os
import requests
import time

# --- Configuration (Set as Environment Variables in AWS Lambda Console) ---
# PUSHOVER_TOKEN: Your Application API Token (e.g., a8cR...p3eE)
# PUSHOVER_USER: Your User Key or Group Key (e.g., uoPj...o4jW)

def lambda_handler(event, context):
    """
    Processes a CloudWatch alarm notification received via SNS and sends 
    a corresponding message to Pushover if the state is ALARM.
    """
    
    # 1. Retrieve Pushover Credentials
    PUSHOVER_TOKEN = os.environ.get('PUSHOVER_TOKEN')
    PUSHOVER_USER = os.environ.get('PUSHOVER_USER')

    if not PUSHOVER_TOKEN or not PUSHOVER_USER:
        print("ERROR: Pushover API token or user key is missing. Check environment variables.")
        # Returning here prevents unauthorized API calls
        return 

    # 2. Parse the SNS Message Content
    try:
        # The actual CloudWatch alarm JSON is nested inside the SNS 'Message' field
        sns_record = event['Records'][0]
        sns_message = sns_record['Sns']['Message']
        alarm_data = json.loads(sns_message)
    except (IndexError, KeyError, json.JSONDecodeError) as e:
        print(f"Error parsing SNS or alarm data: {e}")
        # Log the raw event for debugging
        print(f"Raw Event: {json.dumps(event)}")
        return

    # 3. Check the Alarm State
    new_state = alarm_data.get('NewStateValue', 'UNKNOWN')
    
    # We only care about the transition to ALARM state
    if new_state != 'ALARM':
        print(f"Alarm state is {new_state}. No notification sent.")
        return

    # 4. Extract Alarm Details for Pushover Message
    alarm_name = alarm_data.get('AlarmName', 'N/A')
    alarm_reason = alarm_data.get('NewStateReason', 'No reason provided.')
    # Using the state change time provided by CloudWatch
    timestamp = time.strftime('%Y-%m-%d %H:%M:%S UTC', time.gmtime(alarm_data.get('StateChangeTime', time.time())))
    
    # Construct the message body
    pushover_title = f"🚨 ALARM: {alarm_name}"
    pushover_message = (
        f"State: {new_state}\n"
        f"Reason: {alarm_reason}\n"
        f"Region: {alarm_data.get('Region', 'N/A')}\n"
        f"Time: {timestamp}"
    )

    # 5. Build the Pushover API Payload
    payload = {
        "token": PUSHOVER_TOKEN,
        "user": PUSHOVER_USER,
        "message": pushover_message,
        "title": pushover_title,
        "priority": 1 # Priority 1 often sends a high-priority alert
    }

    # 6. Send the Notification using the requests library
    try:
        pushover_url = "https://api.pushover.net/1/messages.json"
        response = requests.post(pushover_url, data=payload)
        response.raise_for_status() # Raise HTTPError for bad responses (4xx or 5xx)

        response_json = response.json()
        if response_json.get('status') == 1:
            print(f"Successfully sent Pushover notification for alarm: {alarm_name}")
        else:
            print(f"Pushover API Error for {alarm_name}: {response_json.get('errors')}")

    except requests.exceptions.RequestException as req_err:
        print(f"HTTP/Request Error sending Pushover notification: {req_err}")
        
    return {
        'statusCode': 200,
        'body': json.dumps('Pushover notification attempt completed.')
    }
