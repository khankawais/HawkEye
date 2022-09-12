import flask
from flask import request
from flask_httpauth import HTTPBasicAuth
from werkzeug.security import generate_password_hash, check_password_hash
from flask_cors import CORS,cross_origin

import requests
from requests.auth import HTTPBasicAuth as request_auth


from config import *
import socket
from io import StringIO
import _thread
import time
import os


priority_queue=[]
data_queue=[]

app = flask.Flask(__name__)
# app.config["DEBUG"] = True
auth = HTTPBasicAuth()
CORS(app)

# User Authentication for API
users = {
    "root": generate_password_hash("toor")
}

@auth.verify_password
def verify_password(username, password):
    if username in users and \
            check_password_hash(users.get(username), password):
        return username

# Homepage
@app.route('/', methods=['GET'])
@cross_origin()
def home():
    to_return=''
    for alert in priority_queue:
        to_return=to_return+ f"<li> {alert} </li>"
    return f"<h1>Monitoring Server</h1><p>This is a list of generated alerts</p> </br> {to_return}"

@app.route('/api/v1/alerts', methods=['GET'])
@auth.login_required
@cross_origin()
def authlog_alert():
    if 'alert' in request.args:
        r_alert=str(request.args['alert'])
        if r_alert != "":
            priority_queue.append(f"Alert:{r_alert}")
        
        return("Alert has been logged by the server")


@app.route('/api/v1/statistics/stats', methods=['GET'])
@auth.login_required
@cross_origin()
def stats():
    if 'stats' in request.args:
        r_stats=str(request.args['stats'])
        if r_stats != "":
            data_queue.append(f"Stats:{r_stats}")
        
        return("OK")

@app.route('/api/v1/statistics/listprocesses', methods=['GET'])
@auth.login_required
@cross_origin()
def list_processes():
    if 'list' in request.args:
        r_list=str(request.args['list'])
        if r_list != "":
            data_queue.append(f"Process List:{r_list}")
            return("OK")

@app.route('/api/v1/statistics/open-ports', methods=['GET'])
@auth.login_required
@cross_origin()
def open_ports():
    if 'data' in request.args:
        r_ports=str(request.args['data'])
        if r_ports != "":
            data_queue.append(f"Open Ports:{r_ports}")
        
        return("OK")

@app.route('/api/v1/statistics/systeminfo', methods=['GET'])
@auth.login_required
@cross_origin()
def system_info():
    if 'info' in request.args:
        r_info=str(request.args['info'])
        if r_info != "":
            data_queue.append(f"System Info:{r_info}")
        
        return("OK")


# app.run(host= '0.0.0.0',port=5000)

_thread.start_new_thread(app.run, ('127.0.0.1',5000))



 
def receive_data(socket):
    received_data=(socket.recv(1024))
    if received_data.decode("utf-8").startswith("Size:"):
        socket.send(bytes(f"Receiving","utf-8")) #Just sending message to the other side. to make sure that the data is received properly.
        received_data=received_data.decode("utf-8")
        size=received_data.split(":")[1]
        # print(size)

        total=None
        received=0
        while received < int(size):
            if total == None:
                total=socket.recv(1024)
            else:
                total+=socket.recv(1024)
            received=len(total)
        return total
    else:
        return received_data
def send_data_string(socket,data):
    size=int(len(data))
    if size > 1024:
        socket.send(bytes(f"Size:{len(data)}","utf-8"))
        socket.recv(1024) #Just receiving message from the other side. to make sure that the data is received properly.
        sent=0
        sio=StringIO(data)
        while sent < size:
            tosend= sio.read(1024)
            socket.send(bytes(tosend,"utf-8"))
            sent+=len(tosend)
    else:
        socket.send(bytes(data,"utf-8"))
         
 

while True:
    try:
        server=socket.socket()
        server.settimeout(60)
        server.connect((server_address,server_port))
        
        strtime=os.popen("date +'%Y-%m-%d %T'").read().replace("\n","")
        unique_id=os.popen("cat /etc/machine-id").read().replace("\n","")
        hostname=os.popen("hostname").read().replace("\n","")
        loggedin_users=os.popen("who| awk '{print $1}'|sort -u").read()
        timezone=os.popen("timedatectl | grep 'Time zone' | cut -d ':' -f 2 | cut -d ' ' -f 2").read()
        # loggedin_users=list(filter(None, loggedin_users)) # Removing empty element from the list, because in this case after splitting the string we get an empty element in the list
        # loggedin_users=','.join(loggedin_users)
        
        system_info=f"time:{strtime};;,time_zone:{timezone};;,id:{unique_id};;,hostname:{hostname};;,users:{loggedin_users}"
        server.send(bytes(system_info,"utf-8"))
        server.recv(1024).decode("utf-8") # Just receiving confirmation that the data was received by server
        
        while True:
            if len(priority_queue) > 0:
                to_send=str(priority_queue[0])
                
                send_data_string(server,to_send)
                priority_queue.pop(0) # If exception occur at send_data_string then the program automatically goes into excep block below. The data will not be lost because of pop.
                print(server.recv(1024).decode("utf-8"))
            
            if len(data_queue) > 0:
                to_send=str(data_queue[0])
                send_data_string(server,to_send)
                receive=server.recv(1024).decode("utf-8")
                if  receive == "RECEIVED":
                    print(receive)
                    data_queue.pop(0)    
            else:
                server.send(bytes("pulse","utf-8"))
                server.recv(1024).decode("utf-8")                
                time.sleep(3)
            time.sleep(0.5)
    except Exception as e:
        print(e)
        time.sleep(5)
    finally:
        server.close()