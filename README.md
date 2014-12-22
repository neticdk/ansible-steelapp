# ansible-stingray

These are ansible modules made for managing the Stingray Traffic Manager.

Currently, it is using the REST API v. 3.0. No ther APIs are supported.

## Module: stingray_node
Manages a node and it's properties.

Complete example:
```
- hosts: all
  connection: local
  gather_facts: False
  tasks:
    - name: add node to pool
      stingray_node:
        name: mynode:80
        pool: mypool
        state: present
        lb_state: 'active'
        weight: 2
        priority: 1
        server: myserver.mydomain.com
        user: myuser
        password: mypassword
      register: pool
```
