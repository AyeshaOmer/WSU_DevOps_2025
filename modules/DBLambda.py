import boto3
import os
import json

def lambda_handler(event,context):
    #print (event)
    DB_client=boto3.resource('dynamodb')
    DBtable=os.environ["DB_Table"]
    table=DB_client.Table(DBtable)
    

    message = event['Records'][0]['Sns']['Message']
    x=json.loads(message)
    Alarmname=x['AlarmName']
    Reason=x['NewStateReason']
    TimeStamp=x['AlarmConfigurationUpdatedTimestamp']
    
    table.put_item(
        Item={
            'AlarmTime':TimeStamp,
            'AlarmName': Alarmname,
            'Reason':Reason            
        }
    )talin   
    
    print ('Alarmname',Alarmname,'\n')
    print ('Reason',Reason,'\n')
    print ('TimeStamp',TimeStamp,'\n')