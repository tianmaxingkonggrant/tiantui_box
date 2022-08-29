import sys
sys.path.append("/home/www/tianrui_box/")

from tianrui_box.app.libs import *
from tianrui_box.app.utils import *
from tianrui_box.app.config import *
from tianrui_box.app.coordinate import gcj02towgs84
from uuid import uuid4
from decimal import Decimal
import pymysql
_pProcess = psutil.Process(os.getppid())
if any(x in _pProcess.name() for x in ['bash', 'python']):
    app = Sanic(__name__, log_config=LOGGING_CONFIG_DEFAULTS)
else:
    app = Sanic(__name__, log_config=LOGGING_CONFIG_DEFAULTS_0)
# CORS(app, **{"supports_credentials": True})


app.config.CORS_ORIGINS = "*"
app.config.CORS_METHODS = ["OPTIONS", "GET", "POST", "DELETE", "PUT"]
from sanic_cors import CORS  #加入扩展
CORS(app)

Session(app, interface=InMemorySessionInterface(expiry=7200, sessioncookie=True))


app.config.WEBSOCKET_MAX_SIZE = 2 ** 20
app.config.WEBSOCKET_MAX_QUEUE = 32
app.config.WEBSOCKET_READ_LIMIT = 2 ** 16
app.config.WEBSOCKET_WRITE_LIMIT = 2 ** 16
app.config.WEBSOCKET_PING_INTERVAL = 20
app.config.WEBSOCKET_PING_TIMEOUT = 20


"""
login_req:
    {
        "act": "ca_login",
        "device_id": "866652020842507"
    }

ca_report_location:    

    {
        "CD4":"",
        "act":"ca_report_location",
        "bat_l":"51",
        "bat_v":"3704",
        "body_info":"",
        "body_simple_info":"",
        "bt_signal_info":"",
        "c_accuracy":"38.0",
        "c_speed":"0.06",
        "c_startcount":"0",
        "c_trust":"1",
        "charging":"1",
        "gas_data":"",
        "gps":"2",
        "gps_level":"-1",
        "in_use":"1",
        "is_weared":"1",
        "net_strenth":"4",
        "net_type":"2",
        "notuploaded_video_count":"4",
        "online_type":"2",
        "oxygen_data":"",
        "phoneNumber":"89860465011984594135",
        "rail_status":"0",
        "record_switch":"false",
        "sim_data_num":"0",
        "sim_status":"2",
        "tcard_status":"2",
        "tempdata":"mtktsbattery--25000;mtktscpu--49000;mtktspa---127000;mtktspmic--42365;mtktswmt--42000;mtktsAP--40000;mtktsbtsmdpa--38600;mtkts1--48100;mtkts2--49000;",
        "user_id":"666",
        "x_point":"34.824052",
        "y_point":"113.564389"
    }


"""

DEVICE_IDS = ["866652020842507"]

DEVICE_USER = {"666": "866652020842507"}


login_resp = {
            "cmd": "ca_login",
            "status": True,
            "msg": "登陆成功！",
            "data": {
                "user_id": "666",
                "device_id": "866652020842507",
                "user_name": "",
                "user_img": "",
                "sos_height": ""
            },
            "sip_info": {
                "sip_id": 0,
                "sip_pwd": "",
                "sip_host": ""
            }
        }

ca_report_location_resp = {
                        "cmd": "ca_report_location",
                        "status": True,
                        "msg": "上报成功"
                    }


from asyncio import CancelledError

@app.websocket("/api/helmet")
async def helmet(request, ws):
    while True:

        try:
            recv_data = await ws.recv()
        except CancelledError:
            print(CancelledError)
            continue

        print("[{}] Received: ".format(time.strftime("%Y-%m-%d %H:%M:%S")), recv_data)
        print("\n")

        try:
            recv_data_json = json.loads(recv_data)
        except:
            login_resp["status"] = False
            login_resp["msg"] = "失败!"
            await ws.send(json.dumps(login_resp))
        else:
            if recv_data_json.get("act") == "ca_login":
                if recv_data_json.get("device_id") in DEVICE_IDS:
                    login_resp["status"] = True
                    login_resp["msg"] = "登陆成功！"

                    device_id = recv_data_json.get("device_id")
                    async with await app.ctx.db0.conn() as conn:
                        async with conn.cursor() as cur:
                            await cur.execute("update tianrui_server_db.s_device set status=1 where device_uuid=%s", [device_id])

                    await ws.send(json.dumps(login_resp))
                else:
                    login_resp["status"] = False
                    login_resp["msg"] = "登录失败!"
                    await ws.send(json.dumps(login_resp))

            if recv_data_json.get("act") == "ca_report_location":
                user_id = recv_data_json.get("user_id")
                device_id = DEVICE_USER.get(user_id)
                if not device_id:
                    login_resp["status"] = False
                    login_resp["msg"] = "上报失败!"
                    await ws.send(json.dumps(ca_report_location_resp))
                else:
                    try:
                        lng = recv_data_json.get("y_point", "0")  # 经度
                        lat = recv_data_json.get("x_point", "0")  # 纬度
                        time_int = recv_data_json.get("ctime")  # 创建时间
                        speed = float(recv_data_json.get("c_speed", "0"))  # 创建时间

                        # gps_level = int(recv_data_json.get("gps_level", -1))
                        # if gps_level < 0:
                        #     continue


                        # gcj02坐标系转wgs84坐标系
                        lng, lat = gcj02towgs84(float(lng), float(lat))

                        lng = Decimal(lng)
                        lat = Decimal(lat)
                        now = time.time()
                        time_int = time_int if time_int else now
                        time_int = int(time_int)

                        async with await app.ctx.db0.conn() as conn:
                            async with conn.cursor() as cur:
                                await cur.execute("select device_uuid,update_time from tianrui_server_db.s_device")
                                data = await cur.fetchall()
                                device_update_time = {c["device_uuid"]: c["update_time"] for c in data}

                                await cur.execute(
                                    "insert into tianrui_server_db.gps_info(device_uuid,lng,lat,speed,create_time) values(%s,%s,%s,%s,%s)",
                                    [device_id, lng, lat, speed, time_int])

                                if time_int > device_update_time.get(device_id, 0):
                                    await cur.execute(
                                        "update tianrui_server_db.s_device set lng=%s, lat=%s, speed=%s,status=1,update_time=%s where device_uuid=%s",
                                        [lng, lat, speed, time_int, device_id])
                    except:
                        login_resp["status"] = False
                        login_resp["msg"] = "上报失败,查看参数!"
                        await ws.send(json.dumps(ca_report_location_resp))
                    else:
                        login_resp["status"] = True
                        login_resp["msg"] = "上报成功!"
                        await ws.send(json.dumps(ca_report_location_resp))



class Login(HTTPMethodView):
    async def post(self, request: request.Request):
        """
        登录
        """
        data = request.json
        try:
            acc = str(data['acc'])
            pwd = str(data['pwd'])
            assert len(acc) > 0
            assert len(pwd) > 0
        except BaseException as ex:
            raise XExc(str(ex), 400) from ex

        print(uuid.uuid5(uuid.NAMESPACE_DNS, pwd).hex)

        _ret = []
        async with await app.ctx.db0.conn() as conn:
            async with conn.cursor() as cur:
                await cur.execute(
                    "select id, acc, pwd from tianrui_server_db.s_admin where acc = %s and status = 1 and del_time = ''", [acc])
                _ret = await cur.fetchall()
        if len(_ret) > 1:
            raise XExc('', 499)
        elif len(_ret) < 1:
            raise XExc('', 403)
        else:
            s_pwd = _ret[0]['pwd']
            if uuid.uuid5(uuid.NAMESPACE_DNS, pwd).hex == s_pwd:
                request.ctx.session['acc'] = acc
                request.ctx.session['isLogin'] = True
            else:
                raise XExc('', 403)
        return JSONS(**{"msg": '登录成功'})


class Logout(HTTPMethodView):
    def post(self, request):
        """注销"""
        request.ctx.session['acc'] = None
        request.ctx.session['isLogin'] = False
        return JSONS(**{"msg": '注销成功'})


class UpdatePass(HTTPMethodView):
    async def post(self, request):
        """
        修改密码
        """
        _pass = ''
        try:
            _pass = str(request.json['pass']).strip()
            assert len(_pass) > 5
        except BaseException as ex:
            raise XExc(str(ex), 400) from ex
        acc = request.ctx.session['acc']
        async with await app.ctx.db0.conn() as conn:
            async with conn.cursor() as cur:
                await cur.execute(
                    "update tianrui_server_db.s_admin set pwd = %s, update_time = %s where acc = %s",
                    [uuid.uuid5(uuid.NAMESPACE_DNS, _pass).hex,
                     datetime.now().strftime("%Y-%m-%d %H:%M:%S:%f"), acc])
        return JSONS(**{})


