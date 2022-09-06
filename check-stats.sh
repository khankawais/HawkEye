#Get the unique id
id=$(cat /etc/machine-id)

#Get hostname of the machine
hostname=$(hostname)

response=$(curl -Gs "127.0.0.1:5000/api/v1/statistics/systeminfo" --data-urlencode info="time:$(date +'%Y-%m-%d %T');;,id:$id;;,hostname:$hostname;;,users:$(who| awk '{print $1}'|sort -u)" -u $(cat /opt/creds.txt)) 
if [[ "$response" != "OK" ]]
then
    echo "API is not working"
    
fi


# Memory info -------------------------


memory_info=$(free -h | grep -E "Mem|total" | tr -s ' ' | cut -d ' ' -f 2,3,4,6,7)
# echo $memory_info


# Disk info -------------------------
disk_info=$(df -h | grep -E "Use%|/dev/sd|/dev/nvme|/dev/mapper|//|/dev/xvd" | tr -s ' ')
# echo $disk_info



# CPU info -------------------------

cpu_info=$(echo "$[100-$(vmstat 1 2|tail -1|awk '{print $15}')]")
# echo $cpu_info

response=$(curl -Gs "127.0.0.1:5000/api/v1/statistics/stats" --data-urlencode stats="time:$(date +'%Y-%m-%d %T');;,id:$id;;,Memory:$memory_info;;,Disk:$disk_info;;,CPU:$cpu_info" -u $(cat /opt/creds.txt)) 
if [[ "$response" != "OK" ]]
then
    echo "API is not working"
    
fi

process_list=$(ps -e -o user,pid,tty,pcpu,pmem,comm --sort -pcpu,pmem)
#to_send="$to_send Process list: $process_list"
#echo $to_send

response=$(curl -Gs "127.0.0.1:5000/api/v1/statistics/listprocesses" --data-urlencode list="time:$(date +'%Y-%m-%d %T');;,id:$id;;,$process_list" -u $(cat /opt/creds.txt)) 
if [[ "$response" != "OK" ]]
then
    echo "API is not working"
    
fi

open_ports=$(netstat -tulpn | grep -E 'Address|LISTEN')
# echo $open_ports

response=$(curl -Gs "127.0.0.1:5000/api/v1/statistics/open-ports" --data-urlencode data="time:$(date +'%Y-%m-%d %T');;,id:$id;;,$open_ports" -u $(cat /opt/creds.txt)) 
if [[ "$response" != "OK" ]]
then
    echo "API is not working"
    
fi
