import sys
# 导入套接字模块
import socket
import threading
from socket import *
from threading import Thread
# 导入线程模块
import time
import json

sys.path.append("/home/www/tianrui_box/")

from tcp_server.log import logger
from tcp_server.utils import crc16
from tianrui_box.app.config import DB_CONFIG
from tcp_server.tiaoshi06_01_RSSI_ranging_bluetooth_location import RSSI_location
import queue
import re
import pymysql
from decimal import Decimal

MSG_OFFSET = 17
MSG_HEAD_END = 16

db_queue = queue.Queue()

online_stations = {}


def db_handler():
    t = threading.currentThread()

    print("----------22222 ", t.ident, t.getName())

    conn = pymysql.connect(**DB_CONFIG['tianrui_server_db'], autocommit=True,
                           charset="utf8mb4", connect_timeout=10)

    rssi_loc = RSSI_location(K=10, M=3, MAXD=31.21, MIND=2.4)

    with conn.cursor() as cur:
        cur.execute("select minor_id, lng, lat from tianrui_server_db.b_xinbiao where in_use=1 and status=1")
        data = cur.fetchall()
        signalxy = {c[0]: [float(c[1]), float(c[2])] for c in data}

    from_time = int(time.time())
    while True:
        now = int(time.time())
        if now - from_time > 20:
            with conn.cursor() as cur:
                cur.execute("select minor_id, lng, lat from tianrui_server_db.b_xinbiao where in_use=1 and status=1")
                data = cur.fetchall()
                signalxy = {c[0]: [float(c[1]), float(c[2])] for c in data}
                from_time = now

        while not db_queue.empty():
            msg = db_queue.get()

            mtype = msg.get("mtype")
            if mtype == 1:
                pass
            elif mtype == 2:
                data = msg.get("data")
                node_id = msg.get("node_id")
                print("--->>> 参数： ", data, signalxy)
                calc_data = rssi_loc.loc(data, signalxy)
                logger.info("计算后的位置: %s", calc_data)
                if calc_data == [-1]:
                    continue

                lng = Decimal(str(calc_data[0]))
                lat = Decimal(str(calc_data[1]))

                with conn.cursor() as cur:
                    cur.execute("update tianrui_server_db.b_gongka set lng=%s, lat=%s, update_time=%s where device_id=%s", [lng, lat, now, node_id])
                    cur.execute("insert into tianrui_server_db.b_gps_info(device_id, lng, lat, create_time) values(%s,%s,%s,%s)", [node_id, lng, lat, now])

        time.sleep(0.5)


def fun_num_to_str(num, width, base=16, stype="str"):
    """

    :param num: int or str
    :param width: 输出的宽度
    :param base: 10 or 16
    :param stype: str or list
    :return:
    """
    format_str = '{:0>' + str(width) + 'x}'

    if base == 10:
        ret = format_str.format(int(num))
    elif base == 16:
        if isinstance(num, str):
            ret = format_str.format(int(num, 16))
        else:
            ret = format_str.format(num)

    if stype == "str":
        return ret
    elif stype == "list":
        return re.findall(".{2}", ret)


