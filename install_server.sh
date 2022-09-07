# set -x
export DEBIAN_FRONTEND=noninteractive

if [ $(id -u) != 0 ];then
    printf " \n[X] You must be root to run the script\n"
     
else

    echo "[ INFO ] Installing dependencies"
    apt update
    apt install python3 python3-pip -y
    echo "[ INFO ] Creating necessary directories"
    mkdir /opt/Hawk-Eye
    
    echo "[ INFO ] Copying scripts to Installation directory"
    cp -R App/server /opt/Hawk-Eye/App
    
    echo "[ INFO ] Adding scripts to crontab"
    
    echo "[ INFO ] Installing python dependencies"
    pip3 install -r App/server/requirements.txt

    echo "[ INFO ] Creating new user"
    useradd --system --no-create-home --shell=/sbin/nologin hawk-eye
    echo "[ INFO ] Creating new group"
    groupadd hawk-eye
    echo "[ INFO ] Adding root user to the new group"
    usermod -Ghawk-eye "root"
    echo "[ INFO ] Adding hawk-eye user to the new group"
    usermod -Ghawk-eye "hawk-eye"
    
    echo "[ INFO ] Changing permissions for the Installation directory"
    chgrp -R hawk-eye /opt/Hawk-Eye
    chmod -R 070 /opt/Hawk-Eye
    


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
ExecStart= $(which python3) /opt/Hawk-Eye/App/server.py
Restart=always

[Install]
WantedBy=multi-user.target
EOF

    echo "[ INFO ] Enabling mon-agent service"
    systemctl daemon-reload
    systemctl enable mon-agent.service

    echo "[ INFO ] Starting mon-agent service"
    systemctl start mon-agent.service   
       
fi