import os
import sys
import shutil
import json
import tabulate
import pprint
from pymongo import MongoClient
client = MongoClient()
client = MongoClient('mongodb://192.168.0.54:27017/')
db = client['cmdb']
rec = db.cmdb
print rec.find_one()

host = sys.argv[1]

tmp_dir = 'result/'

try:
#    shutil.rmtree(tmp_dir)
    print ""
except OSError:
    pass
cmd = "ansible -t {} -i inventory/hosts --ask-vault-pass -m setup {} >/dev/null".format(tmp_dir, host)
print cmd
os.system(cmd)

headers = [
    'Name', 'FQDN', 'Datetime', 'OS', 'Arch', 'Serial', 'Mem', 'Disk', 'Diskfree', 'IPs', 
]
d = []

for fname in os.listdir(tmp_dir):
    path = os.path.join(tmp_dir, fname)
    j = json.load(file(path, 'r'))
    if 'failed' in j:
        continue
   
    ci = {
	"ci": fname,
	"FQDN": j['ansible_facts']['ansible_fqdn'],
	"Datetime": "%s %s:%s %s %s" % ( j['ansible_facts']['ansible_date_time']['date'], j['ansible_facts']['ansible_date_time']['hour'], j['ansible_facts']['ansible_date_time']['minute'], j['ansible_facts']['ansible_date_time']['tz'], j['ansible_facts']['ansible_date_time']['tz_offset'],),
	"OS": "%s %s" % (j['ansible_facts']['ansible_distribution'],j['ansible_facts']['ansible_distribution_version'],),
	"Arch": j['ansible_facts']['ansible_architecture'],
	"Serial": j['ansible_facts']['ansible_product_serial'],
	"Memory": '%0.fg (free %0.2fg)' % ((j['ansible_facts']['ansible_memtotal_mb'] / 1000.0),(j['ansible_facts']['ansible_memfree_mb'] / 1000.0)),
	"Disk": ', '.join([str(i['size_total']/1048576000) + 'g' for i in j['ansible_facts']['ansible_mounts']]),
	"DiskFree": ', '.join([str(i['size_available']/1048576000) + 'g' for i in j['ansible_facts']['ansible_mounts']]),
	"IPAddress": ', '.join(j['ansible_facts']['ansible_all_ipv4_addresses']),
    }
    ciID = rec.insert_one(ci).inserted_id
    print ciID 
    d.append(
        (
            fname,
            j['ansible_facts']['ansible_fqdn'],
            "%s %s:%s %s %s" % (
                j['ansible_facts']['ansible_date_time']['date'],
                j['ansible_facts']['ansible_date_time']['hour'],
                j['ansible_facts']['ansible_date_time']['minute'],
                j['ansible_facts']['ansible_date_time']['tz'],
                j['ansible_facts']['ansible_date_time']['tz_offset'],
            ),
            "%s %s" % (
                j['ansible_facts']['ansible_distribution'],
                j['ansible_facts']['ansible_distribution_version'],
            ),
            j['ansible_facts']['ansible_architecture'],
            j['ansible_facts']['ansible_product_serial'],
            '%0.fg (free %0.2fg)' % (
                (j['ansible_facts']['ansible_memtotal_mb'] / 1000.0),
                (j['ansible_facts']['ansible_memfree_mb'] / 1000.0)
                ),
            ', '.join([str(i['size_total']/1048576000) + 'g' for i in j['ansible_facts']['ansible_mounts']]),
            ', '.join([str(i['size_available']/1048576000) + 'g' for i in j['ansible_facts']['ansible_mounts']]),
            ', '.join(j['ansible_facts']['ansible_all_ipv4_addresses']),
        )
    )
    os.unlink(path)
#shutil.rmtree(tmp_dir)
print tabulate.tabulate(d, headers=headers)
