﻿#!/usr/bin/python
# -*- coding: UTF-8 -*-

import logging
import time
import sys
import os
import socket
from server_pool import ServerPool
import traceback
from shadowsocks import common, shell, lru_cache
from configloader import load_config, get_config
import importloader
import platform
import datetime
import fcntl


switchrule = None
db_instance = None

class TransferBase(object):
	def __init__(self):
		import threading
<<<<<<< HEAD
		self.event = threading.Event()
		self.key_list = ['port', 'u', 'd', 'transfer_enable', 'passwd', 'enable']
		self.last_get_transfer = {}
		self.last_update_transfer = {}
		self.user_pass = {}
		self.port_uid_table = {}
		self.onlineuser_cache = lru_cache.LRUCache(timeout=60*30)
		self.pull_ok = False

	def load_cfg(self):
		pass
=======
		self.last_update_transfer = {}
		self.event = threading.Event()
		self.port_uid_table = {}
		self.node_speedlimit = 0.00
		self.traffic_rate = 0.0

	def update_all_user(self, dt_transfer):
		import cymysql
		update_transfer = {}
		
		query_head = 'UPDATE user'
		query_sub_when = ''
		query_sub_when2 = ''
		query_sub_in = None
		
		alive_user_count = 0
		bandwidth_thistime = 0
		
		if get_config().MYSQL_SSL_ENABLE == 1:
			conn = cymysql.connect(host=get_config().MYSQL_HOST, port=get_config().MYSQL_PORT, user=get_config().MYSQL_USER,
										passwd=get_config().MYSQL_PASS, db=get_config().MYSQL_DB, charset='utf8',ssl={'ca':get_config().MYSQL_SSL_CA,'cert':get_config().MYSQL_SSL_CERT,'key':get_config().MYSQL_SSL_KEY})
		else:
			conn = cymysql.connect(host=get_config().MYSQL_HOST, port=get_config().MYSQL_PORT, user=get_config().MYSQL_USER,
										passwd=get_config().MYSQL_PASS, db=get_config().MYSQL_DB, charset='utf8')
		
		conn.autocommit(True)
		
		for id in dt_transfer.keys():
			if dt_transfer[id][0] == 0 and dt_transfer[id][1] == 0:
				continue
			
			query_sub_when += ' WHEN %s THEN u+%s' % (id, dt_transfer[id][0] * self.traffic_rate)
			query_sub_when2 += ' WHEN %s THEN d+%s' % (id, dt_transfer[id][1] * self.traffic_rate)
			update_transfer[id] = dt_transfer[id]
			
			alive_user_count = alive_user_count + 1
			
			cur = conn.cursor()
			cur.execute("INSERT INTO `user_traffic_log` (`id`, `user_id`, `u`, `d`, `Node_ID`, `rate`, `traffic`, `log_time`) VALUES (NULL, '" + str(self.port_uid_table[id]) + "', '" + str(dt_transfer[id][0]) +"', '" + str(dt_transfer[id][1]) + "', '" + str(get_config().NODE_ID) + "', '" + str(self.traffic_rate) + "', '" + self.trafficShow((dt_transfer[id][0]+dt_transfer[id][1]) * self.traffic_rate) + "', unix_timestamp()); ")
			cur.close()
			
			
			bandwidth_thistime = bandwidth_thistime + ((dt_transfer[id][0] + dt_transfer[id][1]) * self.traffic_rate)
			
			if query_sub_in is not None:
				query_sub_in += ',%s' % id
			else:
				query_sub_in = '%s' % id
		if query_sub_when != '':
			query_sql = query_head + ' SET u = CASE port' + query_sub_when + \
						' END, d = CASE port' + query_sub_when2 + \
						' END, t = unix_timestamp() ' + \
						' WHERE port IN (%s)' % query_sub_in
			
			cur = conn.cursor()
			cur.execute(query_sql)
			cur.close()
		
		cur = conn.cursor()
		cur.execute("UPDATE `ss_node` SET `node_heartbeat`=unix_timestamp(),`node_bandwidth`=`node_bandwidth`+'" + str(bandwidth_thistime) + "' WHERE `id` = " +  str(get_config().NODE_ID) + " ; ")
		cur.close()
		
		cur = conn.cursor()
		cur.execute("INSERT INTO `ss_node_online_log` (`id`, `node_id`, `online_user`, `log_time`) VALUES (NULL, '" + str(get_config().NODE_ID) + "', '" + str(alive_user_count) + "', unix_timestamp()); ")
		cur.close()
		

		cur = conn.cursor()
		cur.execute("INSERT INTO `ss_node_info` (`id`, `node_id`, `uptime`, `load`, `log_time`) VALUES (NULL, '" + str(get_config().NODE_ID) + "', '" + str(self.uptime()) + "', '" + str(self.load()) + "', unix_timestamp()); ")
		cur.close()
		
		online_iplist = ServerPool.get_instance().get_servers_iplist()
		for id in online_iplist.keys():
			for ip in online_iplist[id]:
				cur = conn.cursor()
				cur.execute("INSERT INTO `alive_ip` (`id`, `nodeid`,`userid`, `ip`, `datetime`) VALUES (NULL, '" + str(get_config().NODE_ID) + "','" + str(self.port_uid_table[id]) + "', '" + str(ip) + "', unix_timestamp())")
				cur.close()
				
		deny_str = ""
		if platform.system() == 'Linux' and get_config().ANTISSATTACK == 1 :
			wrong_iplist = ServerPool.get_instance().get_servers_wrong()
			server_ip = socket.gethostbyname(get_config().MYSQL_HOST)
			for id in wrong_iplist.keys():
				for ip in wrong_iplist[id]:
					if str(ip) == str(server_ip):
						continue
					cur = conn.cursor()
					cur.execute("SELECT * FROM `blockip` where `ip` = '" + str(ip) + "'")
					rows = cur.fetchone()
					cur.close()
					
					if rows != None:
						continue
					if get_config().CLOUDSAFE == 1:
						cur = conn.cursor()
						cur.execute("INSERT INTO `blockip` (`id`, `nodeid`, `ip`, `datetime`) VALUES (NULL, '" + str(get_config().NODE_ID) + "', '" + str(ip) + "', unix_timestamp())")
						cur.close()
						if get_config().CLOUDSAFE == 0:
							os.system('route add -host %s gw 127.0.0.1' % str(ip))
					deny_str = deny_str + "\nALL: " + str(ip)
				if get_config().CLOUDSAFE == 0:
					deny_file=open('/etc/hosts.deny','a')
					fcntl.flock(deny_file.fileno(),fcntl.LOCK_EX)
					deny_file.write(deny_str + "\n")
					deny_file.close()
		conn.close()
		return update_transfer
		
	def uptime(self):
		with open('/proc/uptime', 'r') as f:
			return float(f.readline().split()[0])
	
	def load(self):
		import os
		return os.popen("cat /proc/loadavg | awk '{ print $1\" \"$2\" \"$3 }'").readlines()[0]
		
	def trafficShow(self,Traffic):
		if Traffic<1024 :
			return str(round((Traffic),2))+"B";
		
		if Traffic<1024*1024 :
			return str(round((Traffic/1024),2))+"KB";
		
		if Traffic<1024*1024*1024 :
			return str(round((Traffic/1024/1024),2))+"MB";
		
		return str(round((Traffic/1024/1024/1024),2))+"GB";
