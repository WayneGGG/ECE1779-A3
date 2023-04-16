import requests
from datetime import datetime
from flask import render_template, url_for, request, redirect
from . import webapp, ALLOWED_IMAGE_EXTENSIONS, local_test, s3client, s3_bucket_name, dydb, dyclient, table_name, table, check_account, login, user_table
from werkzeug.utils import secure_filename
from flask import json
import base64
import os
import boto3
from datetime import datetime
from boto3.dynamodb.conditions import Key, Attr


# hold upload (post) request to upload a new pair of key and image
@webapp.route('/api/<user>/<password>/upload', methods=['POST'])
def upload_put(user, password):
    if check_account(user, password) is False:
        return login()

    if request.form.get('key') == '':
        error_message = "Key can not be empty"
    elif request.form.get('tag') == '':
        error_message = "Tag can not be empty"
    elif '"' in request.form.get('key') or '\\' in request.form.get('key') or '#' in request.form.get('key') or '?' in request.form.get('key'):
        error_message = "Key can not include these characters: ?#\" , please enter a valid Key"
    elif len(request.form.get('key')) > 500:
        error_message = "Key can not be too long! The maximum length of the Key is 500"
    elif 'file' not in request.files or not request.files['file']:
        error_message = "Please upload an image file only"
    elif request.files['file'].filename == '':
        error_message = "No image uploaded"
    else:
        key = request.form.get('key')
        if request.form.get('filename') is None:
            filename = secure_filename(request.files['file'].filename)
        else:
            filename = request.form.get('filename')
        if valid_file_type(filename):
            file = request.files['file']

            tag = request.form.get('tag')
            key_value = key
            ori_filename = filename

            image_suffix = ori_filename.rsplit('.', 1)[1].lower()
            image_name = str(datetime.now()).replace(':', '')
            image_name = image_name + "." + image_suffix

            # check repeated key/image
            if dy_check_item(user, key_value) is True:
                print("repeat")
                delete_key(key_value, user, password)

            # store image file to s3
            if local_test:
                file.save(os.path.join(webapp.config['UPLOAD_FOLDER'], image_name))
                size = 0
            else:
                image_filename = os.path.join('/tmp', image_name)
                file.save(image_filename)
                s3client.upload_file(Filename=image_filename, Bucket=s3_bucket_name, Key=image_name)
                size = os.path.getsize(image_filename)
                os.remove(image_filename)

            # store image path to dy
            dy_put(user, key_value, image_name, tag, size)

            user_table.update_item(
                Key={
                    'user': user,
                    'password': password
                },
                UpdateExpression="set storage_used = storage_used + :r",
                ExpressionAttributeValues={
                    ':r': size
                }
            )

            res = user_table.query(
                KeyConditionExpression=Key('user').eq(user) & Key('password').eq(password)
            )
            if res['Items'][0]['storage_used'] > res['Items'][0]['storage_limit']:
                delete_key(key_value, user, password)
                return webapp.response_class(
                    response=json.dumps({
                        "success": "false",
                        "error": 'exceed user storage limit! can not upload!'
                    }),
                    status=400,
                    mimetype='application/json'
                )

            return webapp.response_class(
                response=json.dumps({
                    "success": "true",
                    "key": key_value
                }),
                status=200,
                mimetype='application/json'
            )

        else:
            error_message = "Please upload an image with valid type and name"

    return bad_request(error_message, 400)


# delete all images
@webapp.route('/api/<user>/<password>/delete_all', methods=['POST', 'GET'])
def delete_all_keys(user, password):
    if check_account(user, password) is False:
        return login()

    # clear s3
    if local_test:
        for file in os.listdir(webapp.config['UPLOAD_FOLDER']):
            os.remove(os.path.join(webapp.config['UPLOAD_FOLDER'], file))
    else:
        keys = []
        response = table.query(
            KeyConditionExpression=Key('user').eq(user)
        )
        for i in response['Items']:
            keys.append(i['image'])

        resp = s3client.list_objects_v2(Bucket=s3_bucket_name)
        if 'Contents' in resp:
            '''
            keys = []
            for obj in resp['Contents']:
                keys.append(obj['Key'])
            '''
            for key in keys:
                s3client.delete_object(Bucket=s3_bucket_name, Key=key)

    # clear dy
    res = table.query(
        KeyConditionExpression=Key('user').eq(user)
    )
    for i in res['Items']:
        table.delete_item(
            Key={
                'user': user,
                'key': i['key']
            }
        )

    user_table.update_item(
        Key={
            'user': user,
            'password': password
        },
        UpdateExpression="set storage_used = :r",
        ExpressionAttributeValues={
            ':r': 0
        }
    )

    return list_keys(user, password)