class LocationReport(HTTPMethodView):

    async def post(self, request):
        """
        车辆位置上报

        req:
            device_uuids list of str  设备id 可以传多个设备id, ["2312121", "15897831233"]
        resp:
            {
                "code": 200,
                "status": "success",
                "msg": "成功",
                "data": "",
                "total_count": ""
            }


        """

        data = request.json

        try:
            device_uuids = data.get("device_uuids", [])
            assert len(device_uuids) > 0
        except BaseException as ex:
            raise XExc(str(ex), 400) from ex

        async with await app.ctx.db0.conn() as conn:
            async with conn.cursor() as cur:
                sql = """select device_uuid from tianrui_server_db.s_device where status=1 and device_uuid in ({})""".format( ",".join(device_uuids).strip(","))
                await cur.execute(sql)
                devices = await cur.fetchall()

                devices_info = [i.get("device_uuid") for i in devices]

        for d in device_uuids:
            if d in devices_info:
                pass
            else:
                raise XExc(str(""), 400)

        _uuid = uuid4().hex

        for device_uuid in device_uuids:
            _msg = {
                "type": "SET",
                "stype": "3",
                "operate": "insert",
                "info": "",
                "token": _uuid,
                "UUID": _uuid,
            }

            app.ctx.mqtt.pushMsg(_msg, device_uuid)

            async with await app.ctx.db0.conn() as conn:
                async with conn.cursor() as cur:
                    sql = """update tianrui_server_db.s_device set location_report=0 where device_uuid in ({})""".format(
                        ",".join(device_uuids).strip(","))
                    await cur.execute(sql)

            async with await app.ctx.db0.conn() as conn:
                async with conn.cursor() as cur:
                    await cur.execute(
                        "insert into tianrui_server_db.s_issueorder(device_uuid, uuid, msg, create_time) values(%s,%s,%s,%s)",
                        [device_uuid, _uuid, json.dumps(_msg), time.time()])

        return JSONS(**{"code": 0})


class Xinbiao(HTTPMethodView):

    async def get(self, request):
        """
        获取蓝牙列表信息

        req:
            did int 设备id, 不是uuid, 非必须。传did 只返回指定的设备信息
            page 分页  默认 1
            page_size 分页  默认10
        resp:
            {
                "code": 200,
                "status": "success",
                "msg": "成功",
                "data": [
                    {
                        "did": 67,
                        "major_id": "25605",
                        "minor_id": "11870",
                        "in_use": 1,
                        "status": 0,
                        "lng": 312.537,
                        "lat": 671.065,
                        "altitude": -1,
                        "update_time": "1970-01-01 08:00:00",
                        "create_time": "1970-01-01 08:00:00",
                        "ip": "0.0.0.0"
                    },
                    {
                        "did": 66,
                        "major_id": "25605",
                        "minor_id": "11869",
                        "in_use": 1,
                        "status": 0,
                        "lng": 370.537,
                        "lat": 671.065,
                        "altitude": -1,
                        "update_time": "1970-01-01 08:00:00",
                        "create_time": "1970-01-01 08:00:00",
                        "ip": "0.0.0.0"
                    }
                ],
                "total_count": 10
            }


        """

        data = request.args

        try:
            did = data.get("did")
            page = int(data.get("page", 1)) - 1
            page_size = int(data.get("page_size", 10))
        except BaseException as ex:
            raise XExc(str(ex), 400) from ex

        getall = True if data.get("page") is None else False

        _ret = []
        async with await app.ctx.db0.conn() as conn:
            async with conn.cursor() as cur:
                if did:
                    await cur.execute("select * from tianrui_server_db.b_xinbiao where did=%s", [did])
                else:
                    if getall:
                        await cur.execute("select * from tianrui_server_db.b_xinbiao order by did desc")
                    else:
                        await cur.execute("select * from tianrui_server_db.b_xinbiao order by did desc limit %s, %s",
                                          [page * page_size, page_size])
                _ret = await cur.fetchall()

        async with await app.ctx.db0.conn() as conn:
            async with conn.cursor() as cur:
                await cur.execute("select count(1) as count from tianrui_server_db.b_xinbiao")
                events_count = await cur.fetchone()
        count = events_count.get("count", 0)

        for index, info in enumerate(_ret):
            _ret[index]["create_time"] = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(info.get("create_time", 0)))
            _ret[index]["update_time"] = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(info.get("update_time", 0)))

        return JSONS(**{"data": _ret, "code": 0, "total_count": count})

    async def post(self, request):
        """
        提交基本信息
        req:提交基本信息：
        req:
            {
                "minor_id": "11869",
                "lng": 370.537,
                "lat": 671.065,
                "update_time": "1970-01-01 08:00:00",
                "update_time": "1970-01-01 08:00:00",
                "update_time": "1970-01-01 08:00:00",
            }
        resp:
            {
                "code": 200,
                "status": "success",
                "msg": "成功",
                "data": "",
                "total_count": ""
            }

        """

        data = request.json

        try:
            did = data.get("did")
            major_id = data.get("major_id")
            minor_id = data.get("minor_id")
            lng = str(data.get("lng"))
            lat = str(data.get("lat"))
            in_use = data.get("in_use", 1)
            status = data.get("status", 1)

            assert minor_id
            assert major_id
            assert len(lng) > 0
            assert len(lat) > 0

        except BaseException as ex:
            raise XExc(str(ex), 400) from ex

        update_time = int(time.time())

        lng = Decimal(lng)
        lat = Decimal(lat)

        updated = [lng, lat, in_use, status, update_time, minor_id]

        if did:
            try:
                async with await app.ctx.db0.conn() as conn:
                    async with conn.cursor() as cur:
                        await cur.execute(
                            """update tianrui_server_db.b_xinbiao set lng=%s, lat=%s, in_use=%s,status=%s, update_time=%s where minor_id=%s""",
                            updated)
            except pymysql.err.IntegrityError:
                raise XExc(str(""), 497)
        else:
            async with await app.ctx.db0.conn() as conn:
                async with conn.cursor() as cur:
                    await cur.execute(
                        """insert into tianrui_server_db.b_xinbiao(major_id, minor_id, lng, lat,in_use,status, create_time, update_time) values(%s,%s,%s,%s,%s,%s,%s,%s)""",
                        [str(major_id), str(minor_id), lng, lat, in_use, status, update_time, update_time])

        return JSONS(**{"code": 0})

    async def delete(self, request):
        """
        删除设备列表

        req:
            did
        resp:

            {
                "code": 200,
                "status": "success",
                "msg": "成功",
                "data": "",
                "total_count": ""
            }

        """

        data = request.json

        try:
            did = data.get("did")
            assert did
        except BaseException as ex:
            raise XExc(str(ex), 400) from ex

        async with await app.ctx.db0.conn() as conn:
            async with conn.cursor() as cur:
                await cur.execute("delete from tianrui_server_db.b_xinbiao where did=%s",
                                  [did, ])

        return JSONS(**{"code": 0})


class Gongka(HTTPMethodView):

    async def get(self, request):
        """
        获取工卡列表信息

        req:
            did int 设备id, 不是uuid, 非必须。传did 只返回指定的设备信息
            name 搜索的名字，非必填。
            page 分页  默认 1
            page_size 分页  默认10
        resp:
            {
                "code": 200,
                "status": "success",
                "msg": "成功",
                "data": [
                    {
                        "did": 59,
                        "device_id": "21105394",
                        "in_use": 1,
                        "create_time": "1970-01-01 08:00:00",
                        "update_time": "1970-01-01 08:00:00",
                        "status": 1,
                        "lng": 332.537,
                        "lat": 650.065,
                        "speed": -1.0,
                        "driver": "",
                        "altitude": -1,
                        "ip": "0.0.0.0"
                    },
                    {
                        "did": 58,
                        "device_id": "21105393",
                        "in_use": 1,
                        "create_time": "1970-01-01 08:00:00",
                        "update_time": "1970-01-01 08:00:00",
                        "status": 1,
                        "lng": 312.537,
                        "lat": 671.065,
                        "speed": -1.0,
                        "driver": "",
                        "altitude": -1,
                        "ip": "0.0.0.0"
                    }
                ],
                "total_count": 2
            }


        """

        data = request.args

        try:
            did = data.get("did")
            name = data.get("name")
            page = int(data.get("page", 1)) - 1
            page_size = int(data.get("page_size", 10))
        except BaseException as ex:
            raise XExc(str(ex), 400) from ex

        getall = True if data.get("page") is None else False

        _ret = []
        async with await app.ctx.db0.conn() as conn:
            async with conn.cursor() as cur:
                if did:
                    await cur.execute("select * from tianrui_server_db.b_gongka where did=%s", [did])
                else:
                    if name:
                        sql = f"select * from tianrui_server_db.b_gongka where name like '%%{name}%%' order by did desc limit %s, %s"
                        await cur.execute(sql, [page * page_size, page_size])
                    else:
                        if getall:
                            await cur.execute("select * from tianrui_server_db.b_gongka order by did desc")
                        else:
                            await cur.execute("select * from tianrui_server_db.b_gongka order by did desc limit %s, %s",
                                              [page * page_size, page_size])
                _ret = await cur.fetchall()

        async with await app.ctx.db0.conn() as conn:
            async with conn.cursor() as cur:
                await cur.execute("select count(1) as count from tianrui_server_db.b_gongka")
                events_count = await cur.fetchone()
        count = events_count.get("count", 0)

        for index, info in enumerate(_ret):
            _ret[index]["create_time"] = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(info.get("create_time", 0)))
            _ret[index]["update_time"] = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(info.get("update_time", 0)))

        return JSONS(**{"data": _ret, "code": 0, "total_count": count})

    async def post(self, request):
        """
        提交基本信息
        req:提交基本信息：
        req:
            {
            "device_id": "21105393",
            "name":"校长",
            "in_use": 1,
            "status": 1
        }
        resp:
            {
                "code": 200,
                "status": "success",
                "msg": "成功",
                "data": "",
                "total_count": ""
            }

        """

        data = request.json

        try:
            did = data.get("did")
            device_id = data.get("device_id")
            name = data.get("name")
            lng = str(data.get("lng", 0))
            lat = str(data.get("lat", 0))
            in_use = data.get("in_use", 1)
            status = data.get("status", 1)

            assert name
            assert device_id
            assert len(lng) > 0
            assert len(lat) > 0

        except BaseException as ex:
            raise XExc(str(ex), 400) from ex

        update_time = int(time.time())

        lng = Decimal(lng)
        lat = Decimal(lat)

        updated = [name, lng, lat, in_use, status, update_time, device_id]

        if did is None and device_id:
            async with await app.ctx.db0.conn() as conn:
                async with conn.cursor() as cur:
                    await cur.execute("select count(1) as count from tianrui_server_db.b_gongka where device_id=%s", [device_id, ])
                    has_one = await cur.fetchone()
                    if has_one.get("count"):
                        raise XExc(str("设备数据已存在"), 498)

        if did:
            try:
                async with await app.ctx.db0.conn() as conn:
                    async with conn.cursor() as cur:
                        await cur.execute(
                            """update tianrui_server_db.b_gongka set name=%s,lng=%s, lat=%s, in_use=%s, status=%s, update_time=%s where device_id=%s""",
                            updated)
            except pymysql.err.IntegrityError:
                raise XExc(str(""), 497)
        else:
            async with await app.ctx.db0.conn() as conn:
                async with conn.cursor() as cur:
                    await cur.execute(
                        """insert into tianrui_server_db.b_gongka(device_id, name,lng, lat, in_use, status, update_time,create_time) values(%s,%s,%s,%s,%s,%s,%s,%s)""",
                        [device_id, name,lng, lat, in_use, status, update_time, update_time])

        return JSONS(**{"code": 0})


    async def delete(self, request):
        """
        删除设备列表

        req:
            did
        resp:

            {
                "code": 200,
                "status": "success",
                "msg": "成功",
                "data": "",
                "total_count": ""
            }

        """

        data = request.json

        try:
            did = data.get("did")
            assert did
        except BaseException as ex:
            raise XExc(str(ex), 400) from ex

        async with await app.ctx.db0.conn() as conn:
            async with conn.cursor() as cur:
                await cur.execute("delete from tianrui_server_db.b_gongka where did=%s",
                                  [did, ])

        return JSONS(**{"code": 0})

