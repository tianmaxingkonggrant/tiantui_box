
import logging

import json
import uuid
from datetime import datetime, date
from scripts.log import logger

from paho.mqtt import client as mq_client


# 修复JSON日期
class DateEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, datetime):
            return obj.strftime('%Y-%m-%d %H:%M:%S')
        elif isinstance(obj, date):
            return obj.strftime("%Y-%m-%d")
        elif isinstance(obj, bytes):
            return str(obj, encoding='utf-8')
        else:
            return json.JSONEncoder.default(self, obj)


class MQTT():
    def __init__(self) -> None:
        self.client_id = "100"
        self.host = '192.168.240.228'
        self.port = 1883
        self.user = 'admin'
        self.pwd = '123456'
        self.client = None
        self.will_set_topic = 'client/share/'
        self.subscribe_topic = [("client/#", 0)]
        self.publish_topic = [("public/", 0), ("public/" + self.client_id + '/', 0)]

    def start(self):
        self.client = mq_client.Client(client_id=self.client_id, clean_session=True)
        msg = {"client_id": self.client_id, "msg": "disconnected 1"}
        self.client.will_set(self.will_set_topic, json.dumps(msg, ensure_ascii=False, cls=DateEncoder))
        self.client.on_connect = self.on_connect
        self.client.on_message = self.on_message
        self.client.on_disconnect = self.on_disconnect
        self.client.username_pw_set(self.user, self.pwd)
        self.client.connect_async(self.host, self.port)
        self.client.loop_start()
        # self.client.loop_forever()


    def stop(self):
        self.client.loop_stop()
        self.client.disconnect()

    def on_connect(self, client: mq_client.Client, userdata, flags, rc):

        print(rc, userdata, client, flags)

        if int(rc) == 0:
            try:
                client.subscribe(self.subscribe_topic)
                client.subscribe(self.will_set_topic)

                msg = {"client_id": self.client_id, "msg": "connected"}
                client.publish(self.will_set_topic, json.dumps(msg, ensure_ascii=False, cls=DateEncoder))
            except BaseException as ex:
                logger.info(f'[MQTT订阅失败 {str(ex)}]')
        else:
            logger.info(f'[MQTT连接失败 {str(rc)} {self.__dict__}]')

    def on_disconnect(self, client: mq_client.Client, userdata, rc):
        try:
            msg = {"client_id": self.client_id, "msg": "disconnected 0"}
            client.publish(self.will_set_topic, json.dumps(msg, ensure_ascii=False, cls=DateEncoder))
        except BaseException as ex:
            logger.info(f'[MQTT断开失败 {str(ex)}]')

    def on_message(self, client: mq_client.Client, userdata, msg: mq_client.MQTTMessage):
        try:
            _o_msg = msg.payload.decode('utf-8')

            print(_o_msg)

            logger.info(f'[MQTT订阅消息 {_o_msg}]')
            _msg = json.loads(_o_msg)
            # if '/error/' in msg.topic:
            #     pass
        except BaseException as ex:
            logger.info(f'[MQTT订阅消息解析失败 {str(ex)}]')


_mqtt = MQTT()
_mqtt.start()

_mqtt.client.publish("client/100", json.dumps({"eree": 232}, ensure_ascii=False, cls=DateEncoder))







