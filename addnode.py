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
        print "usermysql.json Not Found"
        return

    with open(config_path, 'r+') as f:
        mysqlcfg = json.loads(f.read().decode('utf8'))
    #time.sleep(300)


    serverip = get_ip_address('eth0')
    print serverip

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
    query_sql= "SELECT * FROM ss_node WHERE server= '" + serverip + "'"
    #print query_sql
    cur.execute(query_sql)
    if cur.fetchone():
        print "该节点已存在"
        return
    else:
        sql = "INSERT INTO ss_node (name, type, server,custom_method, traffic_rate, info, status, offset, sort) VALUES ('" + serverip + "', 0, '" + serverip + "',1,1, '', '', 0,99)"
        print sql
        try:
            # time.sleep(200)
            # cur.execute(sql)
            conn.close()

            logging.info("add node finished")
        except BaseException:
            logging.error("add node error")
        return
addnode()
