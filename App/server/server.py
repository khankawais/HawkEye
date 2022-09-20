from datetime import datetime
from datetime import timedelta
from ipaddress import ip_address
from zoneinfo import available_timezones
import pytz

from urllib import response
import flask
from flask import request, render_template
from flask_httpauth import HTTPBasicAuth
from werkzeug.security import generate_password_hash, check_password_hash
from flask_cors import CORS,cross_origin

from requests.auth import HTTPBasicAuth as request_auth

import json

import socket
import time
import os

from io import StringIO
import _thread
import mysql.connector

from config import *
from logger import genlog

latest_data_dict={}
custom_alerts=[]


query_queue=[]
s=None

def create_scocket():
    global host
    global port
    global s
    s=socket.socket()
    print(f"Binding port -- > {str(port)}")
    genlog.info(f"Binding port -- > {str(port)}")
    
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
        # print(e)
        genlog.error(f"[ Error while connecting to MySQL ] {e}")
        while True:     
            try:
                mysqlconnection=connect_mysql()
                cursor = mysqlconnection.cursor()   # Cursor object creater to execute MySQL Queries.
                break
            except Exception as e:
                # print(e)
                genlog.error(f"[ Error while connecting to MySQL ] {e}")
        
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
                    elif query.lower().startswith("delete"):
                        cursor.execute(query) # Execute the query
                        mysqlconnection.commit()
                        query_queue.pop(0)
                    else:
                        query_queue.pop(0) # Query is not Insert,Update,Delete , so its garbage
                except Exception as e:
                    # print(e)
                    genlog.error(f"[ Error with MySQL ] {e}")
                    if "error in your SQL syntax" in str(e):
                        genlog.error(f"[ MySQL Syntax error ] {e}")
                        # print(f"Syntax error: {e}")
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
        if stats.startswith('time:'):
            time=stats.replace("time:","")
            stats_dict["time"]=time
        elif stats.startswith('time_zone'):
            timezone=stats.split(":")[1]
            stats_dict["timezone"]=timezone
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
            
            if "Gi" in memory_dictionary["total"]:
                total_memory=float(memory_dictionary["total"].replace("Gi","").replace("Mi",""))
                total_memory=total_memory*1000
            else:
                total_memory=float(memory_dictionary["total"].replace("Gi","").replace("Mi",""))
            if "Gi" in memory_dictionary["available"]:
                available_memory=float(memory_dictionary["available"].replace("Gi","").replace("Mi",""))
                available_memory=available_memory*1000
            else:
                available_memory=float(memory_dictionary["available"].replace("Gi","").replace("Mi",""))

            
            percentage=((total_memory-available_memory)/total_memory)*100

            memory_dictionary["percentage"]=percentage
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
    query=f"INSERT INTO `{mysql_db}`.`stats` (`client_id`,`time`,`timezone`,`cpu`,`memory`,`disks`) VALUES ('{id}','{time}','{timezone}','{cpu}','{memory}','{disk}');"
    # print(query)
    genlog.info(f"[ {latest_data_dict[id]['System Info']['ip']} ] Stats added to database")
    # print("[INFO] Stats added to database")
    query_queue.append(query)



def process_process_list(received_data):
    add_to_db=True
    received_data=received_data.replace("'","") # Making sure the query doesnt break
    process_dictionary={}
    
    processes=received_data.split(";;,")
    
    for process in processes:
        if process.startswith('time:'):
            time=process.replace("time:","")
            process_dictionary["time"]=time
        elif process.startswith('time_zone'):
            timezone=process.split(":")[1].replace("\n","")
            process_dictionary["timezone"]=timezone
        elif process.startswith('id'):
            id=process.split(":")[1]
            process_dictionary["id"]=id
        else:
            process_list=process
            process_dictionary["process_list"]=process

    # if id in latest_data_dict:
    #     if "Process List" in latest_data_dict[id]: 
    #         temp_latest_info=latest_data_dict[id]["Process List"].copy()
    #         temp_process_list=process_dictionary.copy()
    #         del temp_latest_info["time"]
    #         del temp_process_list["time"]
    #         if temp_latest_info == temp_process_list:
    #             print("[INFO] Process List received")
    #             add_to_db=False
   
    put_data_new(id,"Process List",process_dictionary)
    
    # if add_to_db:
    #     query=f"INSERT INTO `{mysql_db}`.`process_list` (`client_id`,`time`,`timezone`,`process_list`) VALUES ('{id}','{time}','{timezone}','{process_list}');"
    #     query_queue.append(query)
    #     print("[INFO] Process List added to database")
    genlog.info(f"[ {latest_data_dict[id]['System Info']['ip']} ] Process List received")

