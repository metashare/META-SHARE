
import sys

if len(sys.argv) < 3:
	sys.exit(-1)

from mconfig import CONFIGS

c = CONFIGS[int(sys.argv[1])].get(sys.argv[2])
print c

