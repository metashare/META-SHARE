
'''
	Author: Salvatore Minutoli

	Create a configuration of Metashare nodes for testing.
	For each node appropriate features are collected in
	order to make them run on a single machine.
'''

CONFIGS = []

class mconfig:
	db_base = 'metashare'
	solr_port_base = 4444
	solr_stop_port_base = 3333
	solr_stop_key = 'stop'
	solr_log_base = 'sol_log_'
	solr_root = '/home/metashare/git/META-SHARE-NEW/solr/instances'

	def __init__(self, node_id, node_name, meta_dir, django_port, node_type):
		self.node_id = node_id
		self.node_name = node_name
		self.metashare_dir = meta_dir
		self.django_port = django_port
		self.node_type = node_type
		self.outer_nodes = []

	def set_proxy(self, proxy_node):
		self.proxy_node = proxy_node
		self.proxy_node.outer_nodes.append(self)

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
		self.dict['SOLR_LOG'] = '{0}{1}.log'.format(self.solr_log_base,  self.node_id)
		self.dict['SOLR_ROOT'] = '{0}/instance{1}'.format(self.solr_root,  self.node_id)

	def get(self, name):
		self.build_dict()
		return self.dict[name]

dj_port = 8000
metashare_dir = '/home/metashare/git/META-SHARE-NEW/metashare'
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