>>>>>>> 9d53e83b9685db970ab990e53be3299d9083d1bd

	def push_db_all_user(self):
		if self.pull_ok is False:
			return
		#更新用户流量到数据库
		last_transfer = self.last_update_transfer
		curr_transfer = ServerPool.get_instance().get_servers_transfer()
		#上次和本次的增量
		dt_transfer = {}
		for id in curr_transfer.keys():
			if id in last_transfer:
				if curr_transfer[id][0] + curr_transfer[id][1] - last_transfer[id][0] - last_transfer[id][1] <= 0:
					continue
				if last_transfer[id][0] <= curr_transfer[id][0] and \
						last_transfer[id][1] <= curr_transfer[id][1]:
					dt_transfer[id] = [curr_transfer[id][0] - last_transfer[id][0],
										curr_transfer[id][1] - last_transfer[id][1]]
				else:
					dt_transfer[id] = [curr_transfer[id][0], curr_transfer[id][1]]
			else:
				if curr_transfer[id][0] + curr_transfer[id][1] <= 0:
					continue
				dt_transfer[id] = [curr_transfer[id][0], curr_transfer[id][1]]
<<<<<<< HEAD
			if id in self.last_get_transfer:
				if curr_transfer[id][0] + curr_transfer[id][1] > self.last_get_transfer[id][0] + self.last_get_transfer[id][1]:
					self.onlineuser_cache[id] = curr_transfer[id][0] + curr_transfer[id][1]
			else:
				self.onlineuser_cache[id] = curr_transfer[id][0] + curr_transfer[id][1]
		self.onlineuser_cache.sweep()