class Packager(object):

    def __init__(self):
        self.pf_flow_num = 0
        self.msg_len = 0
        self.out = []
        self.general_queue = queue.Queue()

    def general_message(self):
        self.out[5:7] = fun_num_to_str(self.msg_len, 4, 10, "list")
        check_code = fun_num_to_str(hex(crc16(self.out[5:-2])), 4, stype="list")
        self.out[-2:] = check_code
        return self.out

    def package_pf_head(self, protocol, msg_id):
        self.msg_len = 0
        self.out = []
        self.out.extend(protocol.msg_head)
        self.msg_len += len(protocol.msg_head)

        # 消息长度
        self.out.extend(["00", "00"])
        self.msg_len += 2

        self.out.extend(protocol.station_address)
        self.msg_len += len(protocol.station_address)

        self.pf_flow_num += 1
        # 流水号2个字节 {:0>4x}: 右对齐 十六进制，4位，不足0填充。
        flow_num_list = fun_num_to_str(self.pf_flow_num, 4, 10, "list")
        self.out.extend(flow_num_list)
        self.msg_len += len(flow_num_list)

        msg_id_list = fun_num_to_str(msg_id, 2, 16, "list")
        self.out.extend(msg_id_list)
        self.msg_len += len(msg_id_list)
        return 0

    # 打包平台通用应答
    def package_pf_general_response(self, protocol, status=1):

        # 应答流水号 WORD 对应的平台消息的流水号
        self.out.extend(protocol.bs_flow_num)
        self.msg_len += len(protocol.bs_flow_num)

        # 结果 BYTE 1：成功/确认 0：失败
        result = fun_num_to_str(status, 2, 10, "list")
        self.out.extend(result)
        self.msg_len += len(result)

        # 校验码 2个字节 暂时填充
        self.out.extend(["00", "00"])
        self.msg_len += 2
        return 0

    # 设置节点参数
    def package_node_params(self, protocol, node_id, uplink_node_flow_num, node_msg_id):

        head_msg_len = len(self.out)

        self.out.extend(node_id)
        self.msg_len += len(node_id)

        # 应答流水号 WORD 对应的平台消息的流水号
        self.out.extend(uplink_node_flow_num)
        self.msg_len += len(uplink_node_flow_num)

        # 应答流水号 WORD 对应的平台消息的流水号
        node_msg_len = ["0e"]
        self.out.extend(node_msg_len)
        self.msg_len += len(node_msg_len)

        # 节点消息ID
        node_msg_id_list = fun_num_to_str(node_msg_id, 2, stype="list")
        self.out.extend(node_msg_id_list)
        self.msg_len += len(node_msg_id_list)

        update_node_params_num = ["01"]
        self.out.extend(update_node_params_num)
        self.msg_len += len(update_node_params_num)
        # 只更新上报间隔
        update_node_params = ["02", "00", "01"]
        self.out.extend(update_node_params)
        self.msg_len += len(update_node_params)

        # 校验码 1个字节 取低八位
        check_code_str_16 = hex(sum([int(i, 16) for i in self.out[head_msg_len:]]))
        check_code_str = [fun_num_to_str(hex(int(check_code_str_16, 16) & 0xff).replace("0x", ""), 2, 16)]
        self.out.extend(check_code_str)
        self.msg_len += len(check_code_str)

        # 消息结尾符
        msg_end = ["ff"]
        self.out.extend(msg_end)
        self.msg_len += len(msg_end)

        # 校验码 2个字节 暂时填充
        self.out.extend(["00", "00"])
        self.msg_len += 2

        return 0


# 输出十六进制类型数组
def get_hex(bytes):
    ret = []
    for i in bytes:
        hex_num = hex(int(i))
        if len(hex_num) == 3:
            ret.append(hex_num.replace("0x", "0"))
        else:
            ret.append(hex_num.replace("0x", ""))
    return ret


def check_crc_ok(hex_data):
    origin_check_code = int("".join(hex_data[-2:]), 16)
    check_code = crc16(hex_data[5: -2])

    # print("orgin: {} new: {}".format(origin_check_code, check_code))

    if check_code != origin_check_code:
        return False
    return True


class Protocol:
    # 基站 上行 基站转发节点消息 0x04
    BS_FORWARD_MSG_ID = 0x04
    # 节点 0x01 节点位置消息上报 上报间隔默认 5s，服务器无需应答。
    NODE_LOCATION_REPORT_MSG_ID = 0x01
    # 基站心跳 0x01 节点位置消息上报 上报间隔默认 5s，服务器无需应答。
    BS_HEARTBEAT_MSG_ID = 0x01
    # 平台通用应答  消息 ID：0x80。
    PF_GENERAL_RESPONSE_MSG_ID = 0x80
    # 0x03 自动参数消息上报 上报所有配置参数，服务器需应答
    NODE_AUTO_PARAMETERS_REPORT_MSG_ID = 0x03
    # 0x04 按键参数上报消息体格式：同参数自动上报。
    NODE_MANUAL_PARAMETERS_REPORT_MSG_ID = 0x04
    # 平台应答节点消息 平台应答节点消息消息体数据格式见表 13，节点位置信息平台无需应答
    PF_NODE_RESPONSE_MSG_ID = 0x83
    # 设置节点参数，消息体格式： item（参数个数 n）+参数 ID 1 +参数内容 1 + 参数 ID2 +参数内容 2 +…参数 ID n + 参数内容 n
    NODE_SET_PARAMETERS_MSG_ID = 0x83

    def __init__(self):
        self.msg_head = ['78', '75', '6e', '6a', '69']
        self.msg_len = ["00", "00"]
        self.station_address = []
        self.bs_flow_num = []
        self.bs_msg_id = []


