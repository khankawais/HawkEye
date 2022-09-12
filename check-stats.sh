#Get the unique id
id=$(cat /etc/machine-id)

#Get hostname of the machine
hostname=$(hostname)

#Get the timezone of the machine
timezone=$(timedatectl | grep "Time zone" | cut -d ":" -f 2 | cut -d " " -f 2)

response=$(curl -Gs "127.0.0.1:5000/api/v1/statistics/systeminfo" --data-urlencode info="time:$(date +'%Y-%m-%d %T');;,time_zone:$timezone;;,id:$id;;,hostname:$hostname;;,users:$(who| awk '{print $1}'|sort -u)" -u $(cat /opt/creds.txt)) 
if [[ "$response" != "OK" ]]
then
    echo "API is not working"
    
fi


# Memory info -------------------------
memory_info=$(free -h | grep -E "Mem|total" | tr -s ' ' | cut -d ' ' -f 2,3,4,6,7)


# Disk info -------------------------
disk_info=$(df -h | grep -E "Use%|/dev/sd|/dev/nvme|/dev/mapper|//|/dev/xvd" | tr -s ' ')


# CPU info -------------------------
cpu_info=$(echo "$[100-$(vmstat 1 2|tail -1|awk '{print $15}')]")


response=$(curl -Gs "127.0.0.1:5000/api/v1/statistics/stats" --data-urlencode stats="time:$(date +'%Y-%m-%d %T');;,time_zone:$timezone;;,id:$id;;,Memory:$memory_info;;,Disk:$disk_info;;,CPU:$cpu_info" -u $(cat /opt/creds.txt)) 
if [[ "$response" != "OK" ]]
then
    echo "API is not working"
    
fi

# Process List -------------------------
process_list=$(ps -e -o user,pid,tty,pcpu,pmem,comm --sort -pcpu,pmem)

response=$(curl -Gs "127.0.0.1:5000/api/v1/statistics/listprocesses" --data-urlencode list="time:$(date +'%Y-%m-%d %T');;,time_zone:$timezone;;,id:$id;;,$process_list" -u $(cat /opt/creds.txt)) 
if [[ "$response" != "OK" ]]
then
    echo "API is not working"
    
fi

# Open Ports -------------------------
open_ports=$(netstat -tulpn | grep -E 'Address|LISTEN')

response=$(curl -Gs "127.0.0.1:5000/api/v1/statistics/open-ports" --data-urlencode data="time:$(date +'%Y-%m-%d %T');;,time_zone:$timezone;;,id:$id;;,$open_ports" -u $(cat /opt/creds.txt)) 
if [[ "$response" != "OK" ]]
then
    echo "API is not working"
    
fi