=======
>>>>>>> 9d53e83b9685db970ab990e53be3299d9083d1bd
		update_transfer = self.update_all_user(dt_transfer)
		for id in update_transfer.keys():
			last = self.last_update_transfer.get(id, [0,0])
			self.last_update_transfer[id] = [last[0] + update_transfer[id][0], last[1] + update_transfer[id][1]]
<<<<<<< HEAD
		self.last_get_transfer = curr_transfer

	def del_server_out_of_bound_safe(self, last_rows, rows):
		#停止超流量的服务
		#启动没超流量的服务
=======

	def pull_db_all_user(self):
		import cymysql
		#数据库所有用户信息
		try:
			switchrule = importloader.load('switchrule')
			keys = switchrule.getKeys()
		except Exception as e:
			keys = ['port', 'u', 'd', 'transfer_enable', 'passwd', 'enable' ,'method','protocol','protocol_param','obfs','obfs_param','node_speedlimit','forbidden_ip','forbidden_port','disconnect_ip']
		
		if get_config().MYSQL_SSL_ENABLE == 1:
			conn = cymysql.connect(host=get_config().MYSQL_HOST, port=get_config().MYSQL_PORT, user=get_config().MYSQL_USER,
										passwd=get_config().MYSQL_PASS, db=get_config().MYSQL_DB, charset='utf8',ssl={'ca':get_config().MYSQL_SSL_CA,'cert':get_config().MYSQL_SSL_CERT,'key':get_config().MYSQL_SSL_KEY})
		else:
			conn = cymysql.connect(host=get_config().MYSQL_HOST, port=get_config().MYSQL_PORT, user=get_config().MYSQL_USER,
										passwd=get_config().MYSQL_PASS, db=get_config().MYSQL_DB, charset='utf8')
		conn.autocommit(True)
		
		cur = conn.cursor()
		
		cur.execute("SELECT `node_group`,`node_class`,`node_speedlimit`,`traffic_rate` FROM ss_node where `id`='" + str(get_config().NODE_ID) + "' AND (`node_bandwidth`<`node_bandwidth_limit` OR `node_bandwidth_limit`=0)")
		nodeinfo = cur.fetchone()
		
		if nodeinfo == None :
			rows = []
			cur.close()
			conn.commit()
			conn.close()
			return rows
		
		cur.close()
		
		self.node_speedlimit = float(nodeinfo[2])
		self.traffic_rate = float(nodeinfo[3])
		
		if nodeinfo[0] == 0 :
			node_group_sql = ""
		else:
			node_group_sql = "AND `node_group`=" + str(nodeinfo[0])
		
		cur = conn.cursor()
		cur.execute("SELECT " + ','.join(keys) + " FROM user WHERE `class`>="+ str(nodeinfo[1]) +" "+node_group_sql+" AND`enable`=1 AND `expire_in`>now() AND `transfer_enable`>`u`+`d`")
		rows = []
		for r in cur.fetchall():
			d = {}
			for column in range(len(keys)):
				d[keys[column]] = r[column]
			rows.append(d)
		cur.close()
		conn.close()
		return rows

	def cmp(self, val1, val2):
		if type(val1) is bytes:
			val1 = common.to_str(val1)
		if type(val2) is bytes:
			val2 = common.to_str(val2)
		return val1 == val2

	def del_server_out_of_bound_safe(self, last_rows, rows):
		#停止超流量的服务
		#启动没超流量的服务
		#需要动态载入switchrule，以便实时修改规则
		
		