@webapp.route('/api/<user>/<password>/delete/<key_value>', methods=['POST'])
def delete_key(key_value, user, password):
    if check_account(user, password) is False:
        return login()
    if dy_check_item(user, key_value) is False:
        return webapp.response_class(
            response=json.dumps({
                "success": "false",
                "error": {
                    "code": 400,
                    "message": "The key doesn't exist"
                }
            }),
            status=400,
            mimetype='application/json'
        )

    res = table.query(
        KeyConditionExpression=Key('user').eq(user) & Key('key').eq(key_value)
    )
    filename = res['Items'][0]['image']
    size = res['Items'][0]['size']

    # delete image name in dy
    table.delete_item(
        Key={
            'user': user,
            'key': key_value
        }
    )

    user_table.update_item(
        Key={
            'user': user,
            'password': password
        },
        UpdateExpression="set storage_used = storage_used - :r",
        ExpressionAttributeValues={
            ':r': size
        }
    )

    # delete image file in s3
    if local_test:
        os.remove(os.path.join(webapp.config['UPLOAD_FOLDER'], filename))
    else:
        s3client.delete_object(Bucket=s3_bucket_name, Key=filename)

    res = user_table.query(
        KeyConditionExpression=Key('user').eq(user) & Key('password').eq(password)
    )

    return render_template('display.html', keys=[], user=user, password=password,
                           storage_used=res['Items'][0]['storage_used'],
                           storage_available=res['Items'][0]['storage_limit'] - res['Items'][0]['storage_used'])



# list of all keys
@webapp.route('/api/<user>/<password>/list_keys', methods=['POST', 'GET'])
def list_keys(user, password):
    if check_account(user, password) is False:
        return login()

    # go to dy and get all keys
    keys = []
    response = table.query(
        KeyConditionExpression=Key('user').eq(user)
    )
    for i in response['Items']:
        keys.append(i['key'])
    res = user_table.query(
        KeyConditionExpression=Key('user').eq(user) & Key('password').eq(password)
    )

    return render_template('display.html', keys=keys, user=user, password=password, storage_used=res['Items'][0]['storage_used'], storage_available=res['Items'][0]['storage_limit']-res['Items'][0]['storage_used'])


# delete one key
@webapp.route('/api/<user>/<password>/delete_single_key', methods=['POST'])
def delete_single_key(user, password):
    key = request.form.get('key')
    return delete_key(key, user, password)


# check whether the file type is valid
def valid_file_type(name) -> bool:
    return '.' in name and name.rsplit('.', 1)[1].lower() in ALLOWED_IMAGE_EXTENSIONS


# return a json response for bad request
def bad_request(error_message, error_code):
    text = {
        "success": "false",
        "error": {
            "code": error_code,
            "message": error_message
        }
    }
    response = webapp.response_class(
        response=json.dumps(text),
        status=error_code,
        mimetype='application/json'
    )

    return response


# put item into dy table
def dy_put(user, key, image_name, tag, size):
    table.put_item(
        Item={
            'user': user,
            'key': key,
            'image': image_name,
            'tag': tag,
            'size': size
        }
    )


# check whether an item exists in the dy table
def dy_check_item(user, key):
    response = table.query(
        KeyConditionExpression=Key('user').eq(user) & Key('key').eq(key)
    )

    records = []
    for i in response['Items']:
        records.append(i)
    return len(records) > 0

'''

# create table
def create_table():
    dydb.create_table(
        TableName=table_name,
        KeySchema=[
            {
                'AttributeName': 'user',
                'KeyType': 'HASH'  # Partition key
            },
            {
                'AttributeName': 'key',
                'KeyType': 'RANGE'  # Sort key
            }
        ],
        AttributeDefinitions=[
            {
                'AttributeName': 'user',
                'AttributeType': 'S'
            },
            {
                'AttributeName': 'key',
                'AttributeType': 'S'
            },
        ],
        ProvisionedThroughput={
            'ReadCapacityUnits': 10,
            'WriteCapacityUnits': 10
        }
    )


# delete table
def delete_table():
    dyclient.delete_table(
        TableName=table_name
    )


try:
    create_table()
except dyclient.exceptions.ResourceInUseException:
    pass

'''
