CREATE DATABASE IF NOT EXISTS vernemq_db DEFAULT CHARACTER SET utf8mb4 DEFAULT COLLATE utf8mb4_general_ci;
create or replace table vernemq_db.vmq_auth_acl
(
	mountpoint varchar(10) not null,
	client_id varchar(128) not null,
	username varchar(128) not null,
	password varchar(128) null,
	publish_acl text null,
	subscribe_acl text null,
	primary key (mountpoint, client_id, username)
);

CREATE DATABASE IF NOT EXISTS tianrui_server_db DEFAULT CHARACTER SET utf8mb4 DEFAULT COLLATE utf8mb4_general_ci;
create or replace table tianrui_server_db.s_admin (
	id int auto_increment primary key,
	acc varchar(191) not null,
	pwd varchar(191) not null,
	status int default 1 not null,
	last_login_time varchar(191) default '' not null,
	last_login_ip varchar(191) default '' not null,
	default_pwd varchar(191) default 'a52b27029bcf5701852a2f4edc640fe1' null,
	add_time varchar(191) default '' not null,
	update_time varchar(191) default '' not null,
	del_time varchar(191) default '' not null,
	constraint s_admin_acc_uindex unique (acc)
);

insert into tianrui_server_db.s_admin (acc, pwd, status, default_pwd)
values (
		'admin',
		'a52b27029bcf5701852a2f4edc640fe1',
		'1',
		'a52b27029bcf5701852a2f4edc640fe1'
	);

create or replace table tianrui_server_db.s_config
(
    id          int            auto_increment primary key,
    c_key       varchar(191)                         null,
    c_value     text   default ''        not null,
    create_time datetime default current_timestamp() null,
    update_time datetime default current_timestamp() null on update current_timestamp() comment '修改时间',
    constraint s_config_c_key_uindex
        unique (c_key)
);

INSERT INTO tianrui_server_db.s_config (id, c_key, c_value) VALUES (1, 'mqtt', '{"host": "", "port": 1883, "user": "server", "pass": ""}');
INSERT INTO tianrui_server_db.s_config (id, c_key, c_value) VALUES (2, 'ftp', '{"host": "", "port": 21, "user": "proftpd", "pass": "123456"}');
INSERT INTO tianrui_server_db.s_config (id, c_key, c_value) VALUES (3, 'sdk_NVIDIA', '{"sdk_path": "/home/", "ver": "0.0", "cmd": ""}');
INSERT INTO tianrui_server_db.s_config (id, c_key, c_value) VALUES (4, 'sdk_Rockchip', '{"sdk_path": "/home/", "ver": "0.0", "cmd": ""}');
INSERT INTO tianrui_server_db.s_config (id, c_key, c_value) VALUES (5, 'train_NVIDIA', '{"cmd": ""}');
INSERT INTO tianrui_server_db.s_config (id, c_key, c_value) VALUES (6, 'train_Rockchip', '{"cmd": ""}');