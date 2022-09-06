from urllib import response
import flask
from flask import request
from flask_httpauth import HTTPBasicAuth
from werkzeug.security import generate_password_hash, check_password_hash
from flask_cors import CORS,cross_origin

import requests
from requests.auth import HTTPBasicAuth as request_auth

import json
import random

import socket
import time
import os

from io import StringIO
import _thread
import mysql.connector

from config import *

latest_data_dict={}

latest_alerts=[]
latest_data=[]

query_queue=[]
host=""
port=""
s=None

def create_scocket():
    global port
    global s
    host="0.0.0.0"
    port=1234
    s=socket.socket()
    print(f"Binding port -- > {str(port)}")
    
    s.bind((host,port))
    s.listen(15)

    
#MySQL related functions START --------------------------------------------------------------------------------------------------------


def connect_mysql():
    mysqlconnection = mysql.connector.connect(host=mysql_host,database=mysql_db,user=mysql_user,password=mysql_password)    # Connectin gto MySQL Server.
    return mysqlconnection

def get_from_db(query):
    data_to_return=[]
    try:
        mysqlconnection=connect_mysql()
        cursor = mysqlconnection.cursor()   # Cursor object creater to execute MySQL Queries.
        cursor.execute(query) # Takes the query from the Arguement given when running the Python Script
        results=cursor.fetchall()
        
        if len(results) == 0:
            return(results)
            
        else:
            column_names=cursor.column_names
            for result in results:
                new_dict={}
                for index,res in enumerate(result):
                    new_dict[column_names[index]]=res
                
                data_to_return.append(new_dict)
            return(data_to_return)
    except Exception as e:
        return(e)

def run_mysql():
    
    try:
        mysqlconnection=connect_mysql()
        cursor = mysqlconnection.cursor()   # Cursor object creater to execute MySQL Queries.
    except Exception as e:
        print(e)
        while True:     
            try:
                mysqlconnection=connect_mysql()
                cursor = mysqlconnection.cursor()   # Cursor object creater to execute MySQL Queries.
                break
            except Exception as e:
                print(e)
        
    while True:
        if len(query_queue) > 0:
            for query in query_queue:        
                try:
                    if query.lower().startswith("insert"):
                        cursor.execute(query) # Execute the query
                        mysqlconnection.commit()
                        query_queue.pop(0)
                    elif query.lower().startswith("update"):
                        cursor.execute(query) # Execute the query
                        mysqlconnection.commit()
                        query_queue.pop(0)
                    else:
                        cursor.execute(query) # Takes the query from the Arguement given when running the Python Script
                        result=cursor.fetchall()
                        if len(result) == 0:
                            print("Query Returned Nothing !")
                            
                        else:
                            print(result)
                        query_queue.pop(0)
                except Exception as e:
                    print(e)
                    if "error in your SQL syntax" in str(e):
                        print(f"Syntax error: {e}")
                        query_queue.pop(0)
                    else:
                        while True:     
                            try:
                                mysqlconnection=connect_mysql()
                                break
                            except Exception as e:
                                continue
        time.sleep(0.5) 
                            
    mysqlconnection.close()

#MySQL related functions END ---------------------------------------------------------------------------------------------------------


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




