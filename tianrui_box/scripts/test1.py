# import time
# import paho.mqtt.client as paho
#
broker="192.168.240.228"
broker="123.52.43.212"
#
# def on_message(client, userdata, message):
#     # time.sleep(1)
#     print("received message =",str(message.payload.decode("utf-8")))
#
# client= paho.Client("test1")
# client.on_message=on_message
#
# client.username_pw_set("admin", "123456")
#
# print("connecting to broker ", broker)
# client.connect(broker, port=1883)   #connect
#
# client.loop_start()      #start loop to process received messages
#
# # time.sleep(5)
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
# time.sleep(4)
#
# print("publish ")
# client.publish("client/79921509528419/error/", "testsererere")  #subscribe
#



# print("publishing ")
# client.publish("client/","on123")#publish
# time.sleep(4)
# client.loop_forever()
#
# client.disconnect() #disconnect
# client.loop_stop() #stop loop


import paho.mqtt.client as mqtt

def on_connect(client, userdata, flags, rc):

    if rc == 0:
        print("sub...")
        client.subscribe('client/#', qos=0)


    print("Connected with result code: " + str(rc))

def on_message(client, userdata, msg):
    print(msg.topic + " " + str(msg.payload))

client = mqtt.Client("test1")
client.on_connect = on_connect
client.on_message = on_message
client.username_pw_set("admin", "123456")
client.connect(broker, 61883, 600)

client.loop_forever() # 保持连接