>>>>>>> 9d53e83b9685db970ab990e53be3299d9083d1bd
		try:
			switchrule = importloader.load('switchrule')
		except Exception as e:
			logging.error('load switchrule.py fail')
		cur_servers = {}
		new_servers = {}
		for row in rows:
			try:
				allow = switchrule.isTurnOn(row) and row['enable'] == 1 and row['u'] + row['d'] < row['transfer_enable']
			except Exception as e:
				allow = False

			port = row['port']
			passwd = common.to_bytes(row['passwd'])
			cfg = {'password': passwd}
<<<<<<< HEAD
			if 'id' in row:
				self.port_uid_table[row['port']] = row['id']

			read_config_keys = ['method', 'obfs', 'obfs_param', 'protocol', 'protocol_param', 'forbidden_ip', 'forbidden_port']
=======
			
			self.port_uid_table[row['port']] = row['id']

			read_config_keys = ['method', 'obfs','obfs_param' , 'protocol', 'protocol_param' ,'forbidden_ip', 'forbidden_port' , 'node_speedlimit','forbidden_ip','forbidden_port','disconnect_ip']
			
>>>>>>> 9d53e83b9685db970ab990e53be3299d9083d1bd
			for name in read_config_keys:
				if name in row and row[name]:
					cfg[name] = row[name]
					
					
			
			merge_config_keys = ['password'] + read_config_keys
			for name in cfg.keys():
				if hasattr(cfg[name], 'encode'):
					cfg[name] = cfg[name].encode('utf-8')
					
			if 'node_speedlimit' in cfg:
				if float(self.node_speedlimit) > 0.0 or float(cfg['node_speedlimit']) > 0.0 :
					cfg['node_speedlimit'] = max(float(self.node_speedlimit),float(cfg['node_speedlimit']))
			else:
				cfg['node_speedlimit'] = max(float(self.node_speedlimit),float(0.00))
			
			if 'disconnect_ip' not in cfg:
				cfg['disconnect_ip'] = ''
				
			if 'forbidden_ip' not in cfg:
				cfg['forbidden_ip'] = ''
				
			if 'forbidden_port' not in cfg:
				cfg['forbidden_port'] = ''
				
			if 'protocol_param' not in cfg:
				cfg['protocol_param'] = ''
				
			if 'obfs_param' not in cfg:
				cfg['obfs_param'] = ''

			if port not in cur_servers:
				cur_servers[port] = passwd
			else:
				logging.error('more than one user use the same port [%s]' % (port,))
				continue
				

			if ServerPool.get_instance().server_is_run(port) > 0:
				if not allow:
					logging.info('db stop server at port [%s]' % (port,))
					ServerPool.get_instance().cb_del_server(port)
					if port in self.last_update_transfer:
						del self.last_update_transfer[port]
				else:
					cfgchange = False
					if port in ServerPool.get_instance().tcp_servers_pool:
						relay = ServerPool.get_instance().tcp_servers_pool[port]
						for name in merge_config_keys:
							if name in cfg and not self.cmp(cfg[name], relay._config[name]):
								cfgchange = True
								break;
					if not cfgchange and port in ServerPool.get_instance().tcp_ipv6_servers_pool:
						relay = ServerPool.get_instance().tcp_ipv6_servers_pool[port]
						for name in merge_config_keys:
							if name in cfg and not self.cmp(cfg[name], relay._config[name]):
								cfgchange = True
								break;
					#config changed
					if cfgchange:
						logging.info('db stop server at port [%s] reason: config changed: %s' % (port, cfg))
						ServerPool.get_instance().cb_del_server(port)
						if port in self.last_update_transfer:
							del self.last_update_transfer[port]
						new_servers[port] = (passwd, cfg)

			elif allow and ServerPool.get_instance().server_run_status(port) is False:
				#new_servers[port] = passwd
				protocol = cfg.get('protocol', ServerPool.get_instance().config.get('protocol', 'origin'))
				obfs = cfg.get('obfs', ServerPool.get_instance().config.get('obfs', 'plain'))
				logging.info('db start server at port [%s] pass [%s] protocol [%s] obfs [%s]' % (port, passwd, protocol, obfs))
				ServerPool.get_instance().new_server(port, cfg)

		for row in last_rows:
			if row['port'] in cur_servers:
				pass
			else:
				logging.info('db stop server at port [%s] reason: port not exist' % (row['port']))
				ServerPool.get_instance().cb_del_server(row['port'])
