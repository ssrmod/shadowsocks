#!/usr/bin/python
# -*- coding: UTF-8 -*-

import logging
import time
import sys
import os
import importloader
from speedtest import speedtest_cli
from configloader import load_config, get_config
import cymysql
import json


def speedtest_thread():
	hour = get_config().SPEEDTEST
	if hour == 0:
		return
	if get_config().MYSQL_CONFIG:
		config_path = get_config().MYSQL_CONFIG
	else:
		print "usermysql.json Not Found"
		return

	with open(config_path, 'r+') as f:
		mysqlcfg = json.loads(f.read().decode('utf8'))

	time.sleep(120)

	while True:

		try:
			config = speedtest_cli.getConfig()

			CTid = 0
			servers = speedtest_cli.closestServers(config['client'], True)
			for server in servers:
				if server['country'].find('China') != -1 and server['sponsor'].find('Telecom') != -1:
					CTid = server['id']
			CTNode = speedtest_cli.getBestServer(filter(lambda x: x['id'] == CTid,
														servers))
			CTPing = str(round(CTNode['latency'], 2)) + ' ms'
			sizes = [350, 500, 750, 1000, 1500, 2000, 2500, 3000, 3500, 4000]
			urls = []
			for size in sizes:
				for i in range(0, 4):
					urls.append('%s/random%sx%s.jpg' %
								(os.path.dirname(CTNode['url']), size, size))
			dlspeed = speedtest_cli.downloadSpeed(urls, True)
			CTDLSpeed = str(round((dlspeed / 1000 / 1000) * 8, 2)) + " Mbit/s"

			sizesizes = [int(.25 * 1000 * 1000), int(.5 * 1000 * 1000)]
			sizes = []
			for size in sizesizes:
				for i in range(0, 25):
					sizes.append(size)
			ulspeed = speedtest_cli.uploadSpeed(CTNode['url'], sizes, True)
			CTUpSpeed = str(round((ulspeed / 1000 / 1000) * 8, 2)) + " Mbit/s"

			CUid = 0
			servers = speedtest_cli.closestServers(config['client'], True)
			for server in servers:
				if server['country'].find('China') != -1 and server['sponsor'].find('Unicom') != -1:
					CUid = server['id']
			CUNode = speedtest_cli.getBestServer(filter(lambda x: x['id'] == CTid,
														servers))
			CUPing = str(round(CUNode['latency'], 2)) + " ms"
			sizes = [350, 500, 750, 1000, 1500, 2000, 2500, 3000, 3500, 4000]
			urls = []
			for size in sizes:
				for i in range(0, 4):
					urls.append('%s/random%sx%s.jpg' %
								(os.path.dirname(CUNode['url']), size, size))
			dlspeed = speedtest_cli.downloadSpeed(urls, True)
			CUDLSpeed = str(round((dlspeed / 1000 / 1000) * 8, 2)) + " Mbit/s"

			sizesizes = [int(.25 * 1000 * 1000), int(.5 * 1000 * 1000)]
			sizes = []
			for size in sizesizes:
				for i in range(0, 25):
					sizes.append(size)
			ulspeed = speedtest_cli.uploadSpeed(CUNode['url'], sizes, True)
			CUUpSpeed = str(round((ulspeed / 1000 / 1000) * 8, 2)) + " Mbit/s"

			CMid = 0
			servers = speedtest_cli.closestServers(config['client'], True)
			for server in servers:
				if server['country'].find('China') != -1 and server['sponsor'].find('Mobile') != -1:
					CMid = server['id']
			CMNode = speedtest_cli.getBestServer(filter(lambda x: x['id'] == CTid,
														servers))
			CMPing = str(round(CMNode['latency'], 2)) + " ms"
			sizes = [350, 500, 750, 1000, 1500, 2000, 2500, 3000, 3500, 4000]
			urls = []
			for size in sizes:
				for i in range(0, 4):
					urls.append('%s/random%sx%s.jpg' %
								(os.path.dirname(CMNode['url']), size, size))
			dlspeed = speedtest_cli.downloadSpeed(urls, True)
			CMDLSpeed = str(round((dlspeed / 1000 / 1000) * 8, 2)) + " Mbit/s"

			sizesizes = [int(.25 * 1000 * 1000), int(.5 * 1000 * 1000)]
			sizes = []
			for size in sizesizes:
				for i in range(0, 25):
					sizes.append(size)
			ulspeed = speedtest_cli.uploadSpeed(CMNode['url'], sizes, True)
			CMUpSpeed = str(round((ulspeed / 1000 / 1000) * 8, 2)) + " Mbit/s"


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
				"INSERT INTO `speedtest` (`id`, `node_id`, `datetime`, `telecomping`, `telecomeupload`, `telecomedownload`, `unicomping`, `unicomupload`, `unicomdownload`, `cmccping`, `cmccupload`, `cmccdownload`) VALUES (NULL, '" + str(
					mysqlcfg["node_id"]) + "', unix_timestamp(), '" + CTPing + "', '" + CTDLSpeed + "', '" + CTUpSpeed + "', '" + CUPing + "', '" + CUDLSpeed + "', '" + CUUpSpeed + "', '" + CMPing + "', '" + CMDLSpeed + "', '" + CMUpSpeed + "')")
			cur.close()
			conn.close()

			logging.info("Speedtest finished")
		except BaseException:
			logging.error("Speedtest error")

		time.sleep(hour * 3600)