class Devices(HTTPMethodView):

    async def get(self, request):
        """
        获取车, 设备列表信息

        req:
            did int 设备id, 不是uuid, 非必须。传did 只返回指定的设备信息
        resp:
            {
                "code": 200,
                "status": "success",
                "msg": "成功",
                "data": [
                    {
                        "did": 16,
                        "device_uuid": "124",   # 设备uuid
                        "device_ver": null,  # 设备版本
                        "sys_ver": null,    # 系统版本
                        "device_model": null,  # 系统模型
                        "create_time": "2022-03-28 17:05:19",
                        "update_time": "2022-03-28 17:05:19",
                        "status": 0,
                        "lng": 0.0,      # 当前经度
                        "lat": 0.0,      # 当前纬度
                        "car_code": "",  # 车牌
                        "driver": "",      # 司机
                        "limited_speed": 0  # 限速
                    },
                    {
                        "did": 17,
                        "device_uuid": null,
                        "device_ver": null,
                        "sys_ver": null,
                        "device_model": null,
                        "create_time": "2022-03-28 17:05:19",
                        "update_time": "2022-03-28 17:05:19",
                        "status": 0,
                        "lng": 0.0,
                        "lat": 0.0,
                        "car_code": "",
                        "driver": "",
                        "limited_speed": 0
                    }
                ],
                "total_count": 2
            }


        """

        data = request.args

        try:
            did = data.get("did")
            page = int(data.get("page", 0))
            page_size = int(data.get("page_size", 10))
        except BaseException as ex:
            raise XExc(str(ex), 400) from ex

        _ret = []
        async with await app.ctx.db0.conn() as conn:
            async with conn.cursor() as cur:
                if did:
                    await cur.execute("select * from tianrui_server_db.s_device where did=%s", [did])
                else:
                    await cur.execute("select * from tianrui_server_db.s_device order by did desc limit %s, %s", [page * page_size, page_size])
                _ret = await cur.fetchall()

        async with await app.ctx.db0.conn() as conn:
            async with conn.cursor() as cur:
                await cur.execute("select count(1) as count from tianrui_server_db.s_device")
                events_count = await cur.fetchone()
        count = events_count.get("count", 0)

        for index, info in enumerate(_ret):
            _ret[index]["create_time"] = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(info.get("create_time", 0)))
            _ret[index]["update_time"] = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(info.get("update_time", 0)))

        return JSONS(**{"data": _ret, "code": 0, "total_count": count})

    async def post(self, request):
        """
        提交基本信息：device_uuid, car_code(车牌), limited_speed(限速), driver(司机)
        req:
            {
                "device_uuid": "23112",
                "car_code": "豫A28G99",
                "limited_speed": 60,
                "driver": "万盛",
                "lng":"113.537055",
                "lat":"34.817131",
                "cron_time": 10,       # 定时上报时间， 单位秒, 非必填，默认 0，不限制
                "cron_distance": 1000, # 定距上报， 单位米, 非必填，默认 0，不限制
                "tire_time":10800      # 疲劳驾驶时间设定，单位秒, 非必填，默认 0，不限制
            }
        resp:
            {
                "code": 200,
                "status": "success",
                "msg": "成功",
                "data": "",
                "total_count": ""
            }

        """

        data = request.json

        try:
            did = data.get("did")
            device_uuid = data.get("device_uuid")
            car_code = data.get("car_code")
            lng = str(data.get("lng"))
            lat = str(data.get("lat"))
            limited_speed = int(data.get("limited_speed"))
            driver = data.get("driver", "")

            cron_time = data.get("cron_time", 0)
            cron_distance = data.get("cron_distance", 0)
            tire_time = data.get("tire_time", 0)

            assert device_uuid
            assert car_code
            assert limited_speed > 0
            assert  len(lng) > 0
            assert  len(lat) > 0
            assert cron_distance >= 0
            assert cron_time >= 0
            assert tire_time >= 0

        except BaseException as ex:
            raise XExc(str(ex), 400) from ex

        if did is None and device_uuid:
            async with await app.ctx.db0.conn() as conn:
                async with conn.cursor() as cur:
                    await cur.execute("select count(1) as count from tianrui_server_db.s_device where device_uuid=%s", [device_uuid])
                    has_one = await cur.fetchone()
                    if has_one.get("count"):
                        raise XExc(str("设备数据已存在"), 498)

        limited_speed_changed = False
        cron_time_changed = False
        cron_distance_changed = False
        tire_time_changed = False

        async with await app.ctx.db0.conn() as conn:
            async with conn.cursor() as cur:
                if did:

                    await cur.execute("select * from tianrui_server_db.s_device where did=%s", [did])

                    device_info = await cur.fetchone()

                    if limited_speed != device_info.get("limited_speed"):
                        limited_speed_changed = True

                    if cron_time != device_info.get("cron_time"):
                        cron_time_changed = True

                    if cron_distance != device_info.get("cron_distance"):
                        cron_distance_changed = True

                    if tire_time != device_info.get("tire_time"):
                        tire_time_changed = True

                    updated = [car_code, limited_speed, Decimal(lng), Decimal(lat), driver, time.time(), cron_time, cron_distance, tire_time, did]

                    await cur.execute(
                        """update tianrui_server_db.s_device set car_code=%s, limited_speed=%s, 
                           lng=%s, lat=%s, driver=%s, update_time=%s,cron_time=%s,cron_distance=%s,tire_time=%s where did=%s""", updated)
                else:
                    limited_speed_changed = True
                    cron_time_changed = True
                    cron_distance_changed = True
                    tire_time_changed = True
                    try:
                        await cur.execute("""insert into tianrui_server_db.s_device(device_uuid, car_code, limited_speed,lng,lat,driver,create_time, update_time, cron_time, cron_distance, tire_time) values(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)""",
                                  [device_uuid, car_code, limited_speed, Decimal(lng), Decimal(lat), driver, time.time(), time.time(), cron_time, cron_distance, tire_time])
                    except pymysql.err.IntegrityError:
                        raise XExc(str(""), 497)

        # 更新 devices_info
        if did:
            app.ctx.mqtt.devices_info[device_info.get("device_uuid")] = {'car_code': car_code, 'driver': driver, 'limited_speed': limited_speed}
        else:
            app.ctx.mqtt.devices_info[device_uuid] = {'car_code': car_code, 'driver': driver, 'limited_speed': limited_speed}

        if limited_speed_changed:

            _uuid = uuid4().hex

            _msg = {
                "type": "SET",
                "stype": "1",
                "operate": "insert",
                "info": "1;{};;pahttype:;radius:;st:;et:;pt:0;path:;".format(limited_speed),
                "token": _uuid,
                "UUID": _uuid,
            }

            app.ctx.mqtt.pushMsg(_msg, device_uuid)

            async with await app.ctx.db0.conn() as conn:
                async with conn.cursor() as cur:
                    await cur.execute(
                        "insert into tianrui_server_db.s_issueorder(device_uuid, uuid, msg, create_time) values(%s,%s,%s,%s)",
                        [device_uuid, _uuid, json.dumps(_msg), time.time()])

        if cron_time_changed or cron_distance_changed or tire_time_changed:

            _uuid = uuid4().hex

            _msg = {
                "type": "SET",
                "stype": "4",
                "operate": "insert",
                "info": json.dumps({"cron_time": cron_time, "cron_distance": cron_distance, "tire_time": tire_time}),
                "token": _uuid,
                "UUID": _uuid,
            }

            app.ctx.mqtt.pushMsg(_msg, device_uuid)

            async with await app.ctx.db0.conn() as conn:
                async with conn.cursor() as cur:
                    await cur.execute(
                        "insert into tianrui_server_db.s_issueorder(device_uuid, uuid, msg, create_time) values(%s,%s,%s,%s)",
                        [device_uuid, _uuid, json.dumps(_msg), time.time()])

        return JSONS(**{"code": 0})

    async def delete(self, request):
        """
        删除设备列表

        req:
            did 设备did 不是 device_uuid
        resp:

            {
                "code": 200,
                "status": "success",
                "msg": "成功",
                "data": "",
                "total_count": ""
            }

        """

        data = request.args

        try:
            did = data.get("did").strip()
            assert did
        except BaseException as ex:
            raise XExc(str(ex), 400) from ex

        device_uuid = None
        async with await app.ctx.db0.conn() as conn:
            async with conn.cursor() as cur:
                await cur.execute("select device_uuid from tianrui_server_db.s_device where did=%s",
                                  [did, ])
                device = await cur.fetchone()

                if device:
                    device_uuid = device.get("device_uuid")
                await cur.execute("delete from tianrui_server_db.s_device where did=%s",
                                  [did, ])

        _uuid = uuid4().hex

        _msg = {
            "type": "SET",
            "stype": "1",
            "operate": "delete",
            "info": "1;{};;pahttype:;radius:;st:;et:;pt:0;path:;".format(1000),
            "token": _uuid,
            "UUID": _uuid,
        }

        # 如果删除限速，则设置一个很难超过的速度代替
        if device_uuid:
            # 更新 devices_info
            try:
                app.ctx.mqtt.devices_info.pop(device_uuid)
            except:
                pass
            app.ctx.mqtt.pushMsg(_msg, device_uuid)
        # 设置定时定距疲劳驾驶时间
        if device_uuid:
            _uuid1 = uuid4().hex
            _msg = {
                "type": "SET",
                "stype": "4",
                "operate": "delete",
                "info": json.dumps({"cron_time": 0, "cron_distance": 0, "tire_time": 0}),
                "token": _uuid1,
                "UUID": _uuid1,
            }

            app.ctx.mqtt.pushMsg(_msg, device_uuid)

            async with await app.ctx.db0.conn() as conn:
                async with conn.cursor() as cur:
                    await cur.execute(
                        "insert into tianrui_server_db.s_issueorder(device_uuid, uuid, msg, create_time) values(%s,%s,%s,%s)",
                        [device_uuid, _uuid1, json.dumps(_msg), time.time()])

        return JSONS(**{"code": 0})