<<<<<<< HEAD
				if row['port'] in self.port_uid_table:
					del self.port_uid_table[row['port']]
=======
				if row['port'] in self.last_update_transfer:
					del self.last_update_transfer[row['port']]
				del self.port_uid_table[row['port']]
>>>>>>> 9d53e83b9685db970ab990e53be3299d9083d1bd

		if len(new_servers) > 0:
			from shadowsocks import eventloop
			self.event.wait(eventloop.TIMEOUT_PRECISION + eventloop.TIMEOUT_PRECISION / 2)
			for port in new_servers.keys():
				passwd, cfg = new_servers[port]
				protocol = cfg.get('protocol', ServerPool.get_instance().config.get('protocol', 'origin'))
				obfs = cfg.get('obfs', ServerPool.get_instance().config.get('obfs', 'plain'))
				logging.info('db start server at port [%s] pass [%s] protocol [%s] obfs [%s]' % (port, passwd, protocol, obfs))
				ServerPool.get_instance().new_server(port, cfg)

	def cmp(self, val1, val2):
		if type(val1) is bytes:
			val1 = common.to_str(val1)
		if type(val2) is bytes:
			val2 = common.to_str(val2)
		return val1 == val2

	@staticmethod
	def del_servers():
		for port in [v for v in ServerPool.get_instance().tcp_servers_pool.keys()]:
			if ServerPool.get_instance().server_is_run(port) > 0:
				ServerPool.get_instance().cb_del_server(port)
				if port in self.last_update_transfer:
					del self.last_update_transfer[port]
		for port in [v for v in ServerPool.get_instance().tcp_ipv6_servers_pool.keys()]:
			if ServerPool.get_instance().server_is_run(port) > 0:
				ServerPool.get_instance().cb_del_server(port)
				if port in self.last_update_transfer:
					del self.last_update_transfer[port]

	@staticmethod
	def thread_db(obj):
		import socket
		import time
		global db_instance
		timeout = 60
		socket.setdefaulttimeout(timeout)
		last_rows = []
		db_instance = obj()
		try:
			while True:
				load_config()
				db_instance.load_cfg()
				try:
					db_instance.push_db_all_user()
					rows = db_instance.pull_db_all_user()
					if rows:
						db_instance.pull_ok = True
					db_instance.del_server_out_of_bound_safe(last_rows, rows)
					last_rows = rows
				except Exception as e:
					trace = traceback.format_exc()
					logging.error(trace)
					#logging.warn('db thread except:%s' % e)
				if db_instance.event.wait(get_config().UPDATE_TIME) or not ServerPool.get_instance().thread.is_alive():
					break
		except KeyboardInterrupt as e:
			pass
		db_instance.del_servers()
		ServerPool.get_instance().stop()
		db_instance = None

	@staticmethod
	def thread_db_stop():
		global db_instance
		db_instance.event.set()