class Parser(object):

    def __init__(self, protocol, packager, hex_data):
        self.protocol = protocol
        self.packager = packager
        self.hex_data = hex_data
        self.node_id = []

    def parse_header(self, hex_data, protocol):
        # 解析消息体
        protocol.msg_head = hex_data[:5]
        # 消息长度 2个字节
        protocol.msg_len = hex_data[5:7]
        # 站点地址 6个字节
        protocol.station_address = hex_data[7:13]

        logger.info("基站地址: %s", " ".join(protocol.station_address))

        addr_str = " ".join(protocol.station_address)
        # 在线的站点存放
        if not online_stations.get(addr_str):
            online_stations[addr_str] = 0

        # 流水号 2个字节
        protocol.bs_flow_num = hex_data[13:15]
        # 站点消息ID 1个字节
        protocol.bs_msg_id = hex_data[15:16]
        return 0

    def parse_heartbeat(self):
        # 解析消息体
        pos = MSG_HEAD_END
        # 心跳
        heartbeat = self.hex_data[pos: pos + 2]
        return 0

    def parse_node_location_msg(self, from_offset):
        # 设备电量 1个字节
        device_power_from_index = from_offset
        device_power_end_index = device_power_from_index + 1
        device_power = int(self.hex_data[device_power_from_index: device_power_end_index][0], 16)

        # 设备运动状态 1个字节
        device_act_from_index = device_power_end_index
        device_act_end_index = device_act_from_index + 1
        device_act = int(self.hex_data[device_act_from_index: device_act_end_index][0], 16)

        # logger.info("设备 device_act: %s", device_act)

        # item：（1 byte） 实际上传信标个数 n 1个字节
        beacon_num_from_index = device_act_end_index
        beacon_num_end_index = beacon_num_from_index + 1
        beacon_num = int(self.hex_data[beacon_num_from_index: beacon_num_end_index][0], 16)

        # logger.info("beacon_num: %s", self.hex_data[beacon_num_from_index: beacon_num_end_index])

        save_data = {"mtype": 2, "node_id": "".join(self.node_id), "data": {}}

        # 信标 n 格式：（5 byte） Major（2 byte）+Minor（2 byte）+RSSI（1 byte）
        for i in range(beacon_num):
            # item：（1 byte） 实际上传信标个数 n 1个字节 major
            beacon_major_from_index = beacon_num_end_index + i * 5
            beacon_major_end_index = beacon_major_from_index + 2
            beacon_major = self.hex_data[beacon_major_from_index: beacon_major_end_index]

            # minor
            beacon_minor_from_index = beacon_major_end_index
            beacon_minor_end_index = beacon_minor_from_index + 2
            beacon_minor = self.hex_data[beacon_minor_from_index: beacon_minor_end_index]

            # RSSI
            beacon_rssi_from_index = beacon_minor_end_index
            beacon_rssi_end_index = beacon_rssi_from_index + 1
            beacon_rssi = self.hex_data[beacon_rssi_from_index: beacon_rssi_end_index]

            major_str = str(int("".join(beacon_major), 16))
            minor_str = str(int("".join(beacon_minor), 16))
            rssi_str = str(int(beacon_rssi[0], 16) - 256)
            time_str = str(time.time())

            rssi_int = int(beacon_rssi[0], 16) - 256

            save_data["data"][minor_str] = rssi_int

            logger.info("beacon_major: {}, beacon_minor: {}, beacon_rssi: {}, rssi-10: {} dbm".format(major_str,
                                                                                                      minor_str,
                                                                                                      beacon_rssi,
                                                                                                      rssi_str))

            # if minor_str != "11869":
            #     continue
            #
            # if self.node_id != ['21', '10', '53', '96']:
            #     continue
            #
            # data = [time_str, major_str, minor_str, rssi_str]
            # str_data = ",".join(data)
            # with open("data.txt", "a") as f:
            #     f.write(str_data)
            #     f.write("\n")
        print("======>>>>>>> save_data: ", save_data)
        if save_data.get("data"):
            logger.info("save data put....>>>>>> %s", json.dumps(save_data))
            db_queue.put(save_data)

    def parse_bs_forward_msg(self):
        # 节点消息总数 1个字节, 可能有多条消息
        node_msg_num = int(self.hex_data[16:17][0], 16)

        for i in range(node_msg_num):
            # 上行频点 4个字节
            freq_from_index = MSG_OFFSET + MSG_OFFSET * i
            freq_end_index = freq_from_index + 4
            freq = self.hex_data[freq_from_index:  freq_end_index]

            # 信噪比，单位0.1dB 2个字节
            snr_from_index = freq_end_index
            snr_end_index = snr_from_index + 2
            snr = self.hex_data[snr_from_index:  snr_end_index]

            # RSSI 信号强度，单位1dBm 2个字节
            rssi_from_index = snr_end_index
            rssi_end_index = rssi_from_index + 2
            rssi = self.hex_data[rssi_from_index:  rssi_end_index]

            logger.info("rssi: {} rssi-10: {} dbm".format(rssi, int("".join(rssi), 16) - 65535))

            # SF 扩频因子，取值范围：0x05~0x0C （SF5~SF12） 1个字节
            sf_from_index = rssi_end_index
            sf_end_index = sf_from_index + 1
            sf = self.hex_data[sf_from_index:  sf_end_index]

            # 长度 1个字节
            length_from_index = sf_end_index
            length_end_index = length_from_index + 1
            length = int(self.hex_data[length_from_index: length_end_index][0], 16)
            # logger.info("length: {}".format(length))
            if length < 1:
                continue

            # 节点 ID 节点设备的地址，如 0xC54AD2A8 4个字节
            node_id_from_index = length_end_index
            node_id_end_index = node_id_from_index + 4
            node_id = self.hex_data[node_id_from_index: node_id_end_index]

            logger.info("node_id: {}".format(node_id))

            self.node_id = node_id

            # 按照发送顺序从 0 开始循环累加，范围 0-65535 2个字节
            node_flow_num_from_index = node_id_end_index
            node_flow_num_end_index = node_flow_num_from_index + 2
            node_flow_num = self.hex_data[node_flow_num_from_index: node_flow_num_end_index]

            # 整条消息长度， 消息长度 范围 0~255 1个字节
            node_msg_len_from_index = node_flow_num_end_index
            node_msg_len_end_index = node_msg_len_from_index + 1
            node_msg_len = self.hex_data[node_msg_len_from_index: node_msg_len_end_index]

            # 消息 ID 1个字节
            node_msg_id_from_index = node_msg_len_end_index
            node_msg_id_end_index = node_msg_id_from_index + 1
            node_msg_id = int(self.hex_data[node_msg_id_from_index: node_msg_id_end_index][0], 16)

            # logger.info("node_msg_id: {}".format(node_msg_id))
            logger.info("node_msg_id: %s, node_msg_id_end_index: %s",
                        self.hex_data[node_msg_id_from_index: node_msg_id_end_index], node_msg_id_end_index)

            # if node_msg_id in [Protocol.NODE_MANUAL_PARAMETERS_REPORT_MSG_ID, Protocol.NODE_AUTO_PARAMETERS_REPORT_MSG_ID]:

            # logger.info("转发消息: %s", self.hex_data)

            if node_msg_id == Protocol.NODE_AUTO_PARAMETERS_REPORT_MSG_ID:
                if self.parse_node_auto_parameter_msg(node_msg_id_end_index) == 0:
                    if self.packager.package_pf_head(self.protocol, Protocol.PF_NODE_RESPONSE_MSG_ID) == 0:
                        if self.packager.package_node_params(self.protocol, node_id, node_flow_num, Protocol.NODE_SET_PARAMETERS_MSG_ID) == 0:
                            out_msg = self.packager.general_message()
                            logger.info("NODE_AUTO_PARAMETERS_REPORT_MSG_ID send:  %s", out_msg)
                            self.packager.general_queue.put(" ".join(out_msg))

            if node_msg_id == Protocol.NODE_MANUAL_PARAMETERS_REPORT_MSG_ID:
                if self.parse_node_manual_parameter_msg(node_msg_id_end_index) == 0:
                    if self.packager.package_pf_head(self.protocol, Protocol.PF_NODE_RESPONSE_MSG_ID) == 0:
                        if self.packager.package_node_params(self.protocol, node_id, node_flow_num, Protocol.NODE_SET_PARAMETERS_MSG_ID) == 0:
                            out_msg = self.packager.general_message()
                            logger.info("NODE_MANUAL_PARAMETERS_REPORT_MSG_ID send:  %s", out_msg)
                            self.packager.general_queue.put(" ".join(out_msg))

            if node_msg_id == Protocol.NODE_LOCATION_REPORT_MSG_ID:
                if self.parse_node_location_msg(node_msg_id_end_index) == 0:
                    pass

        return 0

    # 自动获取节点参数
    def parse_node_auto_parameter_msg(self, from_offset):
        # 设备电量 1个字节
        device_power_from_index = from_offset
        device_power_end_index = device_power_from_index + 1
        device_power = int(self.hex_data[device_power_from_index: device_power_end_index][0], 16)

        # 设备运动状态 1个字节
        device_act_from_index = device_power_end_index
        device_act_end_index = device_act_from_index + 1
        device_act = int(self.hex_data[device_act_from_index: device_act_end_index][0], 16)

        # item：（1 byte） 实际上传信标个数 n 1个字节
        parameters_num_from_index = device_act_end_index
        parameters_num_end_index = parameters_num_from_index + 1
        parameters_num = int(self.hex_data[parameters_num_from_index: parameters_num_end_index][0], 16)

        # logger.info("参数内容 parameters_num_end_index: %s, 内容: %s", parameters_num_end_index,
        #             self.hex_data[parameters_num_end_index:])

        # 蓝牙扫描持续时间 0x01 1 取值范围：1~100，单位 100ms，实际：0.1~10s，默认 值：10（1s）
        bluetooth_scan_time_from_index = parameters_num_end_index
        bluetooth_scan_time_end_index = bluetooth_scan_time_from_index + 2
        bluetooth_scan_time_id = int(self.hex_data[bluetooth_scan_time_from_index: bluetooth_scan_time_end_index][0],
                                     16)
        bluetooth_scan_time_value = int(self.hex_data[bluetooth_scan_time_from_index: bluetooth_scan_time_end_index][1],
                                        16)
        # logger.info("bluetooth_scan_time_id: %s, bluetooth_scan_time_value: %s", bluetooth_scan_time_id,
        #             bluetooth_scan_time_value)

        # 位置发送间隔（运动） 0x02 2 取值范围：1~65535，单位 s，默认值：5s
        location_send_interval_time_from_index = bluetooth_scan_time_end_index
        location_send_interval_time_end_index = location_send_interval_time_from_index + 3
        location_send_interval_time_id = int(
            self.hex_data[location_send_interval_time_from_index: location_send_interval_time_end_index][0], 16)
        location_send_interval_time_value = self.hex_data[
                                            location_send_interval_time_from_index: location_send_interval_time_end_index][
                                            1:]
        # logger.info("location_send_interval_time_id: %s, location_send_interval_time_value: %s",
        #             location_send_interval_time_id, location_send_interval_time_value)

        # 加速度使能 0x05 1 取值范围：[0: OFF, 1: ON]，默认：1
        acceleration_enabled_from_index = location_send_interval_time_end_index + 5
        acceleration_enabled_end_index = acceleration_enabled_from_index + 2
        acceleration_enabled_id = int(self.hex_data[acceleration_enabled_from_index: acceleration_enabled_end_index][0],
                                      16)
        acceleration_enabled_value = int(
            self.hex_data[acceleration_enabled_from_index: acceleration_enabled_end_index][1], 16)
        # logger.info("acceleration_enabled_id: %s, acceleration_enabled_value: %s", acceleration_enabled_id,
        #             acceleration_enabled_value)

        # 上行 SF 个数 0x0D 1 取值范围：1~4，默认值：1
        uplink_sf_from_index = acceleration_enabled_end_index + 30
        uplink_sf_end_index = uplink_sf_from_index + 2
        uplink_sf_id = int(self.hex_data[uplink_sf_from_index: uplink_sf_end_index][0], 16)
        uplink_sf_value = int(self.hex_data[uplink_sf_from_index: uplink_sf_end_index][1], 16)
        # logger.info("uplink_sf_id: %s, uplink_sf_value: %s", uplink_sf_id, uplink_sf_value)

        # 上行 SF 起始值 0x0E 1 取值范围：5~12，默认值：7，[ 5:32 6:64 7:128 8:256 9:512 10:1024 11:2048 12:4096 ]
        uplink_sf_initial_value_from_index = uplink_sf_end_index
        uplink_sf_initial_value_end_index = uplink_sf_initial_value_from_index + 2
        uplink_sf_initial_value_id = int(
            self.hex_data[uplink_sf_initial_value_from_index: uplink_sf_initial_value_end_index][0], 16)
        uplink_sf_initial_value_value = int(
            self.hex_data[uplink_sf_initial_value_from_index: uplink_sf_initial_value_end_index][1], 16)
        # logger.info("uplink_sf_initial_value_id: %s, uplink_sf_initial_value_value: %s", uplink_sf_initial_value_id,
        #             uplink_sf_initial_value_value)
        return 0

    # 手动获取节点参数
    def parse_node_manual_parameter_msg(self, from_offset):
        # 设备电量 1个字节
        device_power_from_index = from_offset
        device_power_end_index = device_power_from_index + 1
        device_power = int(self.hex_data[device_power_from_index: device_power_end_index][0], 16)

        # 设备运动状态 1个字节
        device_act_from_index = device_power_end_index
        device_act_end_index = device_act_from_index + 1
        device_act = int(self.hex_data[device_act_from_index: device_act_end_index][0], 16)

        # item：（1 byte） 实际上传信标个数 n 1个字节
        parameters_num_from_index = device_act_end_index
        parameters_num_end_index = parameters_num_from_index + 1
        parameters_num = int(self.hex_data[parameters_num_from_index: parameters_num_end_index][0], 16)

        logger.info("参数内容 parameters_num_end_index: %s, 内容: %s", parameters_num_end_index,
                    self.hex_data[parameters_num_end_index:])

        # 蓝牙扫描持续时间 0x01 1 取值范围：1~100，单位 100ms，实际：0.1~10s，默认 值：10（1s）
        bluetooth_scan_time_from_index = parameters_num_end_index
        bluetooth_scan_time_end_index = bluetooth_scan_time_from_index + 2
        bluetooth_scan_time_id = int(self.hex_data[bluetooth_scan_time_from_index: bluetooth_scan_time_end_index][0],
                                     16)
        bluetooth_scan_time_value = int(self.hex_data[bluetooth_scan_time_from_index: bluetooth_scan_time_end_index][1],
                                        16)


        logger.info("bluetooth_scan_time_id: %s, bluetooth_scan_time_value: %s,  %s", bluetooth_scan_time_id,
                    bluetooth_scan_time_value, self.hex_data[bluetooth_scan_time_from_index: bluetooth_scan_time_end_index])

        # 位置发送间隔（运动） 0x02 2 取值范围：1~65535，单位 s，默认值：5s
        location_send_interval_time_from_index = bluetooth_scan_time_end_index
        location_send_interval_time_end_index = location_send_interval_time_from_index + 3
        location_send_interval_time_id = int(
            self.hex_data[location_send_interval_time_from_index: location_send_interval_time_end_index][0], 16)
        location_send_interval_time_value = self.hex_data[
                                            location_send_interval_time_from_index: location_send_interval_time_end_index][
                                            1:]
        logger.info("location_send_interval_time_id: %s, location_send_interval_time_value: %s",
                    location_send_interval_time_id, location_send_interval_time_value)

        # 加速度使能 0x05 1 取值范围：[0: OFF, 1: ON]，默认：1
        acceleration_enabled_from_index = location_send_interval_time_end_index + 5
        acceleration_enabled_end_index = acceleration_enabled_from_index + 2
        acceleration_enabled_id = int(self.hex_data[acceleration_enabled_from_index: acceleration_enabled_end_index][0],
                                      16)
        acceleration_enabled_value = int(
            self.hex_data[acceleration_enabled_from_index: acceleration_enabled_end_index][1], 16)
        logger.info("acceleration_enabled_id: %s, acceleration_enabled_value: %s", acceleration_enabled_id,
                    acceleration_enabled_value)

        # 上行 SF 个数 0x0D 1 取值范围：1~4，默认值：1
        uplink_sf_from_index = acceleration_enabled_end_index + 30
        uplink_sf_end_index = uplink_sf_from_index + 2
        uplink_sf_id = int(self.hex_data[uplink_sf_from_index: uplink_sf_end_index][0], 16)
        uplink_sf_value = int(self.hex_data[uplink_sf_from_index: uplink_sf_end_index][1], 16)
        logger.info("uplink_sf_id: %s, uplink_sf_value: %s", uplink_sf_id, uplink_sf_value)

        # 上行 SF 起始值 0x0E 1 取值范围：5~12，默认值：7，[ 5:32 6:64 7:128 8:256 9:512 10:1024 11:2048 12:4096 ]
        uplink_sf_initial_value_from_index = uplink_sf_end_index
        uplink_sf_initial_value_end_index = uplink_sf_initial_value_from_index + 2
        uplink_sf_initial_value_id = int(
            self.hex_data[uplink_sf_initial_value_from_index: uplink_sf_initial_value_end_index][0], 16)
        uplink_sf_initial_value_value = int(
            self.hex_data[uplink_sf_initial_value_from_index: uplink_sf_initial_value_end_index][1], 16)
        logger.info("uplink_sf_initial_value_id: %s, uplink_sf_initial_value_value: %s", uplink_sf_initial_value_id,
                    uplink_sf_initial_value_value)
        return 0


