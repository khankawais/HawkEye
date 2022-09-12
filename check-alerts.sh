IFS=''

#Get the unique id
id=$(cat /etc/machine-id)

#Get the timezone of the machine
timezone=$(timedatectl | grep "Time zone" | cut -d ":" -f 2 | cut -d " " -f 2)

# For Auth Log

cp /var/log/auth.log /opt/Hawk-Eye/auth-log/temp-auth.log

copy_authlog=1
copy_bash_history=1

output=

echo "[INFO] Checking Auth Log"
while read -r line
do
    # echo "[Checking Line] : $line"
    
    if [[ "$line" != "" ]]
    then
        echo "Alert to Generate: $line"
        
        out=$(curl -Gs "127.0.0.1:5000/api/v1/alerts" --data-urlencode alert="time:$(date +'%Y-%m-%d %T');;,time_zone:$timezone;;,id:$id;;,$line" -u $(cat /opt/Hawk-Eye/api_creds.txt)) 
        if [[ "$out" != "Alert has been logged by the server" ]]
        then
            copy_authlog=0
            echo "API is not working"
        fi
        
        count=$( echo $line | grep "new user" | wc -l )
        if [[ $count -gt 0 ]] 
        then
            
            $( eval getent passwd {$(awk '/^UID_MIN/ {print $2}' /etc/login.defs)..$(awk '/^UID_MAX/ {print $2}' /etc/login.defs)} | cut -d ":" -f 1,6 > /opt/Hawk-Eye/history/directories.txt)
            getent passwd root | cut -d ":" -f 1,6 >> /opt/Hawk-Eye/history/directories.txt
            while read -r users
            do
                user_name=$(echo $users | cut -d: -f 1)
                directory=$(echo $users | cut -d: -f 2)
                # printf "$directory\n"
                if [[ $( cat $directory/.bashrc | grep "#Added for Hawk-Eye" | wc -l) -lt 1 ]]
                then
                    echo 'shopt -s histappend                      # append to history, dont overwrite it' >> $directory/.bashrc
                    echo 'export PROMPT_COMMAND="history -a; history -c; history -r; $PROMPT_COMMAND"' >> $directory/.bashrc
                    echo 'export HISTTIMEFORMAT="%d/%m/%y %T "' >> $directory/.bashrc
                    echo '#Added for Hawk-Eye' >> $directory/.bashrc
                    cp $directory/.bash_history /opt/Hawk-Eye/history/$( echo $user_name)_bash_history
                    runuser -l $user_name -c "crontab -l" > /opt/Hawk-Eye/crontab/$( echo $user_name)_crontab 2>&1
                fi

            done <<< "$(cat /opt/Hawk-Eye/history/directories.txt)"

            
        fi
    fi

done <<< "$(diff /opt/Hawk-Eye/auth-log/auth.log /opt/Hawk-Eye/auth-log/temp-auth.log | grep "> " | sed 's/> //' | grep -E 'password changed for|useradd')"


if [ $copy_authlog -eq 1 ] 
then
    echo "Temp auth-log moved to auth-log"
    mv /opt/Hawk-Eye/auth-log/temp-auth.log /opt/Hawk-Eye/auth-log/auth.log
fi


#-----------------------------------------------------------------------


# For History ----------------------------------------------------------


if [[ $( cat /opt/Hawk-Eye/history/directories.txt | wc -l) -lt 1 ]]
then

    eval getent passwd {$(awk '/^UID_MIN/ {print $2}' /etc/login.defs)..$(awk '/^UID_MAX/ {print $2}' /etc/login.defs)} | cut -d ":" -f 1,6 > /opt/Hawk-Eye/history/directories.txt
    getent passwd root | cut -d ":" -f 1,6 >> /opt/Hawk-Eye/history/directories.txt

fi

echo "[INFO] Checking History"