class DbTransfer(TransferBase):
	def __init__(self):
		super(DbTransfer, self).__init__()
		self.cfg = {
			"host": "127.0.0.1",
			"port": 3306,
			"user": "ss",
			"password": "pass",
			"db": "shadowsocks",
			"node_id": 1,
			"transfer_mul": 1.0,
			"ssl_enable": 0,
			"ssl_ca": "",
			"ssl_cert": "",
			"ssl_key": ""}
		self.load_cfg()

	def load_cfg(self):
		import json
		config_path = get_config().MYSQL_CONFIG
		cfg = None
		with open(config_path, 'r+') as f:
			cfg = json.loads(f.read().decode('utf8'))

		if cfg:
			self.cfg.update(cfg)

	def update_all_user(self, dt_transfer):
		import cymysql
		update_transfer = {}
		
		query_head = 'UPDATE user'
		query_sub_when = ''
		query_sub_when2 = ''
		query_sub_in = None
		last_time = time.time()

		for id in dt_transfer.keys():
			transfer = dt_transfer[id]
			update_trs = 1024 * max(2048 - self.user_pass.get(id, 0) * 64, 16)
			if transfer[0] + transfer[1] < update_trs:
				continue
			if id in self.user_pass:
				del self.user_pass[id]

			query_sub_when += ' WHEN %s THEN u+%s' % (id, int(transfer[0] * self.cfg["transfer_mul"]))
			query_sub_when2 += ' WHEN %s THEN d+%s' % (id, int(transfer[1] * self.cfg["transfer_mul"]))
			update_transfer[id] = transfer

			if query_sub_in is not None:
				query_sub_in += ',%s' % id
			else:
				query_sub_in = '%s' % id

		if query_sub_when == '':
			return update_transfer
		query_sql = query_head + ' SET u = CASE port' + query_sub_when + \
					' END, d = CASE port' + query_sub_when2 + \
					' END, t = ' + str(int(last_time)) + \
					' WHERE port IN (%s)' % query_sub_in
		if self.cfg["ssl_enable"] == 1:
			conn = cymysql.connect(host=self.cfg["host"], port=self.cfg["port"],
					user=self.cfg["user"], passwd=self.cfg["password"],
					db=self.cfg["db"], charset='utf8',
					ssl={'ca':self.cfg["ssl_enable"],'cert':self.cfg["ssl_enable"],'key':self.cfg["ssl_enable"]})
		else:
			conn = cymysql.connect(host=self.cfg["host"], port=self.cfg["port"],
					user=self.cfg["user"], passwd=self.cfg["password"],
					db=self.cfg["db"], charset='utf8')

		cur = conn.cursor()
		cur.execute(query_sql)
		cur.close()
		conn.commit()
		conn.close()
		return update_transfer

	def pull_db_all_user(self):
		import cymysql
		#数据库所有用户信息
		if self.cfg["ssl_enable"] == 1:
			conn = cymysql.connect(host=self.cfg["host"], port=self.cfg["port"],
					user=self.cfg["user"], passwd=self.cfg["password"],
					db=self.cfg["db"], charset='utf8',
					ssl={'ca':self.cfg["ssl_enable"],'cert':self.cfg["ssl_enable"],'key':self.cfg["ssl_enable"]})
		else:
			conn = cymysql.connect(host=self.cfg["host"], port=self.cfg["port"],
					user=self.cfg["user"], passwd=self.cfg["password"],
					db=self.cfg["db"], charset='utf8')

		rows = self.pull_db_users(conn)
		conn.close()
		return rows

	def pull_db_users(self, conn):
		try:
			switchrule = importloader.load('switchrule')
			keys = switchrule.getKeys(self.key_list)
		except Exception as e:
			keys = self.key_list

		cur = conn.cursor()
		cur.execute("SELECT " + ','.join(keys) + " FROM user")
		rows = []
		for r in cur.fetchall():
			d = {}
			for column in range(len(keys)):
				d[keys[column]] = r[column]
			rows.append(d)
		cur.close()
		return rows

