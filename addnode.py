#!/usr/bin/python
# -*- coding: UTF-8 -*-

import logging
import time
import sys
import os
import importloader
from configloader import load_config, get_config
import cymysql
import json
import socket
import fcntl
import struct



def get_ip_address(ifname):
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    return socket.inet_ntoa(fcntl.ioctl(
        s.fileno(),
        0x8915,  # SIOCGIFADDR
        struct.pack('256s', ifname[:15])
    )[20:24])


def addnode():
    if get_config().MYSQL_CONFIG:
        config_path = get_config().MYSQL_CONFIG
    else:
        print
        "usermysql.json Not Found"
        return

    with open(config_path, 'r+') as f:
        mysqlcfg = json.loads(f.read().decode('utf8'))
    time.sleep(300)

    while True:

        try:
            serverip=get_ip_address('eth0')

            if mysqlcfg["ssl_enable"] == 1:
                conn = cymysql.connect(host=mysqlcfg["host"], port=mysqlcfg["port"],
                                       user=mysqlcfg["user"], passwd=mysqlcfg["password"],
                                       db=mysqlcfg["db"], charset='utf8',
                                       ssl={'ca': mysqlcfg["ssl_enable"], 'cert': mysqlcfg["ssl_enable"],
                                            'key': mysqlcfg["ssl_enable"]})
            else:
                conn = cymysql.connect(host=mysqlcfg["host"], port=mysqlcfg["port"],
                                       user=mysqlcfg["user"], passwd=mysqlcfg["password"],
                                       db=mysqlcfg["db"], charset='utf8')

            conn.autocommit(True)
            cur = conn.cursor()
            cur.execute(
                "INSERT INTO `ss_node` (`id`, `name`, `type`, `server`, `method`, `protocol`, `obfs`, `custom_method`, `traffic_rate`, `info`, `status`, `offset`, `sort`) VALUES (NULL, '" +serverip + "', 0, '" +serverip + "', 'chacha20', 'auth_sha1_v2_compatible', 'tls1.2_ticket_auth_compatible', 1, 1, NULL, NULL, 0, 9999)")
            cur.close()
            conn.close()

            logging.info("add node finished")
        except BaseException:
            logging.error("add node error")