class DevicesV2(HTTPMethodView):

    """
    主要对接视频模块
    """

    async def get(self, request):
        """
        获取车, 设备列表信息

        req:
            did int 设备id, 不是uuid, 非必须。传did 只返回指定的设备信息
        resp:
            {
                "code": 200,
                "status": "success",
                "msg": "成功",
                "data": [
                    {
                        "did": 51,
                        "device_uuid": "224624436340742",
                        "status": 1,
                        "car_code": "测试95",
                        "driver": "测试95",
                        "flv_url": "http://192.168.240.227:8088/live/45002131809777.live.flv",
                        "max_pushed_time": 60,
                        "cam_url": "rtsp://admin:admin123456@192.168.1.124:554"
                    },
                    {
                        "did": 37,
                        "device_uuid": "45002131809795",
                        "status": 0,
                        "car_code": "豫F2356A",
                        "driver": "肖战1.39",
                        "flv_url": "http://192.168.240.227:8088/live/45002131809777.live.flv",
                        "max_pushed_time": 60,
                        "cam_url": "rtsp://admin:admin123456@192.168.1.124:554"
                    }
                ],
                "total_count": 2
            }

        """

        data = request.args

        try:
            did = data.get("did")
            page = int(data.get("page", 0))
            page_size = int(data.get("page_size", 10))
        except BaseException as ex:
            raise XExc(str(ex), 400) from ex

        _ret = []
        async with await app.ctx.db0.conn() as conn:
            async with conn.cursor() as cur:
                if did:
                    await cur.execute("select * from tianrui_server_db.s_device where did=%s", [did])
                else:
                    await cur.execute("select * from tianrui_server_db.s_device order by did desc limit %s, %s", [page * page_size, page_size])
                _ret = await cur.fetchall()

        async with await app.ctx.db0.conn() as conn:
            async with conn.cursor() as cur:
                await cur.execute("select count(1) as count from tianrui_server_db.s_device")
                events_count = await cur.fetchone()
        count = events_count.get("count", 0)

        for index, info in enumerate(_ret):
            _ret[index]["create_time"] = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(info.get("create_time", 0)))
            _ret[index]["update_time"] = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(info.get("update_time", 0)))

            # TODO 临时调整，增加pro支持 http://192.168.240.227:8088/live/46767510625264.h264.live.flv
            if info.get("flv_url"):
                if info["device_uuid"] in ["46767510625264"]:
                    flv_url = "{}/live/{}.h264.live.flv".format(info.get("flv_url"), info["device_uuid"])
                else:
                    flv_url = "{}/live/{}.live.flv".format(info.get("flv_url"), info["device_uuid"])
                _ret[index]["flv_url"] = flv_url

        # 返回新数据
        ret_new = []
        keys = ["did", "device_uuid", "status", "car_code", "driver", "flv_url", "max_pushed_time", "cam_url", "create_time", "update_time"]
        for info in _ret:
            use = {}
            for key in keys:
                use[key] = info.get(key)
            ret_new.append(use)

        return JSONS(**{"data": ret_new, "code": 0, "total_count": count})

    async def post(self, request):
        """
        提交基本信息：device_uuid, car_code(车牌), limited_speed(限速), driver(司机)
        req:
            {
                "device_uuid": "45002131809777",
                "car_code": "豫P6666",
                "driver": "万盛",
                "flv_url": "http://192.168.240.227:8088",
                "flv_url_push": "rtmp://192.168.240.227:1935",
                "cam_url": "rtsp://admin:admin123456@192.168.1.124:554",
                "max_pushed_time": 60,
                "did":49,
            }
        resp:
            {
                "code": 200,
                "status": "success",
                "msg": "成功",
                "data": "",
                "total_count": ""
            }

        """

        data = request.json

        try:
            did = data.get("did")
            device_uuid = data.get("device_uuid")
            car_code = data.get("car_code")
            driver = data.get("driver", "")

            flv_url_push = data.get("flv_url_push", "")
            flv_url = data.get("flv_url", "")
            cam_url = data.get("cam_url", "")
            max_pushed_time = data.get("max_pushed_time", 60)

            flv_url = flv_url[:-1] if flv_url.endswith("/") else flv_url
            flv_url_push = flv_url_push[:-1] if flv_url_push.endswith("/") else flv_url_push
            # cam_url = cam_url[:-1] if cam_url.endswith("/") else cam_url

            assert device_uuid
            assert car_code
            assert flv_url
            assert flv_url_push
            assert cam_url
            assert max_pushed_time


        except BaseException as ex:
            raise XExc(str(ex), 400) from ex

        if did is None and device_uuid:
            async with await app.ctx.db0.conn() as conn:
                async with conn.cursor() as cur:
                    await cur.execute("select count(1) as count from tianrui_server_db.s_device where device_uuid=%s", [device_uuid])
                    has_one = await cur.fetchone()
                    if has_one.get("count"):
                        raise XExc(str("设备数据已存在"), 498)

        flv_url_push_changed = False
        cam_url_changed = False
        max_pushed_time_changed = False

        async with await app.ctx.db0.conn() as conn:
            async with conn.cursor() as cur:
                if did:
                    await cur.execute("select * from tianrui_server_db.s_device where did=%s", [did])

                    device_info = await cur.fetchone()

                    if flv_url_push_changed != device_info.get("flv_url_push"):
                        flv_url_push_changed = True

                    if cam_url != device_info.get("cam_url"):
                        cam_url_changed = True

                    if max_pushed_time != device_info.get("max_pushed_time"):
                        max_pushed_time_changed = True

                    updated = [car_code, flv_url, cam_url, flv_url_push, max_pushed_time, driver, time.time(), did]

                    await cur.execute(
                        """update tianrui_server_db.s_device set car_code=%s, flv_url=%s, cam_url=%s, flv_url_push=%s, max_pushed_time=%s, driver=%s, update_time=%s where did=%s""", updated)
                else:
                    flv_url_push_changed = True
                    cam_url_changed = True
                    max_pushed_time_changed = True
                    try:
                        await cur.execute("""insert into tianrui_server_db.s_device(device_uuid, car_code,flv_url, cam_url, flv_url_push, max_pushed_time,driver,create_time, update_time) values(%s,%s,%s,%s,%s,%s,%s,%s,%s)""",
                                  [device_uuid, car_code, flv_url, cam_url, flv_url_push, max_pushed_time, driver, time.time(), time.time()])
                    except pymysql.err.IntegrityError:
                        raise XExc(str(""), 497)

        if flv_url_push_changed or cam_url_changed or max_pushed_time_changed:

            _uuid = uuid4().hex

            _msg = {
                "type": "SET",
                "stype": "6",
                "operate": "insert",
                "info": json.dumps({"flv_url_push": flv_url_push, "cam_url": cam_url, "max_pushed_time": max_pushed_time}),
                "token": _uuid,
                "UUID": _uuid,
            }

            app.ctx.mqtt.pushMsg(_msg, device_uuid)

            async with await app.ctx.db0.conn() as conn:
                async with conn.cursor() as cur:
                    await cur.execute(
                        "insert into tianrui_server_db.s_issueorder(device_uuid, uuid, msg, create_time) values(%s,%s,%s,%s)",
                        [device_uuid, _uuid, json.dumps(_msg), time.time()])

        return JSONS(**{"code": 0})

    async def delete(self, request):
        """
        删除设备列表

        req:
            did 设备did 不是 device_uuid
        resp:

            {
                "code": 200,
                "status": "success",
                "msg": "成功",
                "data": "",
                "total_count": ""
            }

        """

        data = request.args

        try:
            did = data.get("did").strip()
            assert did
        except BaseException as ex:
            raise XExc(str(ex), 400) from ex

        async with await app.ctx.db0.conn() as conn:
            async with conn.cursor() as cur:
                await cur.execute("delete from tianrui_server_db.s_device where did=%s", [did, ])

        return JSONS(**{"code": 0})