while read users 
do
    user_name=$(echo $users | cut -d: -f 1)
    directory=$(echo $users | cut -d: -f 2)

	copy_bash_history=1
    echo "Directory is [$directory]"

    if ! test -f "/opt/Hawk-Eye/history/$( echo $user_name)_bash_history"; then
    
        cp $directory/.bash_history /opt/Hawk-Eye/history/$( echo $user_name)_bash_history

    fi

    cp $directory/.bash_history /opt/Hawk-Eye/history/$( echo $user_name)-temp-bash_history
    
    file=$(diff /opt/Hawk-Eye/history/$( echo $user_name)_bash_history /opt/Hawk-Eye/history/$( echo $user_name)-temp-bash_history | grep "> " | sed 's/> //')
    
    word_count=$(echo $file | wc -l) 
    
    if [ $word_count -gt 0 ] && [ "$file" != '' ] 
    then
        echo "Word Count is $( echo $file | wc -l)"        
        # echo "File not Empty"
        while read -r malicious
        do
            echo "[Info] Checking against malicious command: [$malicious]"
        
            if [ $(echo $file | grep "$malicious" | wc -l) -gt 0 ]
            then

                while read -r alert
                do
                    echo "Alert to Generate: $alert"
        
                    out=$(curl -Gs "127.0.0.1:5000/api/v1/alerts" --data-urlencode alert="time:$(date +'%Y-%m-%d %T');;,time_zone:$timezone;;,id:$id;;,Malicious Command:$alert" -u $(cat /opt/Hawk-Eye/api_creds.txt)) 
                    if [[ "$out" != "Alert has been logged by the server" ]]
                    then
                        copy_bash_history=0
                        echo "API is not working"
                        
                    fi
                    echo "[Alert] Malicious Command Found {$alert}"

                done <<< "$(echo $file | awk -F \\n '{ if ($0 ~ /^#[0-9]+/) {printf "%s ", strftime("%y/%m/%d %T", substr($1,2)); getline; print $0 }}'| grep "$malicious")"
                
            fi

        done <<< "$(cat /opt/Hawk-Eye/history/dictionary.txt)"
    fi		

    if [ $copy_bash_history -eq 1 ] 
    then
        echo "Temp bash history moved to bash_history"
        mv /opt/Hawk-Eye/history/$( echo $user_name)-temp-bash_history /opt/Hawk-Eye/history/$( echo $user_name)_bash_history
    fi

done <<< "$(cat /opt/Hawk-Eye/history/directories.txt)"




# Checking Crontabs -------------------------------------------


while read users 
do
    copy_crontab=1
    user_name=$(echo $users | cut -d: -f 1)
    directory=$(echo $users | cut -d: -f 2)

    echo "[INFO] Checking crontab for user $user_name"

    new_crontab=$(runuser -l $user_name -c "crontab -l 2>&1" )
    difference=$(diff /opt/Hawk-Eye/crontab/$( echo $user_name)_crontab  - <<< $( printf "$new_crontab" ))
    # printf "$difference\n"
    if [[ $( echo $difference | grep -E "<|>" | wc -l) -gt 0 ]]
    then
        echo "Generating Alert for crontab"
        out=$(curl -Gs "127.0.0.1:5000/api/v1/alerts" --data-urlencode alert="time:$(date +'%Y-%m-%d %T');;,time_zone:$timezone;;,id:$id;;,Crontab:Before:$(cat /opt/Hawk-Eye/crontab/$( echo $user_name)_crontab);,;,After:$new_crontab" -u $(cat /opt/Hawk-Eye/api_creds.txt))
        if [[ "$out" != "Alert has been logged by the server" ]]
        then
            copy_crontab=0
            echo "API is not working"
        fi

    fi 


    if [ $copy_crontab -eq 1 ] 
    then
        echo "[INFO] Crontab copied"
        printf "$new_crontab\n" >  /opt/Hawk-Eye/crontab/$( echo $user_name)_crontab
    fi

done <<< "$(cat /opt/Hawk-Eye/history/directories.txt)"


#-----------------------------------------------------------------------
