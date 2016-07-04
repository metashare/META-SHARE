
from mconfig import CONFIGS

for cfg in CONFIGS:
	print "************* {0} *************".format(cfg.node_name)
	data_str = cfg.get_core_nodes_data()
	print data_str
	print "\n"
	data_str = cfg.get_outer_nodes_data()
	print data_str
	print "\n"
	data_str = cfg.get_sync_users_data()
	print data_str
	print "\n"
	print "*******************************"
	print "\n"