def process_stats(received_data):                 
    received_data=received_data.replace("'","") # Making sure the query doesnt break
    all_stats=received_data.split(';;,')
    stats_dict={}

    for stats in all_stats:
        if stats.startswith('time'):
            time=stats.replace("time:","")
            stats_dict["time"]=time
        elif stats.startswith('id'):
            id=stats.split(":")[1]
            stats_dict["id"]=id
        elif stats.startswith('Memory'):
            
            memory_dictionary={}
            stats=stats.split(":")[1]
            memory=stats # needed to store in database
            stats=stats.split("\n")
            stats=list(filter(None, stats)) # Removing empty element from the list, because in this case after splitting the string we get an empty element in the list
            memory_columns=stats[0].split(" ")
            del stats[0]
            values=stats[0].split(" ")
            for index,value in enumerate(values):
                memory_dictionary[str(memory_columns[index]).lower()]=value
            
            stats_dict["memory"]=memory_dictionary
        elif stats.startswith('Disk'):
            disks_list=[]
            stats=stats.split(":")[1]
            disk=stats
            stats=stats.split("\n")
            disks=list(filter(None, stats)) # Removing empty element from the list, because in this case after splitting the string we get an empty element in the list
            disk_columns=disks[0].replace("Mounted on","Mounted_on")
            disk_columns=disk_columns.split(" ")
            del disks[0]
            for disk in disks:
                values=disk.split(" ")
                disk_dictionary={}
                for index,value in enumerate(values):
                    
                    disk_dictionary[str(disk_columns[index]).lower()]=value

                disks_list.append(disk_dictionary)
            stats_dict["disks"]=disks_list
        elif stats.lower().startswith('cpu'):
            cpu=stats.split(":")[1]
            stats_dict["cpu"]=cpu


    put_data_new(id,"Stats",stats_dict)
    query=f"INSERT INTO `{mysql_db}`.`stats` (`client_id`,`time`,`cpu`,`memory`,`disks`) VALUES ('{id}','{time}','{cpu}','{memory}','{disk}');"
    # print(query)
    print("[INFO] Stats added to database")
    query_queue.append(query)



def process_process_list(received_data):
    received_data=received_data.replace("'","") # Making sure the query doesnt break
    process_dictionary={}
    
    processes=received_data.split(";;,")
    
    for process in processes:
        if process.startswith('time'):
            time=process.replace("time:","")
            process_dictionary["time"]=time
        elif process.startswith('id'):
            id=process.split(":")[1]
            process_dictionary["id"]=id
        else:
            process_list=process
            process_dictionary["process_list"]=process
   
    put_data_new(id,"Process List",process_dictionary)
    # query=f"INSERT INTO `{mysql_db}`.`process_list` (`client_id`,`time`,`process_list`) VALUES ('{id}','{time}','{process_list}');"
    # query_queue.append(query)
    print("[INFO] Process list added to database")
    # print(query)

def process_open_ports(received_data):
    received_data=received_data.replace("'","") # Making sure the query doesnt break
    ports_dictionary={}
    
    received_data=received_data.split(";;,")
    for data in received_data:
        if data.startswith('time'):
            time=data.replace("time:","")
            ports_dictionary["time"]=time
        elif data.startswith('id'):
            id=data.split(":")[1]
            ports_dictionary["id"]=id
        else:
            open_ports=data.strip()
            ports_dictionary["open_ports"]=open_ports

    put_data_new(id,"Open Ports",ports_dictionary)

    # query=f"INSERT INTO `{mysql_db}`.`open_ports` (`client_id`,`time`,`open_ports`) VALUES ('{id}','{time}','{open_ports}');"
    # query_queue.append(query)
    print("[INFO] Open ports added to database")
    # print(query)
    # print(received_data)

def process_system_info(received_data):
    received_data=received_data.replace("'","") # Making sure the query doesnt break
    received_data=received_data.split(";;,")

    system_info_dict={}

    for data in received_data:
        if data.lower().startswith('time'):
            time=data.replace("time:","").strip()
            system_info_dict["time"]=time
        
        elif data.lower().startswith('id'):
            id=data.split(":")[1].strip()
            system_info_dict["id"]=id
        
        elif data.lower().startswith('hostname'):
            hostname=data.replace("hostname:","").strip()
            system_info_dict["host_name"]=hostname
        
        elif data.lower().startswith('users'):

            data=data.replace("users:","").strip()
            data=data.split("\n")
            data=list(filter(None, data)) # Removing empty element from the list, because in this case after splitting the string we get an empty element in the list
            
            user_count=len(data)
            system_info_dict["user_count"]=user_count
            users=','.join(data)
            system_info_dict["users"]=users
        
        elif data.lower().startswith('ip'):
            ip=data.replace("ip:","").strip()
            system_info_dict["ip"]=ip

    put_data_new(id,"System Info",system_info_dict)
    # query=f"INSERT INTO `{mysql_db}`.`system_info` (`client_id`,`time`,`ip`,`users`,`hostname`) VALUES ('{id}','{time}','{ip}','{users}','{hostname}');"
    # query_queue.append(query)
    print("[INFO] System Info added to database")



