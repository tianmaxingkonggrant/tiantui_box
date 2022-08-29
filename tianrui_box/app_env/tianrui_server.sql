# ************************************************************
# Sequel Pro SQL dump
# Version 5446
#
# https://www.sequelpro.com/
# https://github.com/sequelpro/sequelpro
#
# Host: 127.0.0.1 (MySQL 5.5.5-10.4.24-MariaDB)
# Database: tianrui_server_db
# Generation Time: 2022-05-30 09:22:12 +0000
# ************************************************************


/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!40101 SET NAMES utf8 */;
SET NAMES utf8mb4;
/*!40014 SET @OLD_FOREIGN_KEY_CHECKS=@@FOREIGN_KEY_CHECKS, FOREIGN_KEY_CHECKS=0 */;
/*!40101 SET @OLD_SQL_MODE=@@SQL_MODE, SQL_MODE='NO_AUTO_VALUE_ON_ZERO' */;
/*!40111 SET @OLD_SQL_NOTES=@@SQL_NOTES, SQL_NOTES=0 */;


# Dump of table gps_info
# ------------------------------------------------------------

DROP TABLE IF EXISTS `gps_info`;

CREATE TABLE `gps_info` (
  `gid` int(11) unsigned NOT NULL AUTO_INCREMENT,
  `device_uuid` varchar(100) NOT NULL DEFAULT '',
  `lng` decimal(10,7) NOT NULL DEFAULT 0.0000000,
  `lat` decimal(10,7) NOT NULL DEFAULT 0.0000000,
  `speed` float NOT NULL DEFAULT -1,
  `altitude` int(11) NOT NULL DEFAULT -1,
  `create_time` int(11) NOT NULL DEFAULT 0,
  PRIMARY KEY (`gid`),
  KEY `device_uuid` (`device_uuid`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

LOCK TABLES `gps_info` WRITE;
/*!40000 ALTER TABLE `gps_info` DISABLE KEYS */;

INSERT INTO `gps_info` (`gid`, `device_uuid`, `lng`, `lat`, `speed`, `altitude`, `create_time`)
VALUES
	(7,'224624436340742',113.5721700,34.8154033,35,-1,1653898472),
	(8,'224624436340742',113.5721733,34.8154817,35,-1,1653898471),
	(9,'224624436340742',113.5721850,34.8156467,37,-1,1653898469),
	(10,'224624436340742',113.5721900,34.8157317,38,-1,1653898468);

/*!40000 ALTER TABLE `gps_info` ENABLE KEYS */;
UNLOCK TABLES;


# Dump of table s_admin
# ------------------------------------------------------------

DROP TABLE IF EXISTS `s_admin`;

CREATE TABLE `s_admin` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `acc` varchar(191) NOT NULL,
  `pwd` varchar(191) NOT NULL,
  `status` int(11) NOT NULL DEFAULT 1,
  `last_login_time` varchar(191) NOT NULL DEFAULT '',
  `last_login_ip` varchar(191) NOT NULL DEFAULT '',
  `default_pwd` varchar(191) DEFAULT 'a52b27029bcf5701852a2f4edc640fe1',
  `add_time` varchar(191) NOT NULL DEFAULT '',
  `update_time` varchar(191) NOT NULL DEFAULT '',
  `del_time` varchar(191) NOT NULL DEFAULT '',
  PRIMARY KEY (`id`),
  UNIQUE KEY `s_admin_acc_uindex` (`acc`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

LOCK TABLES `s_admin` WRITE;
/*!40000 ALTER TABLE `s_admin` DISABLE KEYS */;

INSERT INTO `s_admin` (`id`, `acc`, `pwd`, `status`, `last_login_time`, `last_login_ip`, `default_pwd`, `add_time`, `update_time`, `del_time`)
VALUES
	(1,'admin','a52b27029bcf5701852a2f4edc640fe1',1,'','','a52b27029bcf5701852a2f4edc640fe1','','','');

/*!40000 ALTER TABLE `s_admin` ENABLE KEYS */;
UNLOCK TABLES;


# Dump of table s_alarm
# ------------------------------------------------------------

DROP TABLE IF EXISTS `s_alarm`;

CREATE TABLE `s_alarm` (
  `aid` int(11) unsigned NOT NULL AUTO_INCREMENT,
  `name` varchar(100) NOT NULL DEFAULT '',
  `ruuid` varchar(64) DEFAULT '',
  `rule` text NOT NULL,
  `st_time` int(11) NOT NULL,
  `et_time` int(11) NOT NULL,
  `create_time` int(11) NOT NULL,
  `update_time` int(11) NOT NULL,
  `atype` int(11) NOT NULL DEFAULT 0 COMMENT '1 圆形 2矩形 3多边形',
  `rule_gps` text NOT NULL,
  PRIMARY KEY (`aid`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

LOCK TABLES `s_alarm` WRITE;
/*!40000 ALTER TABLE `s_alarm` DISABLE KEYS */;

INSERT INTO `s_alarm` (`aid`, `name`, `ruuid`, `rule`, `st_time`, `et_time`, `create_time`, `update_time`, `atype`, `rule_gps`)
VALUES
	(89,'dfa','049b426c181f4830b63112be9c3102f8','{\"type\":\"rectangle\",\"southWest\":[113.563682,34.822876],\"northEast\":[113.56474,34.824571]}',1649865600,1652803200,1649749946,1649749946,2,'{\"type\":\"rectangle\",\"southWest\":[\"113.5575885\",\"34.8239707\"],\"northEast\":[\"113.5586487\",\"34.8256655\"]}'),
	(90,'1233','ec8ec70c22d34b22a345b9cc594373co','{\"type\":\"circle\",\"radius\":\"2219.780\",\"path\":[113.595277,34.891737]}',1649692800,1652284800,1649751400,1649751400,1,'{\"path\":[\"113.5892204\",\"34.8927831\"],\"type\":\"circle\",\"radius\":\"2219.780\"}');

/*!40000 ALTER TABLE `s_alarm` ENABLE KEYS */;
UNLOCK TABLES;


# Dump of table s_alarm_event
# ------------------------------------------------------------

DROP TABLE IF EXISTS `s_alarm_event`;

CREATE TABLE `s_alarm_event` (
  `eid` int(11) unsigned NOT NULL AUTO_INCREMENT COMMENT '告警事件id',
  `device_uuid` varchar(100) NOT NULL DEFAULT '',
  `etype` int(11) NOT NULL DEFAULT 0 COMMENT '0未知1超速2驶入告警区域3驶离告警区域 ',
  `ruuid` varchar(64) DEFAULT NULL COMMENT '告警区域id',
  `aname` varchar(100) NOT NULL DEFAULT '' COMMENT '告警区域名字',
  `limited_speed` int(11) NOT NULL DEFAULT 0,
  `car_code` varchar(32) NOT NULL DEFAULT '',
  `speed` int(11) NOT NULL COMMENT '当前车速',
  `create_time` int(11) NOT NULL,
  `driver` varchar(32) DEFAULT NULL,
  PRIMARY KEY (`eid`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;



# Dump of table s_config
# ------------------------------------------------------------

DROP TABLE IF EXISTS `s_config`;

CREATE TABLE `s_config` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `c_key` varchar(191) DEFAULT NULL,
  `c_value` text NOT NULL DEFAULT '',
  `create_time` datetime DEFAULT current_timestamp(),
  `update_time` datetime DEFAULT current_timestamp() ON UPDATE current_timestamp() COMMENT '修改时间',
  PRIMARY KEY (`id`),
  UNIQUE KEY `s_config_c_key_uindex` (`c_key`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;



# Dump of table s_device
# ------------------------------------------------------------

DROP TABLE IF EXISTS `s_device`;

CREATE TABLE `s_device` (
  `did` int(11) unsigned NOT NULL AUTO_INCREMENT,
  `device_uuid` varchar(100) DEFAULT NULL,
  `location_report` int(11) NOT NULL DEFAULT 1,
  `device_ver` varchar(20) DEFAULT NULL,
  `sys_ver` varchar(20) DEFAULT NULL,
  `device_model` varchar(100) DEFAULT NULL,
  `create_time` int(11) DEFAULT NULL,
  `update_time` int(11) DEFAULT NULL,
  `status` int(11) NOT NULL DEFAULT 0,
  `lng` decimal(10,7) NOT NULL DEFAULT 0.0000000,
  `lat` decimal(10,7) NOT NULL DEFAULT 0.0000000,
  `speed` int(11) NOT NULL DEFAULT -1 COMMENT '时速',
  `car_code` varchar(64) NOT NULL DEFAULT '',
  `driver` varchar(32) NOT NULL DEFAULT '',
  `limited_speed` int(11) NOT NULL,
  `altitude` int(11) NOT NULL DEFAULT -1,
  `ip` varchar(100) NOT NULL DEFAULT '0.0.0.0',
  `cron_time` int(11) NOT NULL DEFAULT 0 COMMENT '定时上报 单位秒',
  `cron_time_result` int(11) NOT NULL DEFAULT 0,
  `cron_distance` int(11) NOT NULL DEFAULT 0 COMMENT '定距离上报 单位米',
  `cron_distance_result` int(11) NOT NULL DEFAULT 0,
  `tire_time` int(11) NOT NULL DEFAULT 10800 COMMENT '疲劳驾驶时间，单位秒： 默认三个小时',
  `flv_url_push` varchar(1000) NOT NULL DEFAULT '' COMMENT 'flv视频推送地址',
  `cam_url` varchar(1000) NOT NULL DEFAULT '' COMMENT '摄像头地址，用户名，密码 rtsp://admin:admin123456@192.168.1.124:554',
  `max_pushed_time` int(11) NOT NULL DEFAULT 180 COMMENT '默认最大推送时间，考虑流量',
  `flv_url` varchar(1000) NOT NULL DEFAULT '' COMMENT 'web页面视频地址',
  PRIMARY KEY (`did`),
  UNIQUE KEY `car_code` (`car_code`),
  UNIQUE KEY `device_uuid` (`device_uuid`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

LOCK TABLES `s_device` WRITE;
/*!40000 ALTER TABLE `s_device` DISABLE KEYS */;

INSERT INTO `s_device` (`did`, `device_uuid`, `location_report`, `device_ver`, `sys_ver`, `device_model`, `create_time`, `update_time`, `status`, `lng`, `lat`, `speed`, `car_code`, `driver`, `limited_speed`, `altitude`, `ip`, `cron_time`, `cron_time_result`, `cron_distance`, `cron_distance_result`, `tire_time`, `flv_url_push`, `cam_url`, `max_pushed_time`, `flv_url`)
VALUES
	(37,'45002131809795',1,'',NULL,NULL,1648711399,1649749902,0,113.5592117,34.8251483,-1,'豫F2356A','肖战1.39',3005,-1,'192.168.1.39',5,1,1000,1,1000,'rtmp://192.168.240.227','rtsp://admin:admin123456@192.168.1.171:554',60,''),
	(42,'45002131809726',1,NULL,NULL,NULL,1648711399,1649749162,0,113.5370550,34.8171310,-1,'豫L8888','万盛1.34',60,-1,'192.168.1.34',0,1,0,1,10800,'rtmp://192.168.240.227','rtsp://admin:admin123456@192.168.1.171:554',60,'http://192.168.240.227:8088'),
	(43,'224624439042706',1,NULL,NULL,NULL,1649211218,1649761845,0,113.7936483,34.8149583,-1,'豫A9999','小李王1.219',70,-1,'0.0.0.219',5,1,1000,1,1000,'rtmp://192.168.240.227:1935','rtsp://admin:admin123456@192.168.1.171:554',60,'http://192.168.240.227:8088'),
	(49,'45002131809777',1,NULL,NULL,NULL,1649644590,1653037266,0,113.6980617,34.7424483,-1,'豫P6666','万盛',10000,-1,'0.0.0.35',1000,0,0,0,10800,'rtmp://192.168.240.227:1935','rtsp://admin:admin123456@192.168.1.171:554',30,'http://192.168.240.227:8088'),
	(51,'224624436340742',1,NULL,NULL,NULL,1653016138,1653898468,1,113.5721900,34.8157317,38,'测试95','测试95',60,-1,'0.0.0.0',10,0,0,0,14400,'rtmp://123.52.43.212:21935','rtsp://admin:admin123456@192.168.1.116:554/cam/realmonitor?channel=1&subtype=1',60,'http://123.52.43.212:28088');

/*!40000 ALTER TABLE `s_device` ENABLE KEYS */;
UNLOCK TABLES;


# Dump of table s_event
# ------------------------------------------------------------

DROP TABLE IF EXISTS `s_event`;

CREATE TABLE `s_event` (
  `id` int(11) unsigned NOT NULL AUTO_INCREMENT,
  `device_uuid` varchar(100) DEFAULT NULL,
  `UUID` varchar(64) DEFAULT NULL,
  `msg` text DEFAULT NULL,
  `event_data` text NOT NULL,
  `create_time` int(11) DEFAULT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

LOCK TABLES `s_event` WRITE;
/*!40000 ALTER TABLE `s_event` DISABLE KEYS */;

INSERT INTO `s_event` (`id`, `device_uuid`, `UUID`, `msg`, `event_data`, `create_time`)
VALUES
	(1,'224624436340742','b6ee5c83b56f45e3be538ff7010551b8','{\"event_uuid\": \"b6ee5c83b56f45e3be538ff7010551b8\", \"etype\": 4}','{\"gps\": \"113.5721600;34.8151650;36;1653898475\", \"state\": \"\"}',1653902468),
	(2,'224624436340742','5605e56d00944d7fbd4bd3e948158a51','{\"event_uuid\": \"5605e56d00944d7fbd4bd3e948158a51\", \"etype\": 4}','{\"gps\": \"113.5721633;34.8152467;35;1653898474\", \"state\": \"\"}',1653902477),
	(3,'224624436340742','9c302013431c42c0bd1133817934fb11','{\"event_uuid\": \"9c302013431c42c0bd1133817934fb11\", \"etype\": 4}','{\"gps\": \"113.5721667;34.8153233;35;1653898473\", \"state\": \"\"}',1653902487),
	(4,'224624436340742','ba72b6cea59f4772a74bf032402b983d','{\"event_uuid\": \"ba72b6cea59f4772a74bf032402b983d\", \"etype\": 4}','{\"gps\": \"113.5721700;34.8154033;35;1653898472\", \"state\": \"\"}',1653902496),
	(5,'224624436340742','c56a9bf97c794a8fa6cbee0070e953c8','{\"event_uuid\": \"c56a9bf97c794a8fa6cbee0070e953c8\", \"etype\": 4}','{\"gps\": \"113.5721733;34.8154817;35;1653898471\", \"state\": \"\"}',1653902506),
	(6,'224624436340742','7ecb1bafdd18448eaba22b0d015a259e','{\"event_uuid\": \"7ecb1bafdd18448eaba22b0d015a259e\", \"etype\": 4}','{\"gps\": \"113.5721850;34.8156467;37;1653898469\", \"state\": \"\"}',1653902515),
	(7,'224624436340742','5efa488b5fa74e27a73944e16aa9b279','{\"event_uuid\": \"5efa488b5fa74e27a73944e16aa9b279\", \"etype\": 4}','{\"gps\": \"113.5721900;34.8157317;38;1653898468\", \"state\": \"\"}',1653902525);

/*!40000 ALTER TABLE `s_event` ENABLE KEYS */;
UNLOCK TABLES;


# Dump of table s_issueorder
# ------------------------------------------------------------

DROP TABLE IF EXISTS `s_issueorder`;

CREATE TABLE `s_issueorder` (
  `id` int(11) unsigned NOT NULL AUTO_INCREMENT,
  `device_uuid` varchar(100) NOT NULL DEFAULT '',
  `msg` text DEFAULT NULL,
  `create_time` int(11) NOT NULL DEFAULT 0,
  `status` int(11) NOT NULL DEFAULT 0,
  `reason` text DEFAULT NULL,
  `UUID` varchar(64) NOT NULL DEFAULT '',
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;




/*!40111 SET SQL_NOTES=@OLD_SQL_NOTES */;
/*!40101 SET SQL_MODE=@OLD_SQL_MODE */;
/*!40014 SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS */;
/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
