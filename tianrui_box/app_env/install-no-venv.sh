apt-get install arp-scan
apt-get install supervisor

apt-get install proftpd
echo -e "1234567\n1234567\n" | passwd proftpd
sed -i 's/# RequireValidShell/RequireValidShell/g' /etc/proftpd/proftpd.conf
systemctl enable proftpd
systemctl start proftpd
chmod -R 777 /run/proftpd

cd /home/server
pip3 install --upgrade pip -i https://pypi.douban.com/simple
pip3 install --upgrade distlib -i https://pypi.douban.com/simple
pip3 install --upgrade wheel -i https://pypi.douban.com/simple

pip3 install -r ./app_env/requirements.pip -i https://pypi.douban.com/simple/

echo_supervisord_conf >/etc/supervisor/supervisord.conf
sed -i '/\[unix_http_server]/c;\[unix_http_server]' /etc/supervisor/supervisord.conf
sed -i '/file=\/tmp\/supervisor.sock/c;file=\/tmp\/supervisor.sock' /etc/supervisor/supervisord.conf
sed -i '/;\[inet_http_server]/c[inet_http_server]' /etc/supervisor/supervisord.conf
sed -i '/;port=127.0.0.1:9001/cport=127.0.0.1:9001' /etc/supervisor/supervisord.conf
sed -i '/;user=chrism/cuser=root' /etc/supervisor/supervisord.conf
sed -i '/serverurl=unix:\/\/\/tmp\/supervisor.sock/c;serverurl=unix:\/\/\/tmp\/supervisor.sock' /etc/supervisor/supervisord.conf
sed -i '/;serverurl=http:\/\/127.0.0.1:9001/cserverurl=http:\/\/127.0.0.1:9001' /etc/supervisor/supervisord.conf
sed -i '/;\[include]/c\[include]' /etc/supervisor/supervisord.conf
echo -e "files=/etc/supervisor/conf.d/*.ini" >>/etc/supervisor/supervisord.conf

apt-get install mariadb-server mariadb-client -y
echo -e "\ny\n123456\n123456\ny\nn\ny\ny" | mysql_secure_installation

mysql -uroot -p123456 </home/server/app_env/privileges.sql
mysql -uroot -p123456 </home/server/app_env/server.sql

wget https://pd.zwc365.com/seturl/https://github.com/vernemq/vernemq/releases/download/1.12.1/vernemq-1.12.1.$(lsb_release -c --short).x86_64.deb
dpkg -i vernemq-1.12.1.$(lsb_release -c --short).x86_64.deb
systemctl enable vernemq
sed -i "s|accept_eula = no|accept_eula = yes|" /etc/vernemq/vernemq.conf
sed -i "s|listener.tcp.default = 127.0.0.1:1883|listener.tcp.default = 0.0.0.0:1883|" /etc/vernemq/vernemq.conf
sed -i "s|listener.http.default = 127.0.0.1:8888|listener.http.default = 0.0.0.0:8888|" /etc/vernemq/vernemq.conf
sed -i "s|plugins.vmq_passwd = on|plugins.vmq_passwd = off|" /etc/vernemq/vernemq.conf
sed -i "s|plugins.vmq_acl = on|plugins.vmq_acl = off|" /etc/vernemq/vernemq.conf
sed -i "s|plugins.vmq_diversity = off|plugins.vmq_diversity = on|" /etc/vernemq/vernemq.conf
sed -i "s|vmq_diversity.auth_mysql.enabled = off|vmq_diversity.auth_mysql.enabled = on|" /etc/vernemq/vernemq.conf
sed -i "s|## vmq_diversity.mysql.host = localhost|vmq_diversity.mysql.host = 127.0.0.1|" /etc/vernemq/vernemq.conf
sed -i "s|## vmq_diversity.mysql.user = root|vmq_diversity.mysql.user = root|" /etc/vernemq/vernemq.conf
sed -i "s|## vmq_diversity.mysql.password = password|vmq_diversity.mysql.password = 123456|" /etc/vernemq/vernemq.conf
sed -i "s|## vmq_diversity.mysql.port = 3306|vmq_diversity.mysql.port = 3306|" /etc/vernemq/vernemq.conf


cat /dev/null >/usr/lib/systemd/system/supervisord.service
echo -e "[Unit]
Description=Supervisor process control system for UNIX
Documentation=http://supervisord.org
After=network.target
[Service]
Type=forking
ExecStart=/usr/bin/supervisord -c /etc/supervisor/supervisord.conf
ExecStop=/usr/bin/supervisorctl shutdown
ExecReload=/usr/bin/supervisorctl reload
KillMode=mixed
Restart=on-failure
RestartSec=42s
[Install]
WantedBy=multi-user.target" >>/usr/lib/systemd/system/supervisord.service

systemctl disable supervisor
systemctl enable supervisord
systemctl daemon-reload

cat /dev/null >/etc/supervisor/conf.d/server.ini
echo -e "[fcgi-program:server]
; environment=PYTHONUNBUFFERED=1
socket=tcp://127.0.0.1:8000
directory=/home/server
command=/usr/bin/python3 /home/server/app/app.py
numprocs=1
process_name=server%(process_num)d
loglevel=warn
autostart=true
startsecs=5
stopasgroup=true
killasgroup=true
autorestart=true
startretries=3
user=root
redirect_stderr=false
stdout_logfile_maxbytes=20MB  ; stdout 日志文件大小，默认 50MB
stdout_logfile_backups=0     ; stdout 日志文件备份数
stderr_logfile_maxbytes=20MB  ; stdout 日志文件大小，默认 50MB
stderr_logfile_backups=0
stdout_logfile=/home/server/app/logs/server.log
stderr_logfile=/home/server/app/logs/server_err.log" >>/etc/supervisor/conf.d/server.ini

systemctl start supervisord