class VideoPlay(HTTPMethodView):

    async def post(self, request):
        """
        视频播放下发

        req:
             device_uuids list of str  设备id 可以传多个设备id, ["2312121", "15897831233"]
             play int 1 播放 0 暂停/停止

            {
                "device_uuids": ["45002131809777"],
                "play":1
            }

        resp:

            {
                "code": 200,
                "status": "success",
                "msg": "成功",
                "data": "",
                "total_count": ""
            }

        ffmpeg -re -rtsp_transport tcp -i rtsp://admin:admin123456@192.168.1.124:554 -vcodec copy -acodec copy -f flv rtmp://192.168.240.227/live/test

        """

        data = request.json

        try:
            device_uuids = data.get("device_uuids", [])
            play = data.get("play")
            assert len(device_uuids) > 0
            assert play in [0, 1]
        except BaseException as ex:
            raise XExc(str(ex), 400) from ex

        async with await app.ctx.db0.conn() as conn:
            async with conn.cursor() as cur:
                sql = """select device_uuid,flv_url_push, cam_url, max_pushed_time from tianrui_server_db.s_device where status=1 and device_uuid in ({})""".format( ",".join(device_uuids).strip(","))
                await cur.execute(sql)
                devices = await cur.fetchall()

                devices_info = {i.get("device_uuid"): [i.get("flv_url_push"), i.get("cam_url"), i.get("max_pushed_time")] for i in devices}

        valid_devices_info = list(devices_info.keys())

        for d in device_uuids:
            if d in valid_devices_info:
                pass
            else:
                raise XExc(str(""), 400)

        _uuid = uuid4().hex

        for device_uuid in device_uuids:
            device = devices_info[device_uuid]

            # TODO 临时调整，增加pro支持 http://192.168.240.227:8088/live/46767510625264.h264.live.flv
            if device_uuid in ["46767510625264"]:
                cmd = "nohup /home/linaro/mpi_encx_test -w 720 -h 480 -t 7 -i /dev/video5 -o {}/live/{}.h264 -n 2400 2>&1 >/dev/null &".format(device[0], device_uuid)
            else:
                cmd = "nohup ffmpeg -t {} -re -rtsp_transport tcp -i \"{}\" -vcodec copy -acodec copy -f flv {}/live/{} 2>&1 >/dev/null &".format(str(device[2]), device[1], device[0], device_uuid)

            _msg = {
                "type": "SET",
                "stype": "7",
                "operate": "play" if play == 1 else "stop",
                "info": cmd,
                "token": _uuid,
                "UUID": _uuid,
            }
            app.ctx.mqtt.pushMsg(_msg, device_uuid)
            async with await app.ctx.db0.conn() as conn:
                async with conn.cursor() as cur:
                    await cur.execute(
                        "insert into tianrui_server_db.s_issueorder(device_uuid, uuid, msg, create_time) values(%s,%s,%s,%s)",
                        [device_uuid, _uuid, json.dumps(_msg), time.time()])

        return JSONS(**{"code": 0})


class IssueOrder(HTTPMethodView):

    async def post(self, request):

        """
        下发指令

        {
                "type": "Download",
                "model": "FTP",
                "url": "ftp://172.19.80.1:21/aaa/data.zip",
                "user": "admin",
                "pwd": "123456",
                "token": "ea0b468e991ac6a21ccccfa6ab586b67",
                "UUID": "F5BB0C8DE146C67B44BABBF4E6584CC0",
                "MD5": "0a48a8ad93bcaee27ac5ad61f98b3566"
            }

        """

        data = request.json

        try:

            issue_order = data.get("issue_order")
            client_id = str(data.get("client_id"))

            data = issue_order

            _type = str(data['type'])

            assert _type in ["CMD", "Download", "Upload"]
            assert len(client_id) > 0

            if _type in ["Download", "Upload"]:
                url = str(data['url'])
                model = str(data['model'])
                user = str(data['user'])
                pwd = str(data['pwd'])
                assert len(url) > 0
                assert len(model) > 0
                assert len(user) > 0
                assert len(pwd) > 0
        except BaseException as ex:
            raise XExc(str(ex), 400) from ex

        async with await app.ctx.db0.conn() as conn:
            async with conn.cursor() as cur:
                await cur.execute("insert into tianrui_server_db.s_issueorder(device_uuid, msg, create_time) values(%s,%s,%s)", [client_id, json.dumps(data), time.time()])

        app.ctx.mqtt.pushMsg(data, client_id)

        access_logger.info(f'[send msg {client_id}]')

        return JSONS(**{"code": 0})


