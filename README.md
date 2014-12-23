# ansible-stingray

These are ansible modules made for managing the Stingray Traffic Manager.

Currently, it is using the REST API v. 3.0. No ther APIs are supported.

Presently, the following modules are available:
  * stingray\_node - for managing nodes in pools
  * stingray\_pool - for managing pool configurations

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

### Fields

#### name (required)
Name of node to manage.

#### pool (required)
Name of pool to manage.

#### state
Desired state:
  * present: ensure the node exists
  * absent: ensure the node does not exist

Default: present

#### lb_state
State of node in pool:
  * active: enable the node (default for new nodes)
  * disabled: disable the node
  * draining: drain the node

The default for new nodes is 'active'.

#### weight
Set the weight of the node.
Defaults to the server's default.

#### priority
Set the priority of the node.
Defaults to the server's default.

#### server (required)
FQDN of stingray server.

#### port
Port to connect to (default: 9070).

#### timeout
HTTP timeout (default: 3).


## Module: stingray_pool
Manage a pool and it's properties