def process_open_ports(received_data):
    add_to_db=True
    received_data=received_data.replace("'","") # Making sure the query doesnt break
    ports_dictionary={}
    
    received_data=received_data.split(";;,")
    for data in received_data:
        if data.startswith('time:'):
            time=data.replace("time:","")
            ports_dictionary["time"]=time
        elif data.startswith('time_zone'):
            timezone=data.split(":")[1].replace("\n","")
            ports_dictionary["timezone"]=timezone
        elif data.startswith('id'):
            id=data.split(":")[1]
            ports_dictionary["id"]=id
        else:
            open_ports=data.strip()
            ports_dictionary["open_ports"]=open_ports

    if id in latest_data_dict:
        if "Open Ports" in latest_data_dict[id]: 
            temp_latest_info=latest_data_dict[id]["Open Ports"].copy()
            temp_open_ports=ports_dictionary.copy()
            del temp_open_ports["time"]
            del temp_latest_info["time"]

            if temp_latest_info == temp_open_ports:
                # print("[INFO] Open Ports received")
                genlog.info(f"[ {latest_data_dict[id]['System Info']['ip']} ] Open Ports received")
                add_to_db=False
          
    
    put_data_new(id,"Open Ports",ports_dictionary)

    if add_to_db:
        query=f"INSERT INTO `{mysql_db}`.`open_ports` (`client_id`,`time`,`timezone`,`open_ports`) VALUES ('{id}','{time}','{timezone}','{open_ports}');"
        query_queue.append(query)
        genlog.info(f"[ {latest_data_dict[id]['System Info']['ip']} ] Open Ports added to database")



def process_system_info(received_data):
    add_to_db=True
    received_data=received_data.replace("'","") # Making sure the query doesnt break
    received_data=received_data.split(";;,")

    system_info_dict={}

    for data in received_data:
        if data.lower().startswith('time:'):
            time=data.replace("time:","").strip()
            system_info_dict["time"]=time
        elif data.startswith('time_zone'):
            timezone=data.split(":")[1].replace("\n","")
            system_info_dict["timezone"]=timezone
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
 

    if id in latest_data_dict:
        if "System Info" in latest_data_dict[id]: 
            temp_latest_info=latest_data_dict[id]["System Info"].copy()
            temp_system_info=system_info_dict.copy()
            del temp_latest_info["time"]
            del temp_system_info["time"]
            if temp_latest_info == temp_system_info:
                # print("[INFO] System Info received")
                genlog.info(f"[ {latest_data_dict[id]['System Info']['ip']} ] System Info received")
                add_to_db=False

    put_data_new(id,"System Info",system_info_dict)
                
    if add_to_db:
        query=f"INSERT INTO `{mysql_db}`.`system_info` (`client_id`,`time`,`timezone`,`ip`,`users`,`hostname`) VALUES ('{id}','{time}','{timezone}','{ip}','{users}','{hostname}');"
        query_queue.append(query)
        # print("[INFO] System Info added to database")
        genlog.info(f"[ {latest_data_dict[id]['System Info']['ip']} ] System Info added to database")
       



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
        elif data.startswith('time_zone'):
            timezone=data.split(":")[1]
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
        
        query=f"INSERT INTO `{mysql_db}`.`alerts` (`client_id`,`time`,`timezone`,`alert_type`,`alert_text`,`description`,`status`,`host_name`) VALUES ('{id}','{time}','{timezone}','{alert_type}','{alert}','{alert_description}','new','{hostname}');"
        query_queue.append(query)
        genlog.info(f"[ {latest_data_dict[id]['System Info']['ip']} ] New Alert received")