class Dbv3Transfer(DbTransfer):
	def __init__(self):
		super(Dbv3Transfer, self).__init__()
		self.key_list += ['id', 'method']
		if get_config().API_INTERFACE == 'sspanelv3ssr':
			self.key_list += ['obfs', 'protocol']
		self.start_time = time.time()

	def update_all_user(self, dt_transfer):
		import cymysql
		update_transfer = {}

		query_head = 'UPDATE user'
		query_sub_when = ''
		query_sub_when2 = ''
		query_sub_in = None
		last_time = time.time()

		alive_user_count = len(self.onlineuser_cache)
		bandwidth_thistime = 0

		if self.cfg["ssl_enable"] == 1:
			conn = cymysql.connect(host=self.cfg["host"], port=self.cfg["port"],
					user=self.cfg["user"], passwd=self.cfg["password"],
					db=self.cfg["db"], charset='utf8',
					ssl={'ca':self.cfg["ssl_enable"],'cert':self.cfg["ssl_enable"],'key':self.cfg["ssl_enable"]})
		else:
			conn = cymysql.connect(host=self.cfg["host"], port=self.cfg["port"],
					user=self.cfg["user"], passwd=self.cfg["password"],
					db=self.cfg["db"], charset='utf8')
		conn.autocommit(True)

		for id in dt_transfer.keys():
			transfer = dt_transfer[id]
			bandwidth_thistime = bandwidth_thistime + transfer[0] + transfer[1]

			update_trs = 1024 * max(2048 - self.user_pass.get(id, 0) * 64, 16)
			if transfer[0] + transfer[1] < update_trs:
				self.user_pass[id] = self.user_pass.get(id, 0) + 1
				continue
			if id in self.user_pass:
				del self.user_pass[id]

			query_sub_when += ' WHEN %s THEN u+%s' % (id, int(transfer[0] * self.cfg["transfer_mul"]))
			query_sub_when2 += ' WHEN %s THEN d+%s' % (id, int(transfer[1] * self.cfg["transfer_mul"]))
			update_transfer[id] = transfer

			cur = conn.cursor()
			try:
				if id in self.port_uid_table:
					cur.execute("INSERT INTO `user_traffic_log` (`id`, `user_id`, `u`, `d`, `node_id`, `rate`, `traffic`, `log_time`) VALUES (NULL, '" + \
						str(self.port_uid_table[id]) + "', '" + str(transfer[0]) + "', '" + str(transfer[1]) + "', '" + \
						str(self.cfg["node_id"]) + "', '" + str(self.cfg["transfer_mul"]) + "', '" + \
						self.traffic_format((transfer[0] + transfer[1]) * self.cfg["transfer_mul"]) + "', unix_timestamp()); ")
			except:
				logging.warn('no `user_traffic_log` in db')
			cur.close()

			if query_sub_in is not None:
				query_sub_in += ',%s' % id
			else:
				query_sub_in = '%s' % id

		if query_sub_when != '':
			query_sql = query_head + ' SET u = CASE port' + query_sub_when + \
						' END, d = CASE port' + query_sub_when2 + \
						' END, t = ' + str(int(last_time)) + \
						' WHERE port IN (%s)' % query_sub_in
			cur = conn.cursor()
			cur.execute(query_sql)
			cur.close()

		try:
			cur = conn.cursor()
			cur.execute("INSERT INTO `ss_node_online_log` (`id`, `node_id`, `online_user`, `log_time`) VALUES (NULL, '" + \
					str(self.cfg["node_id"]) + "', '" + str(alive_user_count) + "', unix_timestamp()); ")
			cur.close()

			cur = conn.cursor()
			cur.execute("INSERT INTO `ss_node_info_log` (`id`, `node_id`, `uptime`, `load`, `log_time`) VALUES (NULL, '" + \
					str(self.cfg["node_id"]) + "', '" + str(self.uptime()) + "', '" + \
					str(self.load()) + "', unix_timestamp()); ")
			cur.close()
		except:
			logging.warn('no `ss_node_online_log` or `ss_node_info_log` in db')

		conn.close()
		return update_transfer

	def pull_db_users(self, conn):
		try:
			switchrule = importloader.load('switchrule')
			keys = switchrule.getKeys(self.key_list)
		except Exception as e:
			keys = self.key_list

		cur = conn.cursor()

		node_info_keys = ['traffic_rate']
		cur.execute("SELECT " + ','.join(node_info_keys) +" FROM ss_node where `id`='" + str(self.cfg["node_id"]) + "'")
		nodeinfo = cur.fetchone()

		if nodeinfo == None:
			rows = []
			cur.close()
			conn.commit()
			return rows
		cur.close()

		node_info_dict = {}
		for column in range(len(nodeinfo)):
			node_info_dict[node_info_keys[column]] = nodeinfo[column]
		self.cfg['transfer_mul'] = float(node_info_dict['traffic_rate'])

		cur = conn.cursor()
		cur.execute("SELECT " + ','.join(keys) + " FROM user")
		rows = []
		for r in cur.fetchall():
			d = {}
			for column in range(len(keys)):
				d[keys[column]] = r[column]
			rows.append(d)
		cur.close()
		return rows

	def load(self):
		import os
		return os.popen("cat /proc/loadavg | awk '{ print $1\" \"$2\" \"$3 }'").readlines()[0]

	def uptime(self):
		return time.time() - self.start_time

	def traffic_format(self, traffic):
		if traffic < 1024 * 8:
			return str(int(traffic)) + "B";

		if traffic < 1024 * 1024 * 2:
			return str(round((traffic / 1024.0), 2)) + "KB";

		return str(round((traffic / 1048576.0), 2)) + "MB";