class alarmArea(HTTPMethodView):
    async def post(self, request):

        """
        上传警告区域
        request:
        {
            "name": "封控",
            "st_time": 1648403637,
            "et_time": 1648953637,
            "rule": "113.22957258828355,34.8794973362596;113.6431722910932,34.886380812878905"
            "rule_gps": '{"type":"rectangle","southWest":[113.570393,34.817487],"northEast":[113.580405,34.827533]}'
        }

        response:
            {
                "code": 200,
                "status": "success",
                "msg": "成功",
                "data": "",
                "TotalCount": ""
            }

        """

        data = request.json

        try:
            rule = data.get("rule")
            rule_gps = data.get("rule_gps")
            name = data.get("name")
            st_time = data.get("st_time")
            et_time = data.get("et_time")
            atype = data.get("atype")

            rule_dict = json.loads(rule_gps)

            assert rule_dict["type"] in ["rectangle", "circle", "polygon"]

            assert name
            assert st_time
            assert et_time
            assert atype in [1, 2, 3]
        except BaseException as ex:
            raise XExc(str(ex), 400) from ex

        ruuid = uuid4().hex

        async with await app.ctx.db0.conn() as conn:
            async with conn.cursor() as cur:
                insert_info = [name, ruuid, rule, rule_gps, st_time, et_time, atype, time.time(), time.time()]
                await cur.execute("insert into tianrui_server_db.s_alarm(name, ruuid, rule, rule_gps,st_time, et_time, atype, create_time, update_time) values(%s,%s,%s,%s,%s,%s,%s,%s,%s)", insert_info)

        pathruletype = {"circle": "1", "rectangle": "2", "polygon": "3"}

        pathtype = pathruletype.get(rule_dict["type"])

        """
        {"type":"rectangle","southWest":[113.570393,34.817487],"northEast":[113.580405,34.827533]}
        {"type":"circle","radius":"1077.325","path":[113.537528,34.846854]}
        {"type":"polygon","path":[[113.532113,34.84361],[113.542728,34.844597]]}
        "事件类型;速度;ruuid;pahttype:;radius:;st:;et:;;path:113.565653,34.820984;113.58024,34.831342;113.58024,34.831342;113.58024,34.831342;"
        """

        info = ""
        if pathtype == "1":

            path = str(rule_dict['path'][0]) + "," + str(rule_dict['path'][1])
            # 便于处理，补齐12位
            radius = str(rule_dict['radius']) + "0" * (12-len(str(rule_dict['radius'])))

            info = "2;;{};pahttype:1;radius:{};st:{};et:{};pt:1;path:{};".format(ruuid, radius, st_time, et_time, path)
        elif pathtype == "2":
            southWest = str(rule_dict.get("southWest")[0]) + "," + str(rule_dict.get("southWest")[1])
            northEast = str(rule_dict.get("northEast")[0]) + "," + str(rule_dict.get("northEast")[1])
            path = southWest + ";" + northEast
            info = "2;;{};pahttype:2;radius:;st:{};et:{};pt:2;path:{};".format(ruuid, st_time, et_time, path)

        elif pathtype == "3":
            path = ";".join([str(i[0]) + "," + str(i[1]) for i in rule_dict["path"]])
            info = "2;;{};pahttype:3;radius:;st:{};et:{};pt:{};path:{};".format(ruuid, st_time, et_time, len(rule_dict["path"]), path)

        async with await app.ctx.db0.conn() as conn:
            async with conn.cursor() as cur:
                await cur.execute("select device_uuid from tianrui_server_db.s_device where status=1")

                ret = await cur.fetchall()

        client_ids = [str(_["device_uuid"]) for _ in ret]

        _uuid = uuid4().hex

        _msg = {
            "type": "SET",
            "stype": "2",
            "operate": "insert",
            "info": info,
            "token": _uuid,
            "UUID": _uuid,
            "MD5": "f105fb9d8b2e9d49c96e7f573284ed17"
        }

        if info:
            for client_id in client_ids:
                print("client_id, send_msg ====>  ", client_id, _msg)
                app.ctx.mqtt.pushMsg(_msg, client_id)

        return JSONS(**{"code": 0})

    async def get(self, request):

        """
        获取警告区域

        req:
            aid int 告警区域id, 获取指定的告警区域时需要，不传获取所有的

        resp:
            {
                "code": 200,
                "status": "success",
                "msg": "成功",
                "data": [
                    {
                        "aid": 2,
                        "name": "封控",
                        "rule": "113.22957258828355,34.8794973362596;113.6431722910932,34.886380812878905;113.63770192042635,34.74898612330245;113.34067031629503,34.67992255537278;113.49051181074631,34.799544927138726;113.4905089026631,34.82657658512676;113.4905089026631,34.82657658512676;113.4106358121304,34.82753347959015;113.45329347033143,34.852370463930136",
                        "st_time": 1648403637,
                        "et_time": 1648953637,
                        "create_time": 1648456334
                    }
                ],
                "TotalCount": ""
            }


        """

        data = request.args
        aid = data.get("aid")

        async with await app.ctx.db0.conn() as conn:
            async with conn.cursor() as cur:
                if aid:
                    await cur.execute("select aid, name, rule, st_time, et_time, atype, create_time from tianrui_server_db.s_alarm where aid=%s", [aid])
                else:
                    await cur.execute("select aid, name, rule, st_time, et_time, atype, create_time from tianrui_server_db.s_alarm")

                _ret = await cur.fetchall()

        for index, info in enumerate(_ret):
            _ret[index]["st_time"] = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(info.get("st_time", 0)))
            _ret[index]["et_time"] = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(info.get("et_time", 0)))
            _ret[index]["create_time"] = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(info.get("create_time", 0)))

        return JSONS(**{"code": 0, "data": list(_ret)})

    async def delete(self, request):

        """
        删除警告区域
        req:
            aid int 删除告警区域id
        """

        data = request.args

        try:
            aid = data.get("aid")
            assert aid
        except BaseException as ex:
            raise XExc(str(ex), 400) from ex

        async with await app.ctx.db0.conn() as conn:
            async with conn.cursor() as cur:
                await cur.execute("delete from tianrui_server_db.s_alarm where aid=%s", aid)

        ruuid = uuid4().hex

        path_zhengzhou = [["0.0","0.0"],["0.0","0.0"],["0.0","0.0"],["0.0","0.0"],["0.0","0.0"],["0.0","0.0"],["0.0","0.0"],["0.0","0.0"]]

        path = ";".join([str(i[0]) + "," + str(i[1]) for i in path_zhengzhou])

        info = "2;;{};pahttype:3;radius:;st:0;et:0;pt:8;path:{};".format(ruuid, path)

        async with await app.ctx.db0.conn() as conn:
            async with conn.cursor() as cur:
                await cur.execute("select device_uuid from tianrui_server_db.s_device where status=1")
                ret = await cur.fetchall()

        client_ids = [str(_["device_uuid"]) for _ in ret]

        _uuid = uuid4().hex

        _msg = {
            "type": "SET",
            "stype": "2",
            "operate": "insert",
            "info": info,
            "token": _uuid,
            "UUID": _uuid,
            "MD5": "f105fb9d8b2e9d49c96e7f573284ed17"
        }

        if info:
            for client_id in client_ids:
                print("client_id, send_msg ====>  ", client_id, _msg)
                app.ctx.mqtt.pushMsg(_msg, client_id)

        return JSONS(**{"code": 0})


class TraceView(HTTPMethodView):
    async def get(self, request):

        """
        根据车辆信息，时间查询轨迹
        request params:
            car_code string 必须 车牌号
            st_time  int 必须 查询轨迹开始时间
            et_time  int 必须 查询轨迹结束时间

        response:
            {
                "code": 200,
                "status": "success",
                "msg": "成功",
                "data": [
                    {
                        "gid": 1,
                        "device_uuid": "2",
                        "lng": 113.563872,
                        "lat": 34.82415,
                        "create_time": 1648436420,
                        "altitude": -1,
                        "car_code": "豫K09T10"
                    },
                    {
                        "gid": 2,
                        "device_uuid": "2",
                        "lng": 113.563942,
                        "lat": 34.82341,
                        "create_time": 1648436439,
                        "altitude": -1,
                        "car_code": "豫K09T10"
                    }

                ],
                "total_count": 2
            }

        """

        data = request.args

        try:
            car_code = data.get("car_code")
            st_time = data.get("st_time")
            et_time = data.get("et_time")

            et_time = int(et_time)

            assert car_code
            assert st_time
            assert et_time
        except BaseException as ex:
            raise XExc(str(ex), 400) from ex

        async with await app.ctx.db0.conn() as conn:
            async with conn.cursor() as cur:
                await cur.execute("select car_code, device_uuid from tianrui_server_db.s_device where car_code = %s", [car_code])
                car_devices = await cur.fetchone()

                print("car_devices  ", car_devices)

        if car_devices is None:
            raise XExc("", 403)

        trace_info = []
        async with await app.ctx.db0.conn() as conn:
            async with conn.cursor() as cur:
                await cur.execute("select * from tianrui_server_db.gps_info where device_uuid = %s and create_time between %s and %s order by create_time asc", [car_devices.get("device_uuid"), st_time, et_time])
                trace_info = await cur.fetchall()

        for index, info in enumerate(trace_info):
            trace_info[index]["car_code"] = car_code
            # trace_info[index].pop("device_uuid")

        return JSONS(**{"code": 0, "data": trace_info, "total_count": len(trace_info)})


class AlarmEventView(HTTPMethodView):
    async def get(self, request):

        """
        告警事件展示
        request params:
            page  int 非必须 哪一页
            page_size  int 非必须 每一页数量

        response:

        {
            "code": 200,
            "status": "success",
            "msg": "成功",
            "data": [
                {
                    "eid": 2,
                    "device_uuid": "2",
                    "etype": 2,  # 事件类型。0 未知 1 超速 2 驶出限行区域
                    "ruuid": 1,
                    "aname": "长椿路电子围栏",
                    "speed": 95,
                    "create_time": "2022-03-28 15:47:17",
                    "driver": "万盛",
                    "car_code": "豫K09T10",
                    "limited_speed": 60,
                    "event_name": "进入限行区域"
                },
                {
                    "eid": 1,
                    "device_uuid": "2",          # 设备uuid
                    "etype": 1,                  # 事件类型。0 未知 1 超速 2 驶出限行区域
                    "ruuid": 0,                    # 告警区域id， 超速了类型没有值, 默认0
                    "aname": "",                 # 告警区域名称， 超速了类型没有值
                    "speed": 95,                 # 车速
                    "create_time": "2022-03-28 15:47:17",  # 事件事件
                    "driver": "万盛",            # 司机
                    "car_code": "豫K09T10",      # 车牌
                    "limited_speed": 60,         # 限速多少
                    "event_name": "超速"         # 事件名称
                }
            ],
            "total_count": 2
        }

        """

        data = request.args

        try:
            page = int(data.get("page", 0))
            page_size = int(data.get("page_size", 10))
        except BaseException as ex:
            raise XExc(str(ex), 400) from ex

        async with await app.ctx.db0.conn() as conn:
            async with conn.cursor() as cur:
                await cur.execute("select * from tianrui_server_db.s_alarm_event order by create_time desc limit %s, %s", [page * page_size, page_size])
                events = await cur.fetchall()

        async with await app.ctx.db0.conn() as conn:
            async with conn.cursor() as cur:
                await cur.execute("select count(1) as count from tianrui_server_db.s_alarm_event")
                events_count = await cur.fetchone()

        count = events_count.get("count", 0)

        if events is None:
            raise XExc("", 403)

        for index, info in enumerate(events):
            if info["etype"] == 1:
                events[index]["event_name"] = "超速"
            elif info["etype"] == 2:
                events[index]["event_name"] = "驶出限行区域"
                # events[index]["aname"] = ruuid_map.get(info.get("ruuid"), "")
            elif info["etype"] == 3:
                events[index]["event_name"] = "进入限行区域"
                # events[index]["aname"] = ruuid_map.get(info.get("ruuid"), "")
            elif info["etype"] == 5:
                events[index]["event_name"] = "疲劳驾驶"
            else:
                events[index]["event_name"] = "-"

            info["create_time"] = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(info.get("create_time", 0)))

        return JSONS(**{"code": 0, "data": events, "total_count": count})