def put_data_new(id,data_type,data):
    global latest_data_dict
    
    if id not in latest_data_dict:
        latest_data_dict[id]={}
    
    latest_data_dict[id][data_type]=data
    


def check_custom_alerts():

    while True:
        try:
            query=f"SELECT * FROM {mysql_db}.custom_alerts_settings;"
            results=get_from_db(query)

            for result in results:
                if result["client_id"] in latest_data_dict:
                    hostname=latest_data_dict[result["client_id"]]["System Info"]["host_name"]
                    timezone=latest_data_dict[result["client_id"]]["System Info"]["timezone"]
                    timezone=timezone.replace("\n","")
                    timezonepytz=pytz.timezone(timezone)
                    time_now=str(datetime.now(timezonepytz))[:19]

                    if result["type"] == "cpu":
                        cpu_values=[]    
                        
                        date_format_str = "%Y-%m-%d %H:%M:%S"

                        time_now = datetime.strptime(time_now, date_format_str)
                        
                        lookup_time=time_now - timedelta(minutes=5)
                        time_range="{ts '"+str(lookup_time)+"'} AND {ts '"+str(time_now)+"'}"
                        query=f"SELECT * FROM {mysql_db}.stats WHERE client_id='{result['client_id']}' AND time BETWEEN {time_range};"
                        
                        stats=get_from_db(query)

                        if len(stats) > 0:
                            for stat in stats:
                                if stat["cpu"] != "null":
                                    cpu_values.append(int(stat["cpu"]))
                            
                            total=sum(cpu_values)
                            number_of_values=len(cpu_values)
                            average_cpu_usage=total/number_of_values

                            if average_cpu_usage > int(result["threshold"]):

                                lookup_time=time_now - timedelta(days=1)
                                time_range="{ts '"+str(lookup_time)+"'} AND {ts '"+str(time_now)+"'}"
                                
                                query=f"SELECT * FROM {mysql_db}.alerts WHERE client_id='{result['client_id']}' AND alert_type='Custom Alert: CPU Usage' AND description LIKE '%than the threshold ({result['threshold']}%'  AND time BETWEEN {time_range};"
                                alerts=get_from_db(query)

                                if len(alerts) < 1:                        
                                    alert="CPU usage has exceeded the threshold limit."
                                    alert_description=f"Current CPU usage is at {int(average_cpu_usage)}% which is greater than the threshold ({result['threshold']}%)"
                                    query=f"INSERT INTO `{mysql_db}`.`alerts` (`client_id`,`time`,`timezone`,`alert_type`,`alert_text`,`description`,`status`,`host_name`) VALUES ('{result['client_id']}','{time_now}','{timezone}','Custom Alert: CPU Usage','{alert}','{alert_description}','new','{hostname}');"
                                    query_queue.append(query)
                                    genlog.info(f"[ {latest_data_dict[result['client_id']]['System Info']['ip']} ] Generated a custom CPU Usage alert")
                    
                    elif result["type"] == "memory":
                        memory_percentages=[]
                        
                        date_format_str = "%Y-%m-%d %H:%M:%S"
                        time_now = datetime.strptime(time_now, date_format_str)
                        lookup_time=time_now - timedelta(minutes=5)

                        time_range="{ts '"+str(lookup_time)+"'} AND {ts '"+str(time_now)+"'}"

                        query=f"SELECT * FROM {mysql_db}.stats WHERE client_id='{result['client_id']}' AND time BETWEEN {time_range};"
                        
                        stats=get_from_db(query)

                        if len(stats) > 0:
                
                            for stat in stats:
                                if stat["memory"] != "null":
                                    memory_dictionary={}
                                    memory_stats=stat["memory"].split("\n")
                                    memory_stats=list(filter(None, memory_stats)) # Removing empty element from the list, because in this case after splitting the string we get an empty element in the list
                                    memory_columns=memory_stats[0].split(" ")
                                    del memory_stats[0]
                                    values=memory_stats[0].split(" ")
                                    for index,value in enumerate(values):
                                        if "Gi" in value:
                                            value=float(value.replace("Gi",""))
                                            value=value*1000
                                        elif "Mi" in value:
                                            value=float(value.replace("Mi",""))
                                        
                                        memory_dictionary[str(memory_columns[index]).lower()]=value

                                    percentage=((memory_dictionary["total"] - memory_dictionary["available"])/memory_dictionary["total"])*100

                                    memory_percentages.append(percentage)
                                
                            
                            total=sum(memory_percentages)
                            number_of_values=len(memory_percentages)
                            average_memory_usage=total/number_of_values

                            if average_memory_usage > int(result["threshold"]):
                                
                                lookup_time=time_now - timedelta(days=1)
                                time_range="{ts '"+str(lookup_time)+"'} AND {ts '"+str(time_now)+"'}"
                                
                                query=f"SELECT * FROM {mysql_db}.alerts WHERE client_id='{result['client_id']}' AND alert_type='Custom Alert: Memory Usage' AND description LIKE '%than the threshold ({result['threshold']}%'  AND time BETWEEN {time_range};"
                                alerts=get_from_db(query)

                                if len(alerts) < 1:
                                    alert="Memory usage has exceeded the threshold limit."
                                    alert_description=f"Current Memory usage is at {int(average_memory_usage)}% which is greater than the threshold ({result['threshold']}%)"
                                    query=f"INSERT INTO `{mysql_db}`.`alerts` (`client_id`,`time`,`timezone`,`alert_type`,`alert_text`,`description`,`status`,`host_name`) VALUES ('{result['client_id']}','{time_now}','{timezone}','Custom Alert: Memory Usage','{alert}','{alert_description}','new','{hostname}');"
                                    query_queue.append(query)
                                    genlog.info(f"[ {latest_data_dict[result['client_id']]['System Info']['ip']} ] Generated a custom Memory Usage alert")


                    elif result["type"] == "disk":
                        threshold=result["threshold"]
                        file_system=result["file_system"]

                        if "Stats" in latest_data_dict[result["client_id"]]:

                            disks=latest_data_dict[result["client_id"]]["Stats"]["disks"]
                            for disk in disks:    
                                if file_system == disk["filesystem"]:
                                    file_system_usage=disk["use%"].replace("%","")
                                    file_system_usage=int(file_system_usage)
                                    if file_system_usage > int(threshold):
                                        date_format_str = "%Y-%m-%d %H:%M:%S"
                                        time_now = datetime.strptime(time_now, date_format_str)
                                        lookup_time=time_now - timedelta(days=1)
                                        time_range="{ts '"+str(lookup_time)+"'} AND {ts '"+str(time_now)+"'}"
                                        
                                        query=f"SELECT * FROM {mysql_db}.alerts WHERE client_id='{result['client_id']}' AND alert_type='Custom Alert: Disk Usage' AND description LIKE '%than the threshold ({result['threshold']}%' AND description LIKE '%for the filesystem [ {file_system}%'  AND time BETWEEN {time_range};"
                                        alerts=get_from_db(query)

                                        if len(alerts) < 1:
                                            alert="Disk usage has exceeded the threshold limit."
                                            alert_description=f"Current Disk usage for the filesystem [ {file_system} ] is at {file_system_usage}% which is greater than the threshold ({result['threshold']}%)"
                                            query=f"INSERT INTO `{mysql_db}`.`alerts` (`client_id`,`time`,`timezone`,`alert_type`,`alert_text`,`description`,`status`,`host_name`) VALUES ('{result['client_id']}','{time_now}','{timezone}','Custom Alert: Disk Usage','{alert}','{alert_description}','new','{hostname}');"
                                            query_queue.append(query)
                                            genlog.info(f"[ {latest_data_dict[result['client_id']]['System Info']['ip']} ] Generated a custom Disk Usage alert")
            time.sleep(5)    
        except:
            time.sleep(5)
        
