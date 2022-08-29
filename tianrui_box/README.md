### 使用说明
> 一般使用说明
 - 开机自启
 - 访问 `http://127.0.0.1:8080`, 默认账号 `admin`, 初始密码 `123456`
 - 访问 `http://127.0.0.1:8080/api.html` 查看 API 接口文档
 - 服务端数据库 采用 `MariaDB 10.2`, 默认用户 `root`, 密码 `123456`, 端口 `3306`, 库名 `server_db`
 - MQTT 服务器采用 `VerneMQ`, 默认 `tcp` 端口 `1883`, 健康检查端口 `8888` ( http://IP:8888/status ), 连接鉴权采用数据库校验模式
   - 鉴权服务器数据库采用 `MariaDB 10.2+`, 库名 `vernemq_db`

> 数据库设计 (库名 : `server_db`)
* `s_admin` Web后台管理员表
  | 字段 | 类型 | 描述 | 默认值 | 可空 | 唯一 | 备注 |
  | ---- | ---- | ---- | :----: | :----: | :----: | ---- |
  | id | int | - | auto_increment | - | √ | - |
  | acc | varchar(191) | 账户 | - | - | √ | - |
  | pwd | varchar(191) | 密码 | - | - | - | - |
  | status | int | 账户状态 | 1 | - | - | 1 可用 0 不可用 |
  | last_login_time | varchar(191) | - | '' | - | - | - |
  | last_login_ip | varchar(191) | - | '' | - | - | - |
  | default_pwd | varchar(191) | 初始化密码 | 'a52b27029bcf5701852a2f4edc640fe1' | - | - | 明文为 123456 |
  | add_time | varchar(191) | - | '' | - | - | - |
  | update_time | varchar(191) | - | '' | - | - | - |
  | del_time | varchar(191) | - | '' | - | - | - |
  |
* `s_config` 配置表
  | 字段 | 类型 | 描述 | 默认值 | 可空 | 唯一 | 备注 |
  | ---- | ---- | ---- | :----: | :----: | :----: | ---- |
  | id | int | - | auto_increment | - | √ | - |
  | c_key | varchar(191) | 配置项KEY | - | - | √ | - |
  | c_value | text | 配置项当前VALUE | '' | - | - | - |
  | create_time | datetime | - | '' | - | - | - |
  | update_time | datetime | - | '' | - | - | - |
  |

> 数据库设计 (库名 : `vernemq_db`)
* `vmq_auth_acl` Web后台管理员表
  | 字段 | 类型 | 描述 | 默认值 | 可空 | 唯一 | 备注 |
  | ---- | ---- | ---- | :----: | :----: | :----: | ---- |
  | mountpoint | varchar(10) | 挂载点 | - | - | - | - |
  | client_id | varchar(128) | 设备唯一id | - | - | √ | - |
  | username | varchar(128) | 用户名 | - | - | - | - |
  | password | varchar(128) | 密码 | - | - | - | - |
  | publish_acl | text | 发布权限 | '' | - | - | - |
  | subscribe_acl | text | 订阅权限 | '' | - | - | - |
  |

### 服务端说明
> 服务
 - 盒子端服务根目录为 `/home/server`
 - 静态文件根目录为 `/home/server/app/html`
 - 框架使用 Sanic 21.6.2, 占用 `8000` `8080` 端口
 - 使用 supervisor 进行管理, 占用 `9001` 端口
   - 管理服务配置文件 /etc/supervisor/supervisord.conf
   - 开启/关闭/重启服务管理服务 systemctl start/stop/restart supervisord
 - 后台服务配置文件 /etc/supervisor/conf.d/server.ini
   - 开启/关闭/重启客户端服务 supervisorctl start/stop/restart server:*
 - 日志路径 /home/server/app/logs/
* 安装部署
  - root 运行 /home/server/app_env/install.sh

### Client端说明(盒子)
> 服务
 - 盒子端服务根目录为 `/home/client`
 - 框架使用 Sanic 21.6.2, 占用 `8001` 和 `8081` 端口
 - 使用 supervisor 进行管理, 占用 `9001` 端口
   - 管理服务配置文件 /etc/supervisor/supervisord.conf
   - 开启/关闭/重启服务管理服务 systemctl start/stop/restart supervisord
 - 后台服务配置文件 /etc/supervisor/conf.d/client.ini
   - 开启/关闭/重启客户端服务 supervisorctl start/stop/restart client:*
 - 日志路径 /home/client/app/logs/
* 安装部署
  - root 运行 /home/client/app_env/install.sh
> 盒子当前更新状态判断逻辑
1. 若 `version` 文件存在并不为空, 获取当前版本号
    - `version` 文件内容示例:
    ```Json
    1.0
    ```
2. 若 `md5` 文件存在并不为空, 获取当前更新文件MD5信息 ( 即 `dev-update.zip` 升级包解压出来的所有文件的MD5信息 )
    - `md5` 文件内容示例:
    ```Json
    {
        "/dev-update-run.sh": "af6d97b15d4cf0b81242b250029197b5",
        "/version": "e4c2e8edac362acab7123654b9e73432",
        "/some_dir/fake.update.file": "0108921e7117a1a8607b21e429fcc7c9",
        "...": "..."
    }
    ```
    - 升级脚本, 必须包含且固定为 `dev-update-run.sh`, 值对应为该文件MD5值
    - 版本文件, 必须包含且名称固定为 `version`, 值对应为该文件MD5值

3. 查询是否存在名称为 `UPDATE` 的进程, 若存在, 返回 `升级中` ( `status` : 2 ) 状态

4. 若不存在名称为 `UPDATE` 的进程, 则遍历 `md5` 文件中的内容, 匹配内容文件和对应文件MD5值
    - 所有匹配成功, 返回 `正常` ( `status` : 1 ) 状态, 运行解压出来的 `dev-update-run.sh` 脚本
    - 匹配失败, 返回 `异常` ( `status` : 0 ) 状态

- 由于校验 `md5` 文件中的 `更新文件` 时, 仅在解压目录下校验, 所以不建议 `dev-update-run.sh` 中运行 `mv`, `cp` 等命令移动 `更新文件`, 建议使用 `ln -sf` 做软连接, 从而保证更新文件校验结果一致性, 例如:
  - ln -sf ./somedir/fake.update.file /some.workdir/destination.file