class BoxMessage(HTTPMethodView):

    async def post(self, request):

        """
        盒子返回消息
        {'client_id': '45002131809795', 'UUID': 'E72B22522FB9DDBD7F9EC89B72FFCCCF',
        'msg': '{"event_uuid": "d0c67a907deb47bd8f1cfaca8a2d2337"}',
        'event_data': '{"Time": "2022-03-16_09:41:30.632",
        "results": [{"name": "??", "score": 0.9977266192436218, "x1": 346, "x2": 441, "y1": 35, "y2": 254}], "type": "face"}'}
        """

        data = request.json

        try:

            page = data.get("page", 0)
            page_size = data.get("page", 10)

            _from = page * page_size

            print(page, page_size)
        except BaseException as ex:
            raise XExc(str(ex), 400) from ex

        _ret = []
        async with await app.ctx.db0.conn() as conn:
            async with conn.cursor() as cur:
                # await cur.execute("select * from tianrui_server_db.s_event where id > %s order by create_time desc limit %s", [_from, page_size])
                await cur.execute("select * from tianrui_server_db.s_event order by create_time desc limit 1000 ")
                _ret = await cur.fetchall()
                print('BoxMessage...', len(_ret))

        for index, info in enumerate(_ret):
            info["create_time"] = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(info.get("create_time", 0)))
            _ret[index] = info

        return JSONS(**{"data": _ret})


class MQTT():
    def __init__(self) -> None:
        self.client_id = str(uuid.getnode())
        self.host = MQTT_CONFIG["host"]
        self.port = MQTT_CONFIG["port"]
        self.user = MQTT_CONFIG["user"]
        self.pwd = MQTT_CONFIG["password"]
        self.base_topic = "tianrui/"
        self.client = None
        self.will_set_topic = self.base_topic + 'client/share/'
        self.subscribe_topic = [(self.base_topic + "client/#", 0)]
        # self.publish_topic = [("public/", 0), ("public/" + self.client_id + '/', 0)]
        self.conn = pymysql.connect(**DB_CONFIG['tianrui_server_db'], autocommit=True,
                                    charset="utf8mb4", connect_timeout=10)
        self.client_ids = self.valid_clients()
        self.devices_info = self.get_devices_info()
        self.device_update_time = {}

        print("init", self.host, self.port, self.user, self.pwd)


    def valid_clients(self):
        with self.conn.cursor() as cur:
            cur.execute(
                "select device_uuid,update_time from tianrui_server_db.s_device")
            data = cur.fetchall()
            self.client_ids = [c[0] for c in data]
            self.device_update_time = {c[0]: c[1] for c in data}
            return self.client_ids

    def get_devices_info(self):
        # app.ctx.mqtt.devices_info 设置，在 mqtt 接收message时使用
        with self.conn.cursor() as cur:
            cur.execute("select device_uuid, car_code, driver, limited_speed from tianrui_server_db.s_device")
            devices_list = cur.fetchall()
            return {i[0]: {"car_code": i[1], "driver": i[2], "limited_speed": i[3]} for i in devices_list}


    def start(self):
        self.client = mq_client.Client(client_id=self.client_id, clean_session=True)
        msg = {"client_id": self.client_id, "msg": "disconnected 1"}
        self.client.will_set(self.will_set_topic, json.dumps(msg, ensure_ascii=False, cls=DateEncoder))
        self.client.on_connect = self.on_connect
        self.client.on_message = self.on_message
        self.client.on_disconnect = self.on_disconnect
        self.client.username_pw_set(self.user, self.pwd)

        print(self.host, self.port)

        self.client.connect_async(self.host, self.port)
        self.client.loop_start()
        # self.client.loop_forever()

    def stop(self):
        self.client.loop_stop()
        self.client.disconnect()

    def on_connect(self, client: mq_client.Client, userdata, flags, rc):
        if int(rc) == 0:
            try:
                client.subscribe(self.subscribe_topic)
                client.subscribe(self.will_set_topic)

                msg = {"client_id": self.client_id, "msg": "connected"}
                client.publish(self.will_set_topic, json.dumps(msg, ensure_ascii=False, cls=DateEncoder))
            except BaseException as ex:
                error_logger.info(f'[MQTT订阅失败 {str(ex)}]')
        else:
            error_logger.info(f'[MQTT连接失败 {str(rc)} {self.__dict__}]')

    def on_disconnect(self, client: mq_client.Client, userdata, rc):
        try:
            msg = {"client_id": self.client_id, "msg": "disconnected 0"}
            client.publish(self.will_set_topic, json.dumps(msg, ensure_ascii=False, cls=DateEncoder))
        except BaseException as ex:
            error_logger.info(f'[MQTT断开失败 {str(ex)}]')

    def on_message(self, client: mq_client.Client, userdata, msg: mq_client.MQTTMessage):

        """
        msg:
        {'client_id': '45002131809726',
        'UUID': '57cbb8fd78634509b7db9c73f7494f7a',
        'msg': '{"event_uuid": "57cbb8fd78634509b7db9c73f7494f7a", "etype": 0, "msgtype": "location_report"}',
        'event_data': '{"gps": "", "state": "0;0;2;1649304337"}'}

        """
        _o_msg = "{}"
        try:
            _o_msg = msg.payload.decode('utf-8')

            _msg = json.loads(_o_msg)

            client_id = _msg.get("client_id", "")
            UUID = _msg.get("UUID", "")
            msg_data = _msg.get("msg", "")
            event_data = _msg.get("event_data", "")

            if client_id not in self.client_ids:
                return

            access_logger.info(f'[MQTT订阅消息 {_o_msg}]')

            if "connected" in _msg.get("msg"):
                with self.conn.cursor() as cur:
                    cur.execute(
                        "update tianrui_server_db.s_device set status=1, connet_update_time=%s where device_uuid=%s",
                        [time.time(), client_id])
                    print('-----connected')

            if "disconnected" in _msg.get("msg"):
                with self.conn.cursor() as cur:
                    cur.execute(
                        "update tianrui_server_db.s_device set status=0, connet_update_time=%s where device_uuid=%s",
                        [time.time(), client_id])
                    print('-----disconnected')

            if msg_data != "":
                try:
                    event_data_dict = json.loads(event_data)
                except:
                    pass
                else:

                    device = self.devices_info.get(client_id, {})
                    limited_speed, car_code, driver = device.get("limited_speed", 0), device.get("car_code", ""),device.get("driver", "")

                    gps = event_data_dict.get("gps")
                    if gps:
                        lng, lat, speed, time_int = gps.split(";")
                        lng = Decimal(lng)
                        lat = Decimal(lat)
                        time_int = time_int if time_int else 0
                        time_int = int(time_int)

                        with self.conn.cursor() as cur:
                            cur.execute("insert into tianrui_server_db.gps_info(device_uuid,lng,lat,speed,create_time) values(%s,%s,%s,%s,%s)", [client_id, lng, lat, speed,time_int])

                            if any([self.device_update_time.get(client_id) and self.device_update_time.get(client_id) > time_int, not self.device_update_time.get(client_id)]):
                                cur.execute("update tianrui_server_db.s_device set lng=%s, lat=%s, speed=%s,update_time=%s where device_uuid=%s", [lng, lat, speed,time_int, client_id])
                                self.device_update_time.update({client_id: time_int})

                    state = event_data_dict.get("state")
                    aname = ""
                    if state:
                        """ {"gps": "", "state": "0;1;0;1648975752"} """
                        etype, speed, ruuid, time_int = state.split(";")
                        if etype in ["2", "3"]:
                            with self.conn.cursor() as cur:
                                cur.execute("select name from tianrui_server_db.s_alarm where ruuid=%s", ruuid)
                                aname = cur.fetchone()

                        with self.conn.cursor() as cur:
                            cur.execute("insert into tianrui_server_db.s_alarm_event(device_uuid, etype,ruuid, speed,limited_speed, car_code, driver, aname,create_time) values(%s,%s,%s,%s,%s,%s,%s,%s,%s)",
                                [client_id, etype, ruuid, speed, limited_speed, car_code, driver, aname, time_int])

                    tire = event_data_dict.get("tire")
                    if tire:
                        """ {"gps": "", "state": "","tire":"5;10800;1648975752"} """
                        etype, tire_time, time_int = tire.split(";")

                        with self.conn.cursor() as cur:
                            cur.execute(
                                "insert into tianrui_server_db.s_alarm_event(device_uuid, etype,ruuid, speed,limited_speed, car_code, driver, create_time) values(%s,%s,%s,%s,%s,%s,%s,%s)",
                                [client_id, etype, "0", 0, 0, car_code, driver, time_int])

                    # 数据上报更新状态， GPS信息在gps处上报
                    try:
                        msg_data_info = json.loads(msg_data)
                    except:
                        pass
                    else:
                        if isinstance(msg_data_info, dict):
                            location_report = msg_data_info.get("msgtype")
                            if location_report == "location_report":
                                with self.conn.cursor() as cur:
                                    cur.execute("update tianrui_server_db.s_device set location_report=1 where device_uuid=%s", [client_id])

            with self.conn.cursor() as cur:
                cur.execute("insert into tianrui_server_db.s_event(device_uuid,UUID,msg,event_data,create_time) values(%s,%s,%s,%s, %s)",
                                      [client_id, UUID, msg_data, event_data, time.time()])
        except pymysql.err.InterfaceError as ex:
            error_logger.info(f'[MQTT订阅消息解析失败: 数据库连接问题 {traceback.format_exc()}]')

            with open("msgs.txt", "a") as f:
                f.write(_o_msg)
                f.write("\n")

            self.conn.ping()

        except BaseException as ex:
            error_logger.info(f'[MQTT订阅消息解析失败 {traceback.format_exc()}]')

    def pushMsg(self, msg: dict, client_id):

        '''
            {
                "type": "Download",
                "model": "FTP",
                "url": "ftp://172.19.80.1:21/aaa/data.zip",
                "user": "admin",
                "pwd": "123456",
                "token": "ea0b468e991ac6a21ccccfa6ab586b67",
                "UUID": "F5BB0C8DE146C67B44BABBF4E6584CC0",
                "MD5": "0a48a8ad93bcaee27ac5ad61f98b3566"
            }


            {
                "type": "CMD",
                "commond": "curl https://www.baidu.com -o baidu.html",
                "UUID": "F5BB0C8DE146C67B44BABBF4E6584CC0",
                "MD5": "43836e8b6d170c0961dccd683325f688"
            }

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
                "type": "SET",
                "stype": 1,
                "info": "30",
                "token": "ea0b468e991ac6a21ccccfa6ab586b67",
                "UUID": "E72B22522FB9DDBD7F9EC89B72FFCCCF",
                "MD5": "f105fb9d8b2e9d49c96e7f573284ed17"
            }

            {
                "type": "SET",
                "stype": 2,
                "info": "3,st_time,et_time,[[113.4964,34.878043],[113.429452,34.858606],[113.507043,34.855507]]",
                "token": "ea0b468e991ac6a21ccccfa6ab586b67",
                "UUID": "E72B22522FB9DDBD7F9EC89B72FFCCCF",
                "MD5": "f105fb9d8b2e9d49c96e7f573284ed17"
            }

        '''


        _type = msg.get("type")

        data = ""
        if _type == 'CMD':
            data = _type + msg['commond'] + msg['UUID']
        elif _type == 'Download':
            data = _type + msg['model'] + msg['url'] + msg['user'] + msg['pwd'] + msg['token'] + msg['UUID']
        elif _type == 'Upload':
            data = _type + msg['model'] + msg['url'] + msg['user'] + msg['pwd'] + msg['token'] + msg['UUID']
        elif _type == "SET":
            data = msg["type"] + msg['stype'] + msg['info'] + msg['UUID']

        _md5 = hashlib.md5(data.encode(encoding='UTF-8')).hexdigest()

        msg.update({"MD5": _md5})

        topic = self.base_topic + 'public/' + client_id + '/'

        print("send...", topic, msg)

        self.client.publish(topic, json.dumps(msg, ensure_ascii=False, cls=DateEncoder))



