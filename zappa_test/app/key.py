import requests
import base64
from flask import render_template, url_for, request, redirect
from . import webapp, local_test, s3client, s3_bucket_name, dydb, dyclient, table, table_name, check_account, login
from flask import json
from boto3.dynamodb.conditions import Key, Attr
from datetime import date
from datetime import datetime
import cv2
import os


# get the key value from the request and pass it to key_check()
@webapp.route('/api/<user>/<password>/key/', methods=['POST'])
def key_retrieve_image(user, password):
    if check_account(user, password) is False:
        return login()

    key = request.form.get('key')
    return key_check(key, user, password)


# hold key/<key_value> (post) request to show an image associated with a given key
@webapp.route('/api/<user>/<password>/key/<key_value>', methods=['POST'])
def key_check(key_value, user, password):
    if check_account(user, password) is False:
        return login()

    response = table.query(
        KeyConditionExpression=Key('user').eq(user) & Key('key').eq(key_value)
    )
    records = []
    for i in response['Items']:
        records.append(i)

    # if exist
    if len(records) > 0:
        # get the filename of the image in dy, then go to s3 to get the file
        filename = records[0]['image']
        if local_test:
            image_location = webapp.config['UPLOAD_FOLDER'] + '/' + filename
            image = open(image_location, 'rb')
            image_content = base64.b64encode(image.read())
        else:
            obj = s3client.get_object(Bucket=s3_bucket_name, Key=filename)
            image_content = base64.b64encode(obj['Body'].read())

        helper()

        text = {
            "success": "true",
            "key": key_value,
            "content": image_content.decode('ascii')
        }
        return webapp.response_class(
            response=json.dumps(text),
            status=200,
            mimetype='application/json'
        )
    else:
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


# show an image (no json response) associated with a given key if the key exist
@webapp.route('/api/<user>/<password>/key/nojson/', methods=['POST'])
def key_retrieve_nojson_image(user, password):
    if check_account(user, password) is False:
        return login()

    key_value = request.form.get('key')
    response = table.query(
        KeyConditionExpression=Key('user').eq(user) & Key('key').eq(key_value)
    )
    records = []
    for i in response['Items']:
        records.append(i)

    # if exist
    if len(records) > 0:
        # get the filename of the image in dy, then go to s3 to get the file
        filename = records[0]['image']
        if local_test:
            image_location = webapp.config['UPLOAD_FOLDER'] + '/' + filename
            image = open(image_location, 'rb')
            image_content = base64.b64encode(image.read())
        else:
            obj = s3client.get_object(Bucket=s3_bucket_name, Key=filename)
            image_content = base64.b64encode(obj['Body'].read())

        content = image_content.decode('ascii')

        helper()

        # show the image itself
        return render_template("show_image.html", content=content)
    else:
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


# show an image (edge response) associated with a given key if the key exist
@webapp.route('/api/<user>/<password>/key/edge/', methods=['POST'])
def key_retrieve_edge_image(user, password):
    if check_account(user, password) is False:
        return login()

    key_value = request.form.get('key')
    response = table.query(
        KeyConditionExpression=Key('user').eq(user) & Key('key').eq(key_value)
    )
    records = []
    for i in response['Items']:
        records.append(i)

    # if exist
    if len(records) > 0:
        # get the filename of the image in dy, then go to s3 to get the file
        filename = records[0]['image']
        if local_test:
            image_location = webapp.config['UPLOAD_FOLDER'] + '/' + filename
            image = open(image_location, 'rb')
            image_content = base64.b64encode(image.read())
        else:
            obj = s3client.get_object(Bucket=s3_bucket_name, Key=filename)
            image_content = base64.b64encode(obj['Body'].read())
        #content = image_content.decode('ascii')

        image_suffix = filename.rsplit('.', 1)[1].lower()
        image_name = str(datetime.now()).replace(':', '')
        new_filename = image_name + "." + image_suffix

        with open(filename, 'wb') as f:
            f.write(base64.b64decode(image_content))
        img = cv2.imread(filename, 0)
        blurred = cv2.GaussianBlur(img, (11, 11), 0)
        gaussImg = img - blurred
        cv2.imwrite(new_filename, gaussImg)
        os.remove(filename)

        with open(new_filename, 'rb') as f:
            content = base64.b64encode(f.read()).decode('ascii')
        os.remove(new_filename)

        helper()

        # show the edge image
        return render_template("show_image.html", content=content)
    else:
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


# show an image (enc response) associated with a given key if the key exist
@webapp.route('/api/<user>/<password>/key/enc/', methods=['POST'])
def key_retrieve_enc_image(user, password):
    if check_account(user, password) is False:
        return login()

    key_value = request.form.get('key')
    response = table.query(
        KeyConditionExpression=Key('user').eq(user) & Key('key').eq(key_value)
    )
    records = []
    for i in response['Items']:
        records.append(i)

    # if exist
    if len(records) > 0:
        # get the filename of the image in dy, then go to s3 to get the file
        filename = records[0]['image']
        if local_test:
            return webapp.response_class(
                response=json.dumps({
                    "success": "false",
                    "error": {
                        "code": 400,
                        "message": "can not do this in local test"
                    }
                }),
                status=400,
                mimetype='application/json'
            )
        url = 'https://a3-images-20230409.s3.amazonaws.com/editor.html?name=' + filename
        helper()

        # show the enc image
        return redirect(url)
    else:
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



# search images
@webapp.route('/api/<user>/<password>/search_images', methods=['POST'])
def search_images(user, password):
    if check_account(user, password) is False:
        return login()

    tag = request.form.get('tag')
    response = table.query(
        KeyConditionExpression=Key('user').eq(user),
        FilterExpression=Attr('tag').eq(tag)
    )
    records = []
    for i in response['Items']:
        records.append(i)

    return render_template('search.html', user=user, password=password, data=records)


# check searched image
@webapp.route('/api/<user>/<password>/check_image/<key>', methods=['POST', 'GET'])
def check_image(user, password, key):
    if check_account(user, password) is False:
        return login()

    response = table.query(
        KeyConditionExpression=Key('user').eq(user) & Key('key').eq(key)
    )
    records = []
    for i in response['Items']:
        records.append(i)
    if len(records) > 0:
        # get the filename of the image in dy, then go to s3 to get the file
        filename = records[0]['image']
        if local_test:
            image_location = webapp.config['UPLOAD_FOLDER'] + '/' + filename
            image = open(image_location, 'rb')
            image_content = base64.b64encode(image.read())
        else:
            obj = s3client.get_object(Bucket=s3_bucket_name, Key=filename)
            image_content = base64.b64encode(obj['Body'].read())

        content = image_content.decode('ascii')
        # show the image itself
        return render_template("show_image.html", content=content)
    else:
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


def helper():
    up_table = dydb.Table('App_usage')
    day = date.today().strftime("%Y%m%d")
    time = datetime.now().hour
    if time >= 4:
        time = time - 4
    else:
        time = 24 - (4-time)

    response = up_table.query(
        KeyConditionExpression=Key('day').eq(day) & Key('time').eq(time)
    )
    records = []
    for i in response['Items']:
        records.append(i)
    if len(records) > 0:
        up_table.update_item(
            Key={
                'day': day,
                'time': time
            },
            UpdateExpression="set request_served = request_served + :r",
            ExpressionAttributeValues={
                ':r': 1
            }
        )
    else:
        up_table.put_item(
            Item={
                'day': day,
                'time': time,
                'request_served': 1
            }
        )




