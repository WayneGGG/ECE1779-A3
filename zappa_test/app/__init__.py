from flask import Flask, render_template, request, json
import os
import boto3
from boto3.dynamodb.conditions import Key, Attr

webapp = Flask(__name__)

ALLOWED_IMAGE_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'bmp'}

local_test = False
UPLOAD_FOLDER = "app/static/images"
webapp.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
webapp.config['MAX_CONTENT_LENGTH'] = 980 * 1000

# set env for S3
# don't need this when using zappa
#os.environ["AWS_DEFAULT_REGION"] = 'us-east-1'
#os.environ["AWS_ACCESS_KEY_ID"] = 'AKIAWO6QGZ3URSCJCCNL'
#os.environ["AWS_SECRET_ACCESS_KEY"] = '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'


# init s3
s3_bucket_name = "imagefilesbucket20230312222008826009"

# initialize s3 client
s3client = boto3.client('s3', region_name='us-east-1')
'''
resp = s3client.list_objects_v2(Bucket=s3_bucket_name)
if 'Contents' in resp:
    keys = []
    for obj in resp['Contents']:
        keys.append(obj['Key'])
    for key in keys:
        s3client.delete_object(Bucket=s3_bucket_name, Key=key)
'''

# init dynamodb
dyclient = boto3.client('dynamodb', region_name='us-east-1')
dydb = boto3.resource('dynamodb', region_name='us-east-1')

table_name = 'Images'
table = dydb.Table(table_name)
user_table = dydb.Table('Accounts')


def check_account(user_name, pwd):
    if user_name is None or pwd is None:
        return False

    response = user_table.query(
        KeyConditionExpression=Key('user').eq(user_name) & Key('password').eq(pwd)
    )

    records = []
    for i in response['Items']:
        records.append(i)

    return len(records) > 0


# login page
@webapp.route('/api/login')
def login():
    return render_template("login.html")


# user login
@webapp.route('/api/user_login', methods=['POST'])
def user_login():
    user = request.form.get('user')
    password = request.form.get('password')
    if check_account(user, password):
        return render_template("main.html", user=user, password=password)
    else:
        return webapp.response_class(
            response=json.dumps({
                "success": "false",
                "error": 'invalid username or password'
            }),
            status=400,
            mimetype='application/json'
        )


# signup page
@webapp.route('/api/signup')
def signup():
    return render_template("signup.html")


# user signup
@webapp.route('/api/user_signup', methods=['POST'])
def user_signup():
    user = request.form.get('user')
    password = request.form.get('password')

    if len(user) > 20 or len(password) > 20:
        return webapp.response_class(
            response=json.dumps({
                "success": "false",
                "error": 'username or password too long(max 20)'
            }),
            status=400,
            mimetype='application/json'
        )

    response = user_table.query(
        KeyConditionExpression=Key('user').eq(user)
    )
    if len(response['Items']) > 0:
        return webapp.response_class(
            response=json.dumps({
                "success": "false",
                "error": 'user name already exist, please user another username'
            }),
            status=400,
            mimetype='application/json'
        )

    user_table.put_item(
        Item={
            'user': user,
            'password': password,
            'storage_used': 0,
            'storage_limit': 50 * 1000 * 1000
        }
    )

    return webapp.response_class(
        response=json.dumps({
            "success": "true",
            "error": 'user sign up succeed'
        }),
        status=200,
        mimetype='application/json'
    )


# logout
@webapp.route('/api/logout')
def logout():
    return render_template("login.html")



from app import main
from app import upload
from app import key