def serve_client(client,addr):
    print(f"\n Connection from {addr} has been established")
    genlog.info(f" Connection has been established from {addr[0]} on port {addr[1]}")
    received_data=receive_data(client).decode("utf-8")
    client.send(bytes("RECEIVED","utf-8"))
    received_data+=f";;,ip:{addr[0]}"
    try:
        data=received_data.split(";;,")
        for value in data:
            if value.startswith("id:"):
                id=value.replace("id:","")
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
            genlog.error(f"[ Client Disconnected {addr[0]} ] {e}")
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
    return f"<h1>Hawk Eye </h1><p>Use this API to get data about the clients</p>"

#Get info about all clients
@app.route('/api/v1/clients', methods=['GET'])
# @auth.login_required
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
    r_type=str(request.args['type'])
    if 'id' in request.args:
        r_id=str(request.args['id'])
        
        if r_id != "" and r_type !="":
            id=r_id.replace("'","") # Just replacing ' so that it doesnt break the query
            if r_type == "custom":
                query=f"SELECT * FROM {mysql_db}.alerts where client_id='{id}' and alert_type LIKE 'Custom Alert:%';"
            else:
                
                query=f"SELECT * FROM {mysql_db}.alerts where client_id='{id}' and alert_type NOT LIKE 'Custom Alert:%';"
    elif 'status' in request.args:
        r_status=str(request.args['status'])
        if r_type != "":
            if r_type == "custom":
                query=f"SELECT * FROM {mysql_db}.alerts where status='{r_status}' and alert_type LIKE 'Custom Alert:%';"
            else:  
                query=f"SELECT * FROM {mysql_db}.alerts where status='{r_status}' and alert_type NOT LIKE 'Custom Alert:%';"
    else:
        if r_type != "":
            if r_type == "custom":
                query=f"SELECT * FROM {mysql_db}.alerts where alert_type LIKE 'Custom Alert:%';"
            else:
                query=f"SELECT * FROM {mysql_db}.alerts where alert_type NOT LIKE 'Custom Alert:%';"
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


