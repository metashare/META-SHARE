
'''
	Author: Salvatore Minutoli

	Create a configuration of Metashare nodes for testing.
	For each node appropriate features are collected in
	order to make them run on a single machine.
'''

import os

CONFIGS = []

class mconfig:
	db_base = 'metashare'
	solr_port_base = 4444
	solr_stop_port_base = 3333
	solr_stop_key = 'stop'
	solr_log_base = 'sol_log_'
	root_dir = ''
	metashare_dir = root_dir + '/metashare'
	solr_root = root_dir + '/solr/instances'
	# Collect all META-SHARE Managing Nodes (aka. inner nodes)
	inner_nodes = []

	def set_root_dir(cls, metashare_dir):
		mconfig.root_dir = root_dir
		mconfig.metashare_dir = mconfig.root_dir + '/metashare'
		mconfig.solr_root = mconfig.root_dir + '/solr/instances'

	def __init__(self, node_id, node_name, meta_dir, django_port, node_type):
		self.node_id = node_id
		self.node_name = node_name
		self.metashare_dir = meta_dir
		self.django_port = django_port
		self.node_type = node_type
		self.outer_nodes = []
		# List of proxy nodes. Usually there should be only one.
		# We allow for multiple proxy to test if something wrong can
		# happen when using inappropriate configurations.
		self.proxy_nodes = []
		if self.node_type == 'inner':
			mconfig.inner_nodes.append(self)

	def set_proxy(self, proxy_node):
		self.proxy_nodes.append(proxy_node)
		proxy_node.outer_nodes.append(self)

	def get_proxy_nodes(self):
		return self.proxy_nodes

	def build_dict(self):
		self.dict = {}
		self.dict['NODE_ID'] = self.node_id
		self.dict['NODE_NAME'] = self.node_name
		self.dict['NODE_TYPE'] = self.node_type
		self.dict['METASHARE_DIR'] = self.metashare_dir
		self.dict['DJANGO_PORT'] = self.django_port
		self.dict['DATABASE_NAME'] = '{0}{1}.db'.format(self.db_base, self.node_id)
		self.dict['SOLR_PORT'] = self.solr_port_base + self.node_id
		self.dict['SOLR_STOP_PORT'] = self.solr_stop_port_base + self.node_id
		self.dict['SOLR_STOP_KEY'] = self.solr_stop_key
		self.dict['SOLR_LOG'] = '{0}{1}.log'.format(self.solr_log_base, self.node_id)
		self.dict['SOLR_ROOT'] = '{0}/instance{1}'.format(self.solr_root, self.node_id)
		self.dict['SYNC_USERS'] = self.get_sync_users_data(escape=True)
		self.dict['CORE_NODES'] = self.get_core_nodes_data(escape=True)
		self.dict['PROXIED_NODES'] = self.get_outer_nodes_data(escape=True)

	def get_other_inner_nodes(self):
		if self.node_type == 'outer':
			return []
		other_inner_nodes = []
		for n in mconfig.inner_nodes:
			if n.node_id != self.node_id:
				other_inner_nodes.append(n)
		return other_inner_nodes

	def get_outer_nodes(self):
		return self.outer_nodes

	def get_outer_nodes_data(self, escape=False):
		return self._get_other_nodes_data(
			self.get_outer_nodes(), 'PROXIED_NODES', escape, 'outer_node')

	def get_core_nodes_data(self, escape=False):
		return self._get_other_nodes_data(
			self.get_other_inner_nodes(), 'CORE_NODES', escape)

	def _get_other_nodes_data(self, nodes, data_name, escape, node_prefix='node'):
		counter = 1
		end_str = ''
		if escape:
			end_str = '\\'
		data_str = "{0} = {{{1}\n".format(data_name, end_str)
		for n in nodes:
			data_str = data_str + "\t'{2}{0}' : {{{1}\n".format(counter, end_str, node_prefix)
			data_str = data_str + "\t\t'NAME': '{0}',{1}\n".format(n.node_name, end_str)
			data_str = data_str + "\t\t'DESCRIPTION': '{0} Metashare node',{1}\n".format(n.node_name, end_str)
			data_str = data_str + "\t\t'URL': 'http://127.0.0.1:{0}/metashare',{1}\n".format(n.django_port, end_str)
			data_str = data_str + "\t\t'USERNAME': 'sync-user-{0}',{1}\n".format(self.node_id, end_str)
			data_str = data_str + "\t\t'PASSWORD': 'sync-user-pass-{0}',{1}\n".format(self.node_id, end_str)
			data_str = data_str + "\t}},{0}\n".format(end_str)
			counter = counter + 1
		data_str = data_str + "}"
		return data_str

	def get_sync_users_data(self, escape=False):
		counter = 1
		end_str = ''
		if escape:
			end_str = '\\'
		data_str = "SYNC_USERS = {{{0}\n".format(end_str)
		if self.node_type == 'inner':
			for n in self.get_other_inner_nodes():
				data_str = data_str + "\t'sync-user-{0}' : 'sync-user-pass-{0}',{1}\n".format(n.node_id, end_str)
				counter = counter + 1
		else:
			for n in self.get_proxy_nodes():
				data_str = data_str + "\t'sync-user-{0}' : 'sync-user-pass-{0}',{1}\n".format(n.node_id, end_str)
				counter = counter + 1
		data_str = data_str + "}"
		return data_str

	def get(self, name):
		self.build_dict()
		return self.dict[name]

dj_port = 18000
metashare_dir = '{0}/metashare'.format(os.environ['METASHARE_SW_DIR'])
count = 0

dj_port = dj_port + 1
count = count + 1
cnf1 = mconfig(count, 'Node1', metashare_dir, dj_port, 'inner')
CONFIGS.append(cnf1)

dj_port = dj_port + 1
count = count + 1
cnf2 = mconfig(count, 'Node2', metashare_dir, dj_port, 'inner')
CONFIGS.append(cnf2)

dj_port = dj_port + 1
count = count + 1
cnf3 = mconfig(count, 'Node3', metashare_dir, dj_port, 'outer')
cnf3.set_proxy(cnf2)
CONFIGS.append(cnf3)

dj_port = dj_port + 1
count = count + 1
cnf4 = mconfig(count, 'Node4', metashare_dir, dj_port, 'inner')
CONFIGS.append(cnf4)

