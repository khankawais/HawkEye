################################################################################
# Author : Awais Khan                                                          #
# Use this script as a root user.                                              #
# This script is used to install the client on a  linux system                 #
#                                                                              #
################################################################################

# set -x
export DEBIAN_FRONTEND=noninteractive

if [ $(id -u) != 0 ];then
    printf " \n[X] You must be root to run the script\n"
     

else

    yum update
    if [ $? -gt 0 ];then
        printf "\n  The current os is not CentOS or Redhat.\n

            Switching to Ubuntu

        "
        echo "[ INFO ] Installing dependencies"
        apt update
        apt install net-tools curl python3 python3-pip -y
    else
        yum update
        yum install net-tools curl python3 python3-pip -y
    fi
    echo "[ INFO ] Creating necessary directories"
    mkdir /opt/Hawk-Eye
    mkdir /opt/Hawk-Eye/auth-log
    mkdir /opt/Hawk-Eye/history
    mkdir /opt/Hawk-Eye/crontab

    echo "[ INFO ] Copying scripts to Installation directory"
    cp -R App/client /opt/Hawk-Eye/App
    cp check-alerts.sh /opt/Hawk-Eye/
    cp check-stats.sh /opt/Hawk-Eye/
    cp get-user-directories.sh /opt/Hawk-Eye/

    echo "[ INFO ] Adding scripts to crontab"
    (crontab -l; echo "@reboot bash /opt/Hawk-Eye/get-user-directories.sh") | sort -u | crontab -
    (crontab -l; echo "* * * * * bash /opt/Hawk-Eye/check-stats.sh") | sort -u | crontab -
    (crontab -l; echo "* * * * * bash /opt/Hawk-Eye/check-alerts.sh") | sort -u | crontab -

    echo "[ INFO ] Installing python dependencies"
    pip3 install -r App/client/requirements.txt

    echo "[ INFO ] Creating new user"
    useradd --system --no-create-home --shell=/sbin/nologin mon-agent
    echo "[ INFO ] Creating new group"
    groupadd hawk-eye
    echo "[ INFO ] Adding root user to the new group"
    usermod -Ghawk-eye "root"
    echo "[ INFO ] Adding mon-agent user to the new group"
    usermod -Ghawk-eye "mon-agent"
    
    echo "[ INFO ] Changing permissions for the Installation directory"
    chgrp -R hawk-eye /opt/Hawk-Eye
    chmod -R 070 /opt/Hawk-Eye
    

    echo "[ INFO ] Copying Dictionary to installation directory"
    cp dictionary.txt /opt/Hawk-Eye/history/dictionary.txt
    echo "[ INFO ] Copying API creds to installation directory"
    cp api_creds.txt /opt/Hawk-Eye/api_creds.txt
    echo "[ INFO ] Copying Auth log to installation directory"
    cp /var/log/auth.log /opt/Hawk-Eye/auth-log/auth.log

    echo "[ INFO ] Copying service config file to systemd folder"

    cat <<EOF > /etc/systemd/system/mon-agent.service
[Unit]
Description=Hawk-Eye monitoring agent
Wants=network.target
After=network.target

[Service]
User=mon-agent
Group=hawk-eye
Type=simple
ExecStart= $(which python3) /opt/Hawk-Eye/App/client.py
Restart=always

[Install]
WantedBy=multi-user.target
EOF

    echo "[ INFO ] Enabling mon-agent service"
    systemctl daemon-reload
    systemctl enable mon-agent.service

    echo "[ INFO ] Starting mon-agent service"
    systemctl start mon-agent.service   
    

    echo "[ INFO ] Fetching user names and their home directories. please wait"
    eval getent passwd {$(awk '/^UID_MIN/ {print $2}' /etc/login.defs)..$(awk '/^UID_MAX/ {print $2}' /etc/login.defs)} | cut -d ":" -f 1,6 > /opt/Hawk-Eye/history/directories.txt
    getent passwd root | cut -d ":" -f 1,6 >> /opt/Hawk-Eye/history/directories.txt
    echo "[ INFO ] Adding necessary settings to individual user's bashrc file"
    cat /opt/Hawk-Eye/history/directories.txt | while read users
    do
        user_name=$(echo $users | cut -d: -f 1)
        directory=$(echo $users | cut -d: -f 2)

        # cp $directory/.bash_history /opt/Hawk-Eye/history/$( echo $user_name)_bash_history
        echo 'shopt -s histappend                      # append to history, dont overwrite it' >> $directory/.bashrc
        echo 'export PROMPT_COMMAND="history -a; history -c; history -r; $PROMPT_COMMAND"' >> $directory/.bashrc
        echo 'export HISTTIMEFORMAT="%d/%m/%y %T "' >> $directory/.bashrc
        echo '#Added for Hawk-Eye' >> $directory/.bashrc
    done
fi