class RecvSendhHandler(object):
    def __init__(self, protocol, packager, tcp_client, tcp_client_address):
        self.protocol = protocol
        self.packager = packager
        self.tcp_client = tcp_client
        self.tcp_client_address = tcp_client_address
        self.online = True

    def send_handler(self):
        stoped = False

        while self.online:
            t = threading.currentThread()

            print("----------11111 ", t.ident, t.getName())

            if stoped:
                print("线程终止... ", t.ident, t.getName())
                break
            while not self.packager.general_queue.empty():
                msg = self.packager.general_queue.get()

                msg_list = msg.split()
                byte_msg = bytes.fromhex("".join(msg_list))

                try:
                    send_num = self.tcp_client.send(byte_msg)
                    logger.info("客户端是: %s, 数量: %s, 发送消息: %s", self.tcp_client_address, send_num, msg)
                except Exception as e:
                    print("err-send: ", e)
                    stoped = True
                    break

            time.sleep(2)

    def receive_handler(self):

        buffer = []
        self.tcp_client.settimeout(8)
        while self.online:
            time.sleep(1)
            t = threading.currentThread()

            try:
                recv_data = self.tcp_client.recv(1024)

            except Exception as e:
                logger.info("连接超时: %s", e)
                self.online = False
                break

            # logger.info("原始 recv_data: %s", recv_data)

            if recv_data:
                hex_data0 = get_hex(recv_data)
                hex_data_str = " ".join(hex_data0)
                splited_data = hex_data_str.split("78 75 6e 6a 69")

                for index, item in enumerate(splited_data):
                    if not item:
                        continue
                    if index == 0:
                        if len(buffer) > 1:
                            last_msg = buffer.pop()
                            last_msg_list = last_msg.strip().split()
                            if int("".join(last_msg_list[5:7]), 16) == len(last_msg_list):
                                buffer.append(last_msg)
                            else:
                                last_combine = last_msg + " " + item.strip()
                                buffer.append(last_combine)
                    else:
                        buffer.append("78 75 6e 6a 69 " + item.strip())
            else:
                logger.info("%s 客户端下线了... %s" % (self.tcp_client_address[1], t.getName()))
                self.tcp_client.close()
                self.online = False
                break
            stop_index = -1
            for index, data_str in enumerate(buffer):
                data_str_list = data_str.strip().split()
                if int("".join(data_str_list[5:7]), 16) != len(data_str_list):
                    stop_index = index
                    break

                hex_data = data_str_list

                logger.info("客户端是: %s 线程： %s", self.tcp_client_address, t.getName())
                logger.info("客户端发来的消息是: %s ", " ".join(hex_data))

                check_ok = check_crc_ok(hex_data)
                if not check_ok:
                    logger.info("客户端消息校验没通过!")
                    continue

                parser = Parser(self.protocol, self.packager, hex_data)

                parser.parse_header(hex_data, self.protocol)

                # 客户端消息消息头不正确
                if self.protocol.msg_head != ['78', '75', '6e', '6a', '69']:
                    logger.info("客户端消息消息头不正确! ")
                    continue

                # 基站心跳消息上报
                if int(self.protocol.bs_msg_id[0], 16) == Protocol.BS_HEARTBEAT_MSG_ID:
                    if parser.parse_heartbeat() == 0:
                        if self.packager.package_pf_head(self.protocol, Protocol.PF_GENERAL_RESPONSE_MSG_ID) == 0:
                            if self.packager.package_pf_general_response(self.protocol) == 0:
                                out_msg = self.packager.general_message()
                                self.packager.general_queue.put(" ".join(out_msg))

                # 位置消息上报
                if int(self.protocol.bs_msg_id[0], 16) == Protocol.BS_FORWARD_MSG_ID:
                    parser.parse_bs_forward_msg()

            buffer = [] if stop_index == -1 else buffer[stop_index:]

        logger.info("%s 客户端下线了 no while ... %s" % (self.tcp_client_address[1], t.getName()))
        self.tcp_client.close()
        self.online = False