@app.route('/api/v1/clients/get_custom_alerts', methods=['GET'])
@auth.login_required
@cross_origin()
def get_custom_alerts():
    if request.method == "GET":
        results=""
        if 'id' in request.args:
            r_id=str(request.args['id']).replace("'","")
            if r_id != "":
                query=f"SELECT * FROM {mysql_db}.custom_alerts_settings where client_id='{r_id}';"
                results=get_from_db(query)
                return(json.dumps(results))
        
        else:
            allowed_custom_alert_types=["cpu","memory","disk"]
            
            return(json.dumps({"allowed_types":allowed_custom_alert_types}))
        

@app.route('/api/v1/clients/update_custom_alert', methods=['PUT'])
@auth.login_required
@cross_origin()
def update_custom_alert():
    if request.method == "PUT":
        allowed_custom_alert_types=["cpu","memory","disk"]
        if request.headers.get('Content-Type') == "application/json":
            prams=request.get_json()
            client_id = str(prams.get("client_id")).replace("'","")
            alert_id = str(prams.get("alert_id")).replace("'","")
            alert_type=str(prams.get("type")).replace("'","")
            threshold=str(prams.get("threshold")).replace("'","")
            if alert_type in allowed_custom_alert_types:
                if alert_type == "disk":
                    filesystem=str(prams.get("file_system")).replace("'","")
                    query=f"UPDATE {mysql_db}.custom_alerts_settings SET `type` = '{alert_type}', threshold='{threshold}', file_system='{filesystem}' WHERE (`id` = '{alert_id}');" 
                else:   
                    query=f"UPDATE {mysql_db}.custom_alerts_settings SET `type` = '{alert_type}', threshold='{threshold}' WHERE (`id` = '{alert_id}');"
                #UPDATE `hawk_eye`.`custom_alerts_settings` SET `type` = 'disk1', `threshold` = '351', `file_system` = 'None1' WHERE (`id` = '3');
                query_queue.append(query)
                return(json.dumps({"message":"Alert Updated"}))
            else:
                return(json.dumps({"message":"this alert type is not allowed"}))
        else:
            return(json.dumps({"message":"Content-Type not allowed"}))
    else:
        return(json.dumps({"message":"Method not allowed"}))

