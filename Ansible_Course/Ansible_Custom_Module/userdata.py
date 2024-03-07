#! /usr/bin/python

import json
from ansible.module_utils.basic import AnsibleModule
import sys
def main():
    module = AnsibleModule(
        argument_spec = dict(
            name = dict(requied=True, type='str'),
            age = dict(required=True, type='str'),
        )
    )

    name = module.params['name']
    age = module.params['age']
    
    data = dict(
        output = "Your Data has been stored succesfully"
    )

    try:
        file = open('/tmp/ansible_folder/userData.txt', 'a')
        file.write(name+ "," + age + "\n")
        module.exit_json(changed=True, success=data, msg=data)
    except Exception as e:
        module.exit_json(msg='error')

if __name__ == '__main__':
    main()
