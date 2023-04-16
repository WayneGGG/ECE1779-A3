from flask import render_template, url_for, request, redirect
from app import webapp
from . import webapp, local_test, s3client, s3_bucket_name, dydb, dyclient, table, table_name, check_account, login, user_table
from boto3.dynamodb.conditions import Key, Attr


# main page
@webapp.route('/api/<user>/<password>/')
def main(user, password):
    if check_account(user, password):
        return render_template("main.html", user=user, password=password)
    else:
        return login()


# search page
@webapp.route('/api/<user>/<password>/search')
def search(user, password):
    if check_account(user, password):
        return render_template("search.html", user=user, password=password, data={})
    else:
        return login()


# upload page to upload a new pair of key and image
@webapp.route('/api/<user>/<password>/upload', methods=['GET'])
def upload(user, password):
    if check_account(user, password):
        return render_template("upload.html", user=user, password=password)
    else:
        return login()


# key page that shows an image associated with a given key
@webapp.route('/api/<user>/<password>/key', methods=['GET'])
def key(user, password):
    if check_account(user, password):
        return render_template("key.html", user=user, password=password)
    else:
        return login()


# display page that displays all the available keys stored in the database
# as well as a button to delete all keys and values
@webapp.route('/api/<user>/<password>/display')
def display(user, password):
    if check_account(user, password):
        res = user_table.query(
            KeyConditionExpression=Key('user').eq(user) & Key('password').eq(password)
        )
        return render_template("display.html", keys=[], user=user, password=password, storage_used=res['Items'][0]['storage_used'], storage_available=res['Items'][0]['storage_limit']-res['Items'][0]['storage_used'])
    else:
        return login()






