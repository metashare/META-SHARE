
from mconfig import CONFIGS

for cfg in CONFIGS:
	data_str = cfg.get_core_nodes_data()
	print "************* {0} *************".format(cfg.node_name)
	print data_str
	data_str = cfg.get_sync_users_data()
	print data_str
	print "*******************************"
	print "\n"
