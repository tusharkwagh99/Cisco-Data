#!/usr/bin/env python
import json

inventory_data = {
    'web_servers': {
        'hosts': ['web1'],
        'vars': {
            'ansible_ssh_user': 'root',
        },
    },
    'db_servers': {
        'hosts': ['db1'],
        'vars': {
            'ansible_ssh_user': 'root',
        },
    },
    '_meta': {
        'hostvars': {
            'web1': {
                'ansible_host': '10.106.126.229',
            },
            'db1': {
                'ansible_host': '10.106.126.230',
            },
        },
    },
}

print(json.dumps(inventory_data))

