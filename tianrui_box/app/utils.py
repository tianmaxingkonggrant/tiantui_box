from libs import *

__all__ = ['aQuery2List', 'DateEncoder', 'JSONS', "XExc", "CustomErrorHandler", "DBManager", "FileMD5"]


async def aQuery2List(cursor, querySet):
    result_list = [dict((cursor.description[i][0], value) for i, value in enumerate(row)) for row in querySet]
    return result_list


def FileMD5(file_path):
    with open(file_path, "rb") as f:
        fcont = f.read()
    fmd5 = hashlib.md5(fcont).hexdigest()
    return fmd5


class DBManager():
    def __init__(self, db_config, cursorclass=aiomysql.DictCursor):
        self.config = {
            "host": db_config['host'],
            "port": db_config['port'],
            "user": db_config['user'],
            "password": db_config['password'],
            "db": db_config['db'],
            "autocommit": True,
            "charset": "utf8mb4",
            "connect_timeout": 10,
            "cursorclass": cursorclass,
        }
        self.__pool = None

    async def pool(self):
        if self.__pool == None:
            self.__pool = await aiomysql.create_pool(**self.config)
            if not self.__pool:
                raise ("connect to DB error !!")
        return self.__pool

    async def conn(self):
        pool = await self.pool()
        conn = pool.acquire()
        return conn


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


# 构造JSON
def JSONS(**kwargs):
    """Json 构造体

    :param msg
    :param data
    """

    _res = {
        'code': 200,
        'status': 'success',
    }
    _res['msg'] = kwargs['msg'] if 'msg' in kwargs.keys() else "成功"
    _res['data'] = kwargs['data'] if 'data' in kwargs.keys() else ""
    # _res['data'] = json.dumps(kwargs['data'], ensure_ascii=False, cls=DateEncoder) if 'data' in kwargs.keys() else ""
    _res['total_count'] = kwargs['total_count'] if 'total_count' in kwargs.keys() else ""

    # if isinstance(ctx, bytes):
    # ctx = str(ctx, encoding='utf-8')
    return response.json(_res)


class XExc(SanicException):
    def __init__(self,
                 message: Optional[Union[str, bytes]] = None,
                 status_code: Optional[int] = None,
                 quiet: Optional[bool] = None) -> None:
        super().__init__(message, status_code, quiet)


class CustomErrorHandler(ErrorHandler):
    def default(self, request: request.Request, exception):
        super().default(request, exception)
        _dict = {
            400: "入参错误",
            403: "记录不存在",
            497: "记录唯一性重复",
            498: "记录已存在",
            499: "记录异常",
            500: "未知错误",
            501: "连接失败",
            502: "CMD操作失败",
            503: "SQL操作失败",
            504: "流未开启",
            505: "配置失败",
            506: "状态不可用",
            600: "未登录"
        }
        _res = {}
        _res['status'] = 'error'
        _res['data'] = ''
        _d_data = {}
        _d_data['path'] = ''
        _req = request
        try:
            _d_data['req_body'] = _req.load_json()
        except BaseException as ex:
            _d_data['req_body'] = _req.body.decode()
        _d_data['method'] = _req.method
        _d_data['path'] = _req.path
        _res['code'] = exception.status_code if 'status_code' in exception.__dict__.keys(
        ) and exception.status_code in _dict.keys() else 500
        _res['msg'] = exception.args if len(exception.args) and len(exception.args[0]) else _dict[_res['code']]
        _res['d_code'] = random.randint(100000, 999999)
        json_res = json.dumps(_res, ensure_ascii=False, cls=DateEncoder)
        _tb = traceback.extract_tb(exception.__traceback__)[-1]
        try:
            error_logger.info('[{}] [{}:{}] [{}:{}]\n[SQL:{}] {}\n[REQ:{}] {}\n[RET:{}] {}\n[ARG:{}] {}'.format(_res['d_code'], _d_data['path'], _d_data['method'],
                _tb.filename, _tb.lineno, _res['d_code'],
                request.ctx._last_executed if hasattr( request.ctx, '_last_executed') else '', _res['d_code'],
                _d_data['req_body'], _res['d_code'], json_res, _res['d_code'], exception.args))
        except BaseException as ex:
            print(f'[{datetime.now().strftime("%Y-%m-%d %H:%M:%S:%f")} 日志写入失败 {str(ex)}]')
        return response.json(_res)