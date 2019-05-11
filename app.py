import os
from flask import Flask
from flask import request
import json
from flask_cors import CORS, cross_origin
import pymongo
import sys
from werkzeug import secure_filename
import pandas as pd
import time
import random
import string
import requests
from datetime import datetime

app = Flask(__name__)

# @app.route('/upload')
# def upload_file():
#    return render_template('upload.html')

duration = 20*60

files = dict()

client = pymongo.MongoClient("mongodb://sramako:admin1@ds251598.mlab.com:51598/tplat")
userdb = client['tplat']

# CLEANUP CODE
filescol = userdb['files']
# filescol.insert_one({'test_id':'abcde','name':'DemoFile','sub':'This is a demo test'})
file_list = os.listdir('upload')
file_list = list(map(lambda x:x.split('.')[0], file_list))
cursor = filescol.find({})
for document in cursor:
    if document['test_id'] not in file_list:
        filescol.delete_one(document)
    else:
        print(document)
for test_id in file_list:
    files[test_id] = pd.read_excel('upload/'+test_id+'.xlsx')

def new_session(stringLength=10):
    letters = string.ascii_lowercase
    return ''.join(random.choice(letters) for i in range(stringLength))

def new_test(stringLength=3):
    letters = string.ascii_lowercase
    return ''.join(random.choice(letters) for i in range(stringLength))

def validate_user(email, session_id):
    user = []
    usercol = userdb['user']
    for i in usercol.find({'email':email,'session_id':session_id},{'_id':0}):
        user.append(i)
    if len(user)==0:
        print("Validation Failed")
        return 0
    else:
        return 1

def validate_admin(email, session_id):
    user = []
    usercol = userdb['admin']
    for i in usercol.find({'email':email},{'_id':0}):
        user.append(i)
    if len(user)==0:
        print("Validation Failed")
        return 0
    else:
        return 1

# ACCESS CONTROL LIST
acl = userdb['acl']
def check_access(email,test_id):
    if email in ['sramakoo@gmail.com','choudhuryrini24@gmail.com','jayantach@gmail.com']:
        return True
    acl_data = acl.find({'email':email, 'test_id':test_id})
    count = 0
    for i in acl_data:
        count += 1
    if count>0:
        return True
    else:
        return False

@app.route('/add_access', methods = ['GET', 'POST'])
def add_access(email,test_id):
    acl.insert_one({'email':email, 'test_id':test_id})

def delete_access(email,test_id):
    acl.delete_one({'email':email, 'test_id':test_id})



# VIEW AVAILABLE TESTS
@app.route('/tests', methods = ['GET', 'POST'])
def tests():
    if request.method == 'GET':
        email = request.values['email']
        session_id = request.values['session_id']
        if(validate_user(email, session_id)):
            cursor = filescol.find({},{'_id':0})
            ret = []
            for document in cursor:
              if(check_access(email,document['test_id'])):
                  print(document)
                  ret.append(document)
            return json.dumps(ret)

# UPLOAD TEST
@app.route('/uploader', methods = ['GET', 'POST'])
def upload_file():
   if request.method == 'POST':
      f = request.files['file']
      name = request.values['name']
      sub = request.values['sub']
      test_id = new_test()
      f.save('upload/'+test_id+'.xlsx')
      # files[test_id] = pd.read_excel('upload/'+test_id+'.xlsx')
      filescol.insert_one({'test_id':test_id,'name':name,'sub':sub})
      return 'File uploaded successfully'

@app.route('/tests', methods = ['GET', 'POST'])
def explore():
    s = os.listdir('upload')
    return json.dumps(s)

# SETUP THE TEST FOR USER
@app.route('/testdetails', methods = ['GET', 'POST'])
def testdetails():
    if request.method == 'GET':
        res = request.values['res']
        email = request.values['email']
        session_id = request.values['session_id']
        test_id = request.values['session_id']
        if(validate_user(email, session_id)):
            if check_access(email, test_id):
                testinfo = userdb['testinfo']
                cur_time = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
                test_info.insert_one({'test_id':test_id, 'email':email, 'time':cur_time})
                return 'success'
            else:
                return "You don't have permission to take this test"
        else:
            return "Invalid user."


# PULL QUESTIONS
@app.route('/pull', methods = ['GET', 'POST'])
def pull():
    if request.method == 'GET':
        test_id = request.values['test_id']
        email = request.values['email']
        session_id = request.values['session_id']
        # For security don't let user send test id, retreive from database
    if(validate_user(email, session_id)):
        if check_access(email, test_id):
            i = int(request.values['i'])
            que = list(files[test_id].iloc[i-1].values)
            return json.dumps(que)
        else:
            return json.dumps("Permission Denied")

