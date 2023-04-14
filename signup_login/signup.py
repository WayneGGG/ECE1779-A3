import json
import boto3
from botocore.exceptions import ClientError
import re
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

def validateInput(name, email, password):
    # validate name length
    if name.strip() == '':
        return False, "Please enter the name"
    # validate email format
    emailRegex = r'^[^\s@]+@[^\s@]+\.[^\s@]+$'
    if not re.search(emailRegex, email):
        return False, "Please enter a valid email address"
    if email.strip() == '':
        return False, "Please enter the email"
    # validate password length
    if len(password) < 6:
        return False, "Password must be at least 6 characters long"
    if len(password) > 16:
        return False, "Password must be at most 16 characters long"
    return True, ""

def lambda_handler(event, context):
    try:
        name = event['name']
        email = event['email']
        password = event['password']

        # Validate input parameters
        is_valid, message = validateInput(name, email, password)
        if not is_valid:
            return {
                "statusCode": 400,
                "headers": { "Content-type": "application/json" },
                "body": json.dumps({"error": message})
            }

        table = dynamodb.Table(table_name) 

        # Check if user already exists
        response = table.get_item(Key={'email': email})
        if 'Item' in response:
            return {
                "statusCode": 400,
                "headers": { "Content-type": "application/json" },
                "body": "User already exists"
                }

        table.put_item(
            Item={
                'name': name,
                'email': email,
                'password': password
            }
        )
        return {
            "statusCode": 200,
            "headers": { "Content-type": "application/json" },
            "body": "Registration Complete. Please Login to your account!"
        }
    except ClientError as e:
        error = e.response['Error']['Message']
        return {
            "statusCode": 500,
            "headers": { "Content-type": "application/json" },
            "body": json.dumps({"error": error})
            }