class MuJsonTransfer(TransferBase):
	def __init__(self):
		super(MuJsonTransfer, self).__init__()

	def update_all_user(self, dt_transfer):
		import json
		rows = None

		config_path = get_config().MUDB_FILE
		with open(config_path, 'rb+') as f:
			rows = json.loads(f.read().decode('utf8'))
			for row in rows:
				if "port" in row:
					port = row["port"]
					if port in dt_transfer:
						row["u"] += dt_transfer[port][0]
						row["d"] += dt_transfer[port][1]

		if rows:
			output = json.dumps(rows, sort_keys=True, indent=4, separators=(',', ': '))
			with open(config_path, 'r+') as f:
				f.write(output)
				f.truncate()

		return dt_transfer

	def pull_db_all_user(self):
		import json
		rows = None

		config_path = get_config().MUDB_FILE
		with open(config_path, 'rb+') as f:
			rows = json.loads(f.read().decode('utf8'))
			for row in rows:
				try:
					if 'forbidden_ip' in row:
						row['forbidden_ip'] = common.IPNetwork(row['forbidden_ip'])
				except Exception as e:
					logging.error(e)
				try:
					if 'forbidden_port' in row:
						row['forbidden_port'] = common.PortRange(row['forbidden_port'])
				except Exception as e:
					logging.error(e)
				try:
					if 'disconnect_ip' in row:
						row['disconnect_ip'] = common.IPNetwork(row['disconnect_ip'])
				except Exception as e:
					logging.error(e)
				
		return rows

