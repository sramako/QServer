import json
import pymongo

client = pymongo.MongoClient("mongodb://sramako:admin1@ds251598.mlab.com:51598/tplat")
userdb = client['tplat']

filescol = userdb['files']
cursor = filescol.find({})
for document in cursor:
    print(document)

usercol = userdb['admin']
# usercol.insert_one({'email':'sramakoo@gmail.com'})
for i in usercol.find({},{'_id':0}):
    print(i)
# usercol.delete_one({'email':'sramakoo@gmail.com'})


usercol = userdb['feedback']
for i in usercol.find({},{'_id':0}):
    print(i)



usercol = userdb['acl']
# usercol.insert_one({'email':'sramakoo@gmail.com','test_id':'mjg'})
for i in usercol.find({},{'_id':0}):
    print(i)