def process_alerts(received_data):
    received_data=received_data.replace("'","") # Making sure the query doesnt break
    alert_type=""
    alert_description=""
    alert=""
    status=""
    received_data=received_data.split(";;,")
    
    for data in received_data:
        if data.startswith("time:"):
            time=data.replace("time:","").strip()
        elif data.startswith("id:"):
            id=data.replace("id:","").strip()
        else:
            alert=data

            if "Malicious Command" in alert:
                alert=alert.replace("Malicious Command:","")
                alert_type="Malicious Command"
                alert_description="A malicious command has been run on the system which could potentialy compromise the system"
            elif "crontab:" in alert.lower():
                alert=alert.replace("Crontab:","")
                
                alert_type="Change in Crontab"
                alert_description="The crontab has been changed for a user.\nCrontab is used to schedule some command or code to run at a certain time.\nIt can be used by hackers to maintain persistant access to the hacked system."

            elif "useradd" in alert:
                if "new user" in alert:
                    alert_type="New User Added"
                    alert_description="A new user has been created in the system."
                elif "new group" in alert:
                    alert_type="New group created"
                    alert_description="A new user group has been created in the system"
            elif "password changed for" in alert:
                alert_type="Password Changed"
                alert_description="Password has been changed for a user."
            


    if alert !="" and alert_type != "" and alert_description != "":

        if id in latest_data_dict:
            hostname=latest_data_dict[id]["System Info"]["host_name"]
        else:
            hostname=""
        
        query=f"INSERT INTO `{mysql_db}`.`alerts` (`client_id`,`time`,`alert_type`,`alert_text`,`description`,`status`,`host_name`) VALUES ('{id}','{time}','{alert_type}','{alert}','{alert_description}','new','{hostname}');"
        query_queue.append(query)


def put_data_new(id,data_type,data):
    global latest_data_dict
    
    if id not in latest_data_dict:
        latest_data_dict[id]={}
    
    latest_data_dict[id][data_type]=data



def serve_client(client,addr):
    print(f"\n Connection from {addr} has been established")
    received_data=receive_data(client).decode("utf-8")
    client.send(bytes("RECEIVED","utf-8"))
    received_data+=f";;,ip:{addr[0]}"
    try:
        id=received_data.split(";;,")[1].split(":")[1]
        process_system_info(received_data)
         
    except:
        None
    while True:
        try:
            received_data=receive_data(client).decode("utf-8")
            if received_data != "pulse": # each client sends a pulse after a specified time interval to make sure that the server is alive
                
                if received_data.startswith("Alert:"):
                    received_data=received_data.replace("Alert:","")
                    process_alerts(received_data)

                elif received_data.startswith("Stats:"):
                    received_data=received_data.replace("Stats:","")
                    process_stats(received_data)
                elif received_data.startswith("Process List:"):
                    received_data=received_data.replace("Process List:","")
                    process_process_list(received_data)
                elif received_data.startswith("Open Ports:"):
                    received_data=received_data.replace("Open Ports:","")
                    process_open_ports(received_data)
                elif received_data.startswith("System Info:"):
                    received_data=received_data.replace("System Info:","")
                    received_data+=f";;,ip:{addr[0]}"
                    process_system_info(received_data)
                else:
                    print(received_data)
            client.send(bytes("RECEIVED","utf-8"))
            time.sleep(0.1)
        except Exception as e:
            if id in latest_data_dict:
                del latest_data_dict[id]
            print(e)
            break



app = flask.Flask(__name__)
# app.config["DEBUG"] = True
auth = HTTPBasicAuth()
CORS(app)

