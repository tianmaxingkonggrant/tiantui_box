# import time
# import paho.mqtt.client as paho
#
# broker="192.168.240.228"
#
# def on_message(client, userdata, message):
#     # time.sleep(1)
#     print("received message =",str(message.payload.decode("utf-8")))
#
# client= paho.Client("test")
# client.on_message=on_message
#
# client.username_pw_set("admin", "123456")
#
# print("connecting to broker ", broker)
# client.connect(broker, port=1883)   #connect
#
# client.loop_start()      #start loop to process received messages
#
# time.sleep(5)
#
# while not client.is_connected():
#     time.sleep(2)
#     print("sleep,", 2)
#     continue
#
#
# print("connected", client.is_connected())
#
#
# print("is_connected...")
#
# print("subscribing ")
# client.subscribe("client/79921509528419/error/")  #subscribe
#
#
#
#
# # print("publishing ")
# # client.publish("client/","on123")#publish
# # time.sleep(4)
# client.loop_forever()
#
# # client.disconnect() #disconnect
# # client.loop_stop() #stop loop


import paho.mqtt.client as mqtt
from time import sleep

# def on_connect(client, userdata, flags, rc):
#     print("Connected with result code: " + str(rc))
#
# def on_message(client, userdata, msg):
#     print(msg.topic + " " + str(msg.payload))
#
# # broker="192.168.240.228"
# broker="123.52.43.212"
#
# client = mqtt.Client("test")
# client.on_connect = on_connect
# client.on_message = on_message
# client.username_pw_set("admin", "123456")
# client.connect(broker, 61883, 600) # 600为keepalive的时间间隔
#
# # client.loop_start()
# for i in range(100):
#     print(i)
#     # client.publish('fifa', payload=f'amazing{i}', qos=0)
#     client.publish('client/test/123', payload=f'amazing{i}', qos=1)
#     sleep(1) # 可以超过5秒了


# from geopy.geocoders import Nominatim
# geolocator=Nominatim(user_agent= "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_14_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/99.0.4844.84 Safari/537.36")
# location= geolocator.reverse("34.816963 113.568289")
# print(location.address)

import pymysql

DB_CONFIG = {
    "tianrui_server_db": {
        "host": '192.168.240.227',
        "port": 3306,
        "user": 'root',
        "password": '123456',
        "db": "tianrui_server_db"
    },
    "vernemq_db": {
        "host": '192.168.240.227',
        "port": 3306,
        "user": 'root',
        "password": '123456',
        "db": "vernemq_db"
    }
}

conn = pymysql.connect(**DB_CONFIG['tianrui_server_db'], autocommit=True,
                                    charset="utf8mb4", connect_timeout=10)


import time
with open("gps.txt") as f:
    lines = f.read().split("\n")
client_id = 1234567889
from decimal import Decimal

for index, l in enumerate(lines):
    ll = l.strip()
    if not ll:
        break

    lng, lat, time_int, speed = ll.split(",")
    print(lng, lat, time_int, speed)

    lng = Decimal(lng)
    lat = Decimal(lat)
    time_int = int(time.time())
    time_int = int(time_int - 3600) + index
    speed = int(0)

    with conn.cursor() as cur:
        cur.execute("insert into tianrui_server_db.gps_info(device_uuid,lng,lat,speed,create_time) values(%s,%s,%s,%s,%s)",
                    [client_id, lng, lat, speed, time_int])