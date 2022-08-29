

"""
请求下发,上传 命令

{
    "type": "CMD",
    "commond": "curl https://www.baidu.com -o baidu.html",
    "UUID": "F5BB0C8DE146C67B44BABBF4E6584CC0",
    "MD5": "43836e8b6d170c0961dccd683325f688"
}

curl -u admin:123456 ftp://123.52.43.212:60021/info.log -s --connect-timeout 5 -m 120 --retry 1 -T /home/www/smartbox/logs/info.log -v

"""

import requests


def upload_log(client_id, ctype=""):

    url = "http://192.168.240.228:8080/api/IssueOrder"

    assert ctype in ["info", "mq", "gpsevent", "gps_info", "smartbox"]

    cmd = {
            "issue_order": {
                "type": "CMD",
                "commond": "curl -u admin:123456 ftp://123.52.43.212:60021/{}.log -s --connect-timeout 5 -m 120 --retry 1 -T /home/www/smartbox/logs/{}.log -v".format(ctype, ctype),
                "UUID": "F5BB0C8DE146C67B44BABBF4E6584CC0",
                "MD5": "43836e8b6d170c0961dccd683325f688"
            },
            "client_id": client_id
        }

    print(cmd)

    resp = requests.post(url, json=cmd)

    print(resp.json())


def download_file(client_id, filename="", to_path="/home/www/smartbox/"):

    """
    在ftp目录发送
    """

    url = "http://192.168.240.228:8080/api/IssueOrder"

    downed_path = to_path + filename

    cmd = {
            "issue_order": {
                "type": "CMD",
                "commond": "curl -u admin:123456 ftp://123.52.43.212:60021/{} -o {} -v".format(filename, downed_path),
                "UUID": "F5BB0C8DE146C67B44BABBF4E6584CC0",
                "MD5": "43836e8b6d170c0961dccd683325f688"
            },
            "client_id": client_id
        }

    print(cmd)

    resp = requests.post(url, json=cmd)

    print(resp.json())


def cmd(client_id, cmd_info):

    """
    在 /home/www/smartbox/download/ 执行

    curl https://www.baidu.com -o baidu.html

    """

    url = "http://192.168.240.228:8080/api/IssueOrder"

    cmd = {
            "issue_order": {
                "type": "CMD",
                "commond": cmd_info,
                "UUID": "F5BB0C8DE146C67B44BABBF4E6584CC0",
                "MD5": "43836e8b6d170c0961dccd683325f688"
            },
            "client_id": client_id
        }

    print(cmd)

    resp = requests.post(url, json=cmd)

    print(resp.json())


if __name__ == "__main__":
    # upload_log(224624439042706, "info")
    # upload_log(45002131809726, "mq")
    cmd(45002131809726, "sudo supervisorctl -u user -p 123456 restart all")
    # download_file(45002131809726, "tt.txt")
    # download_file(224624439042706, "info.txt", to_path="/home/www/")