def message_handler(tcp_socket):
    """等待客户端连接"""
    while True:
        client_socket, client_addr = tcp_socket.accept()

        print("{} online".format(client_addr))

        protocol = Protocol()
        packager = Packager()

        recvsendhandler = RecvSendhHandler(protocol, packager, client_socket, client_addr)

        # 接收消息服务
        tr = Thread(target=recvsendhandler.receive_handler)
        tr.start()

        # 发送消息服务
        tr1 = Thread(target=recvsendhandler.send_handler)
        tr1.start()
        time.sleep(1)


class TcpServer(object):
    """Tcp服务器"""

    def __init__(self, port):
        """初始化对象"""
        self.code_mode = "utf-8"  # 收发数据编码/解码格式
        self.server_socket = socket(AF_INET, SOCK_STREAM)  # 创建socket
        self.server_socket.setsockopt(SOL_SOCKET, SO_REUSEADDR, True)  # 设置端口复用
        self.server_socket.bind(("0.0.0.0", port))  # 绑定IP和Port
        self.server_socket.listen(128)  # 设置为被动socket
        print("Listen on {}".format(port))

    def run(self):
        """等待客户端连接"""
        # 创建线程为客户端服务
        tr = Thread(target=message_handler, args=(self.server_socket,))
        tr.start()

        # 创建线程为数据存储服务
        tr = Thread(target=db_handler)
        tr.start()


if __name__ == '__main__':
    my_server = TcpServer(port=65405)
    my_server.run()

