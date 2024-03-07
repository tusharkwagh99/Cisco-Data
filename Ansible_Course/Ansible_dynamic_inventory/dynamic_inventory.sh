#!/bin/bash

# Example dynamic inventory script

# Output a JSON structure representing hosts and their properties
echo '{
  "web": {
    "hosts": ["web1"],
    "vars": {
      "ansible_user": "roots",
      "ansible_ssh_private_key_file": "/root/.ssh/id_rsa.pub"
    }
  },
  "db": {
    "hosts": ["db1"],
    "vars": {
      "ansible_user": "roots",
      "ansible_ssh_private_key_file": "/root/.ssh/id_rsa.pub"
    }
  }
}'

