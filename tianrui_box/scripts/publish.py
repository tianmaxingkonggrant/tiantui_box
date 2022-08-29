# -*- coding=utf8 -*-


import sys
import os


# import mqtt.client as mqtt

# import mqtt.publish as publish
from paho.mqtt import publish


if __name__ == "__main__":
    topic = "public/100"

    ret = publish.single(topic, payload="payload123456",
                            qos=1, hostname="192.168.240.26",
                            port=1883, client_id="100",
                            keepalive=60,
                            transport="tcp",
                            retain=True,
                            auth={'username': "admin", 'password': "123456"}
                            )
    print(ret)