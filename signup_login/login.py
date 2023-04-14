import json
import boto3
from botocore.exceptions import ClientError
# from boto3.dynamodb.conditions import Key

dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
table_name = 'Users'

# # Create the DynamoDB table if it does not exist.
# if table_name not in [table.name for table in dynamodb.tables.all()]:
#     table = dynamodb.create_table(
#         TableName=table_name,
#         KeySchema=[
#             {
#                 'AttributeName': 'email',
#                 'KeyType': 'HASH'
#             }
#         ],
#         AttributeDefinitions=[
#             {
#                 'AttributeName': 'email',
#                 'AttributeType': 'S'
#             }
#         ],
#         ProvisionedThroughput={
#             'ReadCapacityUnits': 10,
#             'WriteCapacityUnits': 10
#         }
#     )

def lambda_handler(event, context):
    try:
        email = event['email']
        password = event['password']

        if not email or not password:
            return {
                "statusCode": 400,
                "headers": { "Content-type": "application/json" },
                "body": json.dumps({"error": "Missing input parameter"})
            }

        table = dynamodb.Table(table_name)
        response = table.get_item(Key={'email': email})
        if 'Item' not in response:
            return {
                "statusCode": 401,
                "headers": { "Content-type": "application/json" },
                "body": "Invalid email or password"
                }
        name = response['Item']['name']
        if password == response['Item']['password']:
            return {
                "statusCode": 200,
                "headers": { "Content-type": "application/json" },
                "body": f"Welcome, {name}!"
                }
        else:
            return {
                "statusCode": 401,
                "headers": { "Content-type": "application/json" },
                "body": "Invalid email or password"
                }
    except ClientError as e:
        error = e.response['Error']['Message']
        return {
            "statusCode": 500,
            "headers": { "Content-type": "application/json" },
            "body": json.dumps({"error": error})
            }