class SysInit():
    async def init(self, *args) -> None:
        async with await app.ctx.db1.conn() as conn:
            async with conn.cursor() as cur:
                await cur.execute("SELECT * from vmq_auth_acl where client_id = %s", [app.ctx.mqtt.client_id])
                if cur.rowcount == 0:

                    sql = """INSERT INTO vmq_auth_acl (mountpoint, client_id, username, password, publish_acl, subscribe_acl) VALUES ('', %s, 'admin', PASSWORD(%s), '[{"pattern":"tianrui/public/#"},{"pattern":"tianrui/client/#"}]', '[{"pattern":"tianrui/client/#"}]');"""

                    print(sql)

                    await cur.execute(
                        sql,
                        [app.ctx.mqtt.client_id,hashlib.md5(str(app.ctx.mqtt.client_id).encode()).hexdigest()])

                    await cur.execute("SELECT * from vmq_auth_acl where client_id = %s", [app.ctx.mqtt.client_id])
                res = await cur.fetchall()
                app.ctx.mqtt.user = res[0]['username']
                app.ctx.mqtt.pwd = hashlib.md5(str(app.ctx.mqtt.client_id).encode()).hexdigest()

        async with await app.ctx.db0.conn() as conn:
            async with conn.cursor() as cur:
                sql_str = "select * from tianrui_server_db.s_config where c_key = %s"
                await cur.execute(sql_str, ['mqtt'])
                if cur.rowcount != 0:
                    res = await cur.fetchall()
                    app.ctx.mqtt.host = json.loads(res[0]['c_value'])['host']
                    app.ctx.mqtt.port = json.loads(res[0]['c_value'])['port']
                app.ctx.mqtt.start()


# 初始化
class Setup:
    def __init__(self) -> None:
        app.config.FALLBACK_ERROR_FORMAT = "json"
        app.error_handler = CustomErrorHandler()
        self.setup_db()
        self.setup_route()
        self.setup_utils()

    def setup_db(self):

        app.ctx.db0 = DBManager(DB_CONFIG['tianrui_server_db'])
        app.ctx.db1 = DBManager(DB_CONFIG['vernemq_db'])

    def setup_utils(self):
        app.ctx.mqtt = MQTT()
        app.ctx.train_info = {'start_time': '', 'commond': '', 'log': '', 'type': '', 'status': False}

    def setup_route(self):
        # 静态资源
        HTML_DIR = os.path.join(APP_DIR, 'html/')
        app.static("/", HTML_DIR + "/index.html", name='index')
        app.static("/", HTML_DIR, name='static')
        api_bp = Blueprint("api", url_prefix="/api")
        # API路由
        api_bp.add_route(Devices.as_view(), "Devices")
        api_bp.add_route(BoxMessage.as_view(), "BoxMessage")
        api_bp.add_route(UpdatePass.as_view(), "UpdatePass")
        api_bp.add_route(IssueOrder.as_view(), "IssueOrder")

        api_bp.add_route(alarmArea.as_view(), "alarmArea")
        api_bp.add_route(TraceView.as_view(), "TraceView")
        api_bp.add_route(AlarmEventView.as_view(), "AlarmEventView")

        # 实时位置上报
        api_bp.add_route(LocationReport.as_view(), "LocationReport")

        ##################################################
        # 视频播报
        api_bp.add_route(VideoPlay.as_view(), "VideoPlay")
        api_bp.add_route(DevicesV2.as_view(), "DevicesV2")


        ##################################################
        # 室内 蓝牙信标
        api_bp.add_route(Xinbiao.as_view(), "Xinbiao")
        api_bp.add_route(Gongka.as_view(), "Gongka")


        ##################################################

        # api_bp.middleware(self.login, attach_to="request")
        api_bp.middleware(self.req, attach_to="request")
        api_bp.middleware(self.resp, attach_to="response")
        app.blueprint(api_bp)

        base_bp = Blueprint("base", url_prefix="/api")
        base_bp.add_route(Login.as_view(), "Login")
        base_bp.add_route(Logout.as_view(), "Logout")

        api_bp.middleware(self.req, attach_to="request")
        api_bp.middleware(self.resp, attach_to="response")
        app.blueprint(base_bp)

    async def login(self, request: Optional[request.Request]):
        try:
            isLogin = request.ctx.session['isLogin']
            assert isLogin
        except BaseException as ex:
            raise XExc('', 600)

    async def req(self, request: Optional[request.Request]):
        if request.method == 'POST':
            try:
                assert isinstance(request.load_json(), Dict)
            except BaseException as ex:
                raise XExc(str(ex), 400) from ex

    async def resp(self, request: Optional[request.Request], response: Optional[response.HTTPResponse]):
        pass


if __name__ == "__main__":
    """启动数据库预设
    /home/server/bin/python3 /home/server/app/app.py -h 192.168.1.1 -p 3306 -u root -P 123456
    """
    opts, args = getopt.getopt(sys.argv[1:], "h:p:u:p", ["host=", "port=", "user=", "password="])
    error_logger.info(f'[启动 {sys.argv}]')
    for opt, arg in opts:
        if opt in ("-h", "--host"):
            DB_CONFIG['tianrui_server_db']['host'] = str(arg)
            DB_CONFIG['vernemq_db']['host'] = str(arg)
        if opt in ("-p", "--port"):
            DB_CONFIG['tianrui_server_db']['port'] = int(arg)
            DB_CONFIG['vernemq_db']['port'] = int(arg)
        if opt in ("-u", "--user"):
            DB_CONFIG['tianrui_server_db']['user'] = str(arg)
            DB_CONFIG['vernemq_db']['user'] = str(arg)
        if opt in ("-P", "--password"):
            DB_CONFIG['tianrui_server_db']['password'] = str(arg)
            DB_CONFIG['vernemq_db']['password'] = str(arg)
    Setup()
    # app.register_listener(SysInit().init, "after_server_start")
    # app.add_task((task_set_device))
    app.run(host="0.0.0.0", port=65404)