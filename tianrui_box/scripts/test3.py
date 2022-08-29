


"""
{
    "type": "Upload",
    "model": "FTP",
    "url": "ftp://172.19.80.1:21/aaa/",
    "user": "admin",
    "pwd": "123456",
    "token": "ea0b468e991ac6a21ccccfa6ab586b67",
    "UUID": "E72B22522FB9DDBD7F9EC89B72FFCCCF",
    "MD5": "f105fb9d8b2e9d49c96e7f573284ed17"
}


{
    "type": "CMD",
    "commond": "curl https://www.baidu.com -o baidu.html",
    "UUID": "F5BB0C8DE146C67B44BABBF4E6584CC0",
    "MD5": "43836e8b6d170c0961dccd683325f688"
}


{
    "type": "CMD",
    "commond": "sudo systemctl restart supervisord",
    "UUID": "F5BB0C8DE146C67B44BABBF4E6584CC0"
}


{
    "type": "Upload",
    "model": "FTP",
    "url": "ftp://192.168.1.13:60021/",
    "user": "admin",
    "pwd": "123456",
    "token": "3260d9006c0c40f5afc85bfb7627c8cc",
    "UUID": "3260d9006c0c40f5afc85bfb7627c8cc"
}


"""
_msg = {
    "type": "Upload",
    "model": "FTP",
    "url": "ftp://123.52.43.212:60021/",
    "user": "admin",
    "pwd": "123456",
    "token": "3260d9006c0c40f5afc85bfb7627c8cc",
    "UUID": "0",
    "MD5":"090e1db639f204b9a5963b018c7bbfe2"
}

_msg = {
    "type": "CMD",
    "commond": "sudo systemctl restart supervisord",
    "UUID": "F5BB0C8DE146C67B44BABBF4E6584CC0",
    "MD5": "41cfbfebdb391b702dd309c0f92763f4"
}

_msg = {
    "type": "CMD",
    "commond": "curl -u admin:123456 ftp://123.52.43.212:60021/MediaServer.log -s --connect-timeout 5 -m 120 --retry 1 -T /home/www/smartbox/logs/MediaServer.log  -v",
    "UUID": "F5BB0C8DE146C67B44BABBF4E6584CC0",
    "MD5": "b7be614917604eb7e92100a781babf50"
}


_msg = {
    "type": "CMD",
    "commond": "curl -u admin:123456 ftp://123.52.43.212:60021/all.log -s --connect-timeout 5 -m 120 --retry 1 -T /home/www/smartbox/logs/all.log  -v",
    "UUID": "F5BB0C8DE146C67B44BABBF4E6584CC0",
    "MD5": "77bb0b0a4d1910fdee90e61e1d7ce4d5"
}

_msg = {
    "type": "CMD",
    "commond": "curl -u admin:123456 ftp://123.52.43.212:60021/UVC_rknn_err.log -s --connect-timeout 5 -m 120 --retry 1 -T /home/www/smartbox/logs/UVC_rknn_err.log -v",
    "UUID": "F5BB0C8DE146C67B44BABBF4E6584CC0",
    "MD5": "9d6150c912de58de6f7fba3db20bfaa9"
}


_msg = {
    "type": "CMD",
    "commond": "sudo supervisorctl -u user -p 123456 status",
    "UUID": "test1",
    "MD5": "c69f50f942fe4e135234b23f5061c5eb"
}



_type = _msg["type"]

data = _type + _msg['commond'] + _msg['UUID']

# data = _type + _msg['model'] + _msg['url'] + _msg['user'] + _msg['pwd'] + _msg['token'] + _msg['UUID']

# _md5 = hashlib.md5(data.encode(encoding='UTF-8')).hexdigest()

import hashlib

a = hashlib.md5(str(data).encode()).hexdigest()

print(a)


