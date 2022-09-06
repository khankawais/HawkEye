# set -x
export DEBIAN_FRONTEND=noninteractive

if [ $(id -u) != 0 ];then
    printf " \n[X] You must be root to run the script\n"
     
else

    echo "[ INFO ] Installing dependencies"
    apt update
    apt install net-tools curl python3 python3-pip -y
    echo "[ INFO ] Creating necessary directories"
    mkdir /opt/Hawk-Eye
    mkdir /opt/Hawk-Eye/auth-log
    mkdir /opt/Hawk-Eye/history
    mkdir /opt/Hawk-Eye/crontab
    echo "[ INFO ] Copying Auth log to installation directory"

    cp dictionary.txt /opt/Hawk-Eye/history/dictionary.txt
    cp api_creds.txt /opt/Hawk-Eye/api_creds.txt
    cp /var/log/auth.log /opt/Hawk-Eye/auth-log/auth.log

    echo "[ INFO ] Fetching user names and their home directories"
    eval getent passwd {$(awk '/^UID_MIN/ {print $2}' /etc/login.defs)..$(awk '/^UID_MAX/ {print $2}' /etc/login.defs)} | cut -d ":" -f 1,6 > /opt/Hawk-Eye/history/directories.txt
    getent passwd root | cut -d ":" -f 1,6 >> /opt/Hawk-Eye/history/directories.txt
    echo "[ INFO ] Adding necessary settings to individual user's bashrc file"
    cat /opt/Hawk-Eye/history/directories.txt | while read users
    do
        user_name=$(echo $users | cut -d: -f 1)
        directory=$(echo $users | cut -d: -f 2)

        cp $directory/.bash_history /opt/Hawk-Eye/history/$( echo $user_name)_bash_history
        echo 'shopt -s histappend                      # append to history, dont overwrite it' >> $directory/.bashrc
        echo 'export PROMPT_COMMAND="history -a; history -c; history -r; $PROMPT_COMMAND"' >> $directory/.bashrc
        echo 'export HISTTIMEFORMAT="%d/%m/%y %T "' >> $directory/.bashrc
        echo '#Added for Hawk-Eye' >> $directory/.bashrc
    done
fi