# SIZE OF TEST
@app.route('/size', methods = ['GET', 'POST'])
def size():
    if request.method == 'GET':
        test_id = request.values['test_id']
        print(files[test_id].shape)
        return str(files[test_id].shape[0])

# PUSH ANSWER
@app.route('/push', methods = ['GET', 'POST'])
def push():
    if request.method == 'GET':
        i = request.values['i']
        res = request.values['res']
        email = request.values['email']
        session_id = request.values['session_id']
        test_id = request.values['test_id']
        if(validate_user(email, session_id) and check_access(email, test_id)):
            testcol = userdb['test']
            test = []
            for row in testcol.find({'session_id':session_id},{'_id':0}):
                test.append(row)
            if len(test)!=0:
                test[0]['data'][i] = res
                testcol.update_one({'session_id':session_id},{'$set':test[0]})
                return str("saved")
            else:
                return str("Test not available")

# CHECK IF ALREADY ANSWERED
@app.route('/check', methods = ['GET', 'POST'])
def check():
    if request.method == 'GET':
        i = request.values['i']
        email = request.values['email']
        session_id = request.values['session_id']
        if(validate_user(email, session_id)):
            testcol = userdb['test']
            test = []
            for row in testcol.find({'session_id':session_id},{'_id':0}):
                test.append(row)
            if len(test)!=0:
                data = test[0]['data']
                print(data)
                print(i)
                if i in list(data.keys()):
                    return data[i]
                else:
                    return 'blank'
            else:
                return 'Test not available'

# START THE TEST OR RETURN TIME LEFT
@app.route('/start', methods = ['GET', 'POST'])
def start():
    global end_time
    if request.method == 'GET':
        email = request.values['email']
        session_id = request.values['session_id']
        test_id = request.values['test_id']
        if(validate_user(email, session_id)):
            testcol = userdb['test']
            test = []
            for i in testcol.find({'session_id':session_id},{'_id':0}):
                test.append(i)
            if len(test)==0:
                temp = {
                    "session_id" : session_id,
                    "test_id":test_id,
                    "email" : email,
                    "end_time" : int(time.time()+duration),
                    "data" : dict()
                }
                testcol.insert_one(temp)
                return str(duration)
            else:
                rem = int(test[0]['end_time']-time.time())
                if rem>0:
                    return str(rem)
                else:
                    return 'expired'

# RESUME TEST
@app.route('/loadstate', methods = ['GET', 'POST'])
def loadstate():
    if request.method == 'GET':
        email = request.values['email']
        session_id = request.values['session_id']
        if(validate_user(email, session_id)):
            testcol = userdb['test']
            test = []
            for i in testcol.find({'session_id':session_id},{'_id':0}):
                test.append(i)
            if len(test)!=0:
                data = test[0]['data']
                if len(list(data.keys()))>0:
                    return json.dumps(data)
                else:
                    return "nosaves"

# AUTHENTICATE USER
@app.route('/startsession', methods = ['GET', 'POST'])
def startsession():
    if request.method == 'POST':
        usercol = userdb['user']
        name = request.values['name']
        pic = request.values['pic']
        email = request.values['email']
        id_token = request.values['id_token']
        response = requests.get("https://oauth2.googleapis.com/tokeninfo",{"id_token":id_token})
        if response.status_code == 200:
            if response.json()['email'] == email:
                temp = {
                'name':name,
                'pic':pic,
                'email':email,
                'session_id':new_session()
                }
                user = []
                for i in usercol.find({'email':email},{'_id':0}):
                    user.append(i)
                if len(user)==0:
                    usercol.insert_one(temp)
                else:
                    usercol.update_one({'email':email},{'$set':temp})
                return temp['session_id']
        return 'failed'


@app.route('/checksession', methods = ['GET', 'POST'])
def checksession():
    if request.method == 'GET':
        session_id = request.values['session_id']
        email = request.values['email']
        user = []
        for i in usercol.find({'email':email,'session_id':session_id},{'_id':0}):
            user.append(i)
        if len(user)==0:
            return 'failed'
        else:
            return 'success'

@app.route('/feedback', methods = ['GET', 'POST'])
def feedback():
    if request.method == 'GET':
        email = request.values['email'];
        value = request.values['value'];
        print(email,value)
        usercol = userdb['feedback']
        usercol.insert_one({"email":email,"value":value})
        return str('success')

if __name__ == '__main__':
	port = int(os.environ.get('PORT', 5000))
	cors = CORS(app, resources=r'/*')
    # app.config['CORS_HEADERS'] = 'Content-Type'
	app.run(host='0.0.0.0', port=port,debug=True)
	# app.run()