@app.route('/api/v1/clients/del_custom_alert', methods=['DELETE'])
@auth.login_required
@cross_origin()
def del_custom_alert():
    if request.method == "DELETE":
        if 'client_id' in request.args and 'alert_id' in request.args:
            client_id = str(request.args['client_id']).replace("'","")
            alert_id = str(request.args['alert_id']).replace("'","")
            if client_id != "" and alert_id != "":
                client_id=client_id.replace("'","")
                alert_id=alert_id.replace("'","")
                query=f"DELETE FROM {mysql_db}.custom_alerts_settings WHERE id='{alert_id}' and client_id='{client_id}';"
                query_queue.append(query)
                return(json.dumps({"message":"Alert Deleted"}))
        else:
            return(json.dumps({"message":"Bad request"}))
            

@app.route('/api/v1/clients/create_custom_alert', methods=['POST'])
@auth.login_required
@cross_origin()
def create_custom_alert():
    
    if request.method == "POST":
        if request.headers.get('Content-Type') == "application/json":
            prams=request.get_json()
            allowed_custom_alert_types=["cpu","memory","disk"]
            try:
                # getting input data from HTML form
                client_id = str(prams.get("client_id"))
                client_id=client_id.replace("'","")
                alert_type = str(prams.get("type"))
                alert_type=alert_type.replace("'","")
                
                threshold=str(prams.get("threshold"))
                threshold=threshold.replace("'","")
                created_at=str(datetime.now())[:19]

                if alert_type.lower() in allowed_custom_alert_types:
                    if alert_type.lower() == "disk":
                        file_system=request.form.get("file_system")
                        
                        query=f"INSERT INTO `{mysql_db}`.`custom_alerts_settings` (`client_id`, `time_created`, `type`, `threshold`,`file_system`) VALUES ('{client_id}', '{created_at}', '{alert_type}', '{threshold}', '{file_system}');"
                    else:
                        query=f"INSERT INTO `{mysql_db}`.`custom_alerts_settings` (`client_id`, `time_created`, `type`, `threshold`) VALUES ('{client_id}', '{created_at}', '{alert_type}', '{threshold}');"
                    query_queue.append(query)
                    return(json.dumps({"message":"Custom alert added to database"}))
                    
                else:
                    return(json.dumps({"message":"This alert type is not allowed"}))
                        
            except:
                return(json.dumps({"message":"Something went wrong"}))
        
@app.after_request
def after_request(response):
  response.headers['Access-Control-Allow-Methods']='*'
  response.headers['Access-Control-Allow-Origin']='*'
  response.headers['Vary']='Origin'
  return response


# client_id = str(request.form.get("client_id"))


create_scocket()

_thread.start_new_thread(run_mysql, ()) # Running the custom function in background that will execute mysql queries like INSERT, UPDATE, DELETE.
_thread.start_new_thread(check_custom_alerts, ()) # This will create a thread for checking the custom alerts in the background.
_thread.start_new_thread(app.run, ('0.0.0.0',5000)) # Creating seperate thread for running the flask API app




while True:
    client,addr=s.accept()
    _thread.start_new_thread(serve_client,(client,addr)) # Creating a seperate thread for serving each client
