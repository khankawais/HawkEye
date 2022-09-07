eval getent passwd {$(awk '/^UID_MIN/ {print $2}' /etc/login.defs)..$(awk '/^UID_MAX/ {print $2}' /etc/login.defs)} | cut -d ":" -f 1,6 > /opt/Hawk-Eye/history/directories.txt
getent passwd root | cut -d ":" -f 1,6 >> /opt/Hawk-Eye/history/directories.txt
