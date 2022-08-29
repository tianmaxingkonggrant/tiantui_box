

import subprocess
import re
import socket
import fcntl
import struct
import time
import traceback

def _cmd(cmd, ctype="ip"):

    try:
        _ret = subprocess.run(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, cwd="/home/firefly", timeout=5)

        if ctype == "ip":
            ip_list = []
            if _ret.returncode == 0:
                ip_list = re.findall(r'[0-9]+(?:\.[0-9]+){3}', _ret.stdout.decode('utf-8').strip())

            return True if ip_list else False

        if ctype == "super":
            if "FATAL" in _ret.stdout.decode('utf-8'):
                c = 0
                while c < 3:
                    time.sleep(2)
                    _ret1 = subprocess.run("sudo supervisorctl -u user -p 123456 restart all", shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, cwd="/home/firefly", timeout=10)
                    if ("mipi:mipi0: started" in _ret1.stdout.decode('utf-8')) and ("reqrep:reqrep0: started" in _ret1.stdout.decode('utf-8')):
                        break
                    else:
                        c += 1
                        continue
    except Exception as e:
        print(traceback.print_exc())


def get_ip_address(ifname):
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    inet = fcntl.ioctl(s.fileno(), 0x8915, struct.pack('256s', bytes(ifname[:15], 'utf-8')))
    return socket.inet_ntoa(inet[20:24])


while True:
    time.sleep(2)
    try:
        ip = get_ip_address("usb0")
        print("usb0 ip: ", ip)
    except:
        print("usb0 ip get_ip_address error")
        _cmd("sudo udhcpc -i usb0", "ip")
        continue
    else:
        if re.match("[0-9]+(?:\.[0-9]+){3}", ip):
            print("ip ok: ", ip)
            _cmd("sudo supervisorctl -u user -p 123456 status", ctype="super")
        else:
            print("no usb0 ip: err")
            continue