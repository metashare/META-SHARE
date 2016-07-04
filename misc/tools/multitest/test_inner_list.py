
from mconfig import CONFIGS

for cfg in CONFIGS:
	print cfg.node_name
	inner_list = cfg.get_other_inner_nodes()
	inner_names = []
	for n in inner_list:
		inner_names.append(n.node_name)
	print "   Inner nodes: {0}".format(', '.join(inner_names))
	outer_list = cfg.get_outer_nodes()
	outer_names = []
	for n in outer_list:
		outer_names.append(n.node_name)
	print "   Outer nodes: {0}".format(', '.join(outer_names))
	proxy_list = cfg.get_proxy_nodes()
	proxy_names = []
	for n in proxy_list:
		proxy_names.append(n.node_name)
	print "   Proxy nodes: {0}".format(', '.join(proxy_names))