# User Authentication for API
users = {
    "admin": generate_password_hash("admin")
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
    return f"<h1>Hawk Eye </h1><p>Use this API to get data about the clients</p> </br> {to_return}"

#Get info about all clients
@app.route('/api/v1/clients', methods=['GET'])
@auth.login_required
@cross_origin()
def get_clients():
    if 'id' in request.args:
        r_id=str(request.args['id'])
        if r_id != "":
            if r_id in latest_data_dict:
                if "System Info" in latest_data_dict[r_id]:
                    return(json.dumps(latest_data_dict[r_id]["System Info"]))
                else:
                    return(json.dumps("System Info not received for this client"))
            else:
                return(json.dumps("No data exists for this client"))
    else:
        clients=[]
        for client in latest_data_dict.values():
            clients.append(client["System Info"])

        response={
            "clients": clients
        }
        return(json.dumps(response))


#Get Statistics of a specific client
@app.route('/api/v1/clients/getstats', methods=['GET'])
@auth.login_required
@cross_origin()
def get_stats():

    if 'id' in request.args:
        r_id=str(request.args['id'])
        if r_id != "":
            if r_id in latest_data_dict:
                if "Stats" in latest_data_dict[r_id]:
                    return(json.dumps(latest_data_dict[r_id]["Stats"]))
                else:
                    return(json.dumps("Stats not received for this client"))
            else:
                return(json.dumps("No data exists for this client"))
        
    


#Get Processes of a specific client
@app.route('/api/v1/clients/getprocesses', methods=['GET'])
@auth.login_required
@cross_origin()
def get_processes():
    if 'id' in request.args:
        r_id=str(request.args['id'])
        if r_id in latest_data_dict:
                if "Process List" in latest_data_dict[r_id]:
                    return(json.dumps(latest_data_dict[r_id]["Process List"]))
                else:
                    return(json.dumps("Process List not received for this client"))
        else:
            return(json.dumps("No data exists for this client"))


#Get Open Ports of a specific client
@app.route('/api/v1/clients/getports', methods=['GET'])
@auth.login_required
@cross_origin()
def get_ports():
    if 'id' in request.args:
        r_id=str(request.args['id'])
        if r_id != "":
            if "Open Ports" in latest_data_dict[r_id]:
                return(json.dumps(latest_data_dict[r_id]["Open Ports"]))
            else:
                return(json.dumps("Ports data not received for this client"))
        else:
            return(json.dumps("No data exists for this client"))
    

#Get Alerts
@app.route('/api/v1/clients/getalerts', methods=['GET'])
@auth.login_required
@cross_origin()
def get_alerts():

    if 'id' in request.args:
        r_id=str(request.args['id'])
        if r_id != "":
            id=r_id.replace("'","") # Just replacing ' so that it doesnt break the query
            query=f"SELECT * FROM {mysql_db}.alerts where client_id='{id}';"
            
    elif 'status' in request.args:
        r_status=str(request.args['status'])
        query=f"SELECT * FROM {mysql_db}.alerts where status='{r_status}';"
    else:
        query=f"SELECT * FROM {mysql_db}.alerts;"
    results=get_from_db(query)

    for result in results:
        if result["alert_type"] == "Change in Crontab":
            alert=result["alert_text"]
            alert=alert.split(";,;,")
            crontab_before=alert[0].replace("Before:","")
            crontab_after=alert[1].replace("After:","")
            result["crontab_before"]=crontab_before
            result["crontab_after"]=crontab_after
            result["alert_text"]="Changes made to the Crontab"
    
    return(json.dumps(results))



#Change Alert Status
@app.route('/api/v1/clients/changealertstatus', methods=['PUT'])
@auth.login_required
@cross_origin()
def change_alert_status():
    if 'id' in request.args and 'status' in request.args:
        r_id=str(request.args['id'])
        r_status=str(request.args['status'])
        query=f"UPDATE {mysql_db}.`alerts` SET `status` = '{r_status}' WHERE (`id` = '{r_id}');"
        query_queue.append(query)
    else:
        response="invalid input"

    
    
    response={"id":str(r_id),
            "new_status":str(r_status)

        }
    return(json.dumps(response))





create_scocket()

_thread.start_new_thread(run_mysql, ())
_thread.start_new_thread(app.run, ('0.0.0.0',5000))



while True:
    client,addr=s.accept()
    _thread.start_new_thread(serve_client,(client,addr))
