#!/usr/bin/env python
import os
import json
from json import dumps
from flask import Flask, g, Response, request, render_template
import sys

# pics = os.path.join('static', 'pics')


app = Flask(__name__, static_url_path='/static/')
# app.config['UPLOAD_FOLDER'] = pics
# app = Flask(__name__)
# app.config['UPLOAD_FOLDER'] = pics

@app.route("/")
def get_index():
	# full_filename = os.path.join(app.config['UPLOAD_FOLDER'],'graph.jpg')
	return app.send_static_file('index.html')


@app.route('/urls', methods=['GET','POST'])
def get_urls():
    try:
        print("connected")
        # q = request.args["q"]
        content = request.json
    except KeyError:
        print("error")
        return []
    else:
    	print("got input")
    	print(content)
    	with open('data.json', 'w') as outfile:
    		json.dump(content, outfile)
    	query = jsontoquery()
    	print(query)
    	# qjson = json.loads("place for pictures")
    	# print(qjson)
    	# return json.dumps({'success':True}), qjson, {'ContentType':'application/json'}
    	return json.dumps({'status':'OK', 'pass':'Place for Pics'});
		# return Response(dumps("YES"),
		#                 mimetype="application/json")

@app.route('/my-link/')
def my_link():
  print('I got clicked!')

  return 'Click.'


def jsontoquery():
	with open('data.json') as data_file:
		data = json.load(data_file)
	noun={}
	relation={}
	source=[]
	target=[]
	
	for i in range(len(data["nodes"])):
	    if data["nodes"][i]["class"]=="noun":
	        #ncount=ncount+1
	        noun[int(data["nodes"][i]["id"])]=data["nodes"][i]["title"]
	    if data["nodes"][i]["class"]=="rel":
	        #rcounter=rcounter+1
	        relation[int(data["nodes"][i]["id"])]=data["nodes"][i]["title"]

	for i in range(len(data["edges"])):
	    source.append(data["edges"][i]["source"])
	    target.append(data["edges"][i]["target"])

	#relation appears in both source and target, each relation only once in source and target respectively
	#relation only connected to two nouns
	
	for key in relation:
		countSR = 0
		countTR = 0
		for i in source:
		    if i==key:
		        countSR=countSR+1
		for i in target:
		    if i==key:
		        countTR=countTR+1
		if(countTR!=countSR or countTR!=1 or countSR!=1):
		    print("This query is not valid")
		    return []
		    # sys.exit()
		else:
		    print("Relation "+relation[key]+" is valid!")

	#no noun-to-noun connections
	#no relation to relation connections

	for i in range(len(data["edges"])):
	    if data["edges"][i]["source"] in noun.keys() and data["edges"][i]["target"] in noun.keys():
	        print("This query is not valid")
	        return []
	        # sys.exit()
	    if data["edges"][i]["source"] in relation.keys() and data["edges"][i]["target"] in relation.keys():
	        print("This query is not valid!")
	        return []
	        # sys.exit()

	flagnoun=0
	keystopop=[]
	for key in noun:
	    for i in range(len(data["edges"])):
	        if key==data["edges"][i]["source"] or key==data["edges"][i]["target"]:
	            flagnoun=1
	    if flagnoun!=1:
	        keystopop.append(key)
	    flagnoun=0

	for i in keystopop:
	    noun.pop(i)

	nc={}
	ncount=0
	for key in noun:
		ncount=ncount+1
		nc[key]=ncount

	ncounter=0
	rcounter=0
	#create final query
	query=""

	for key,value in noun.items():
	    ncounter=ncounter+1
	    query=query+str(ncounter)+",n,"+value+"\n"

	sourceval=0
	targetval=0
	for key,value in relation.items():
	    for i in range(len(data["edges"])):
	        if data["edges"][i]["source"]==key:
	            targetval=data["edges"][i]["target"]
	    for i in range(len(data["edges"])):
	        if data["edges"][i]["target"]==key:
	            sourceval=data["edges"][i]["source"]
	    rcounter=rcounter+1
	    query=query+str(rcounter)+",r,"+value+","+str(nc[sourceval])+","+str(nc[targetval])+"\n"
	    sourceval=0
	    targetval=0

	return query





if __name__ == '__main__':
    app.run(port=8080)
