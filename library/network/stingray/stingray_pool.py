#!/usr/bin/python
# -*- coding: utf-8 -*-

import json
import requests

DOCUMENTATION = """
module: stingray_pool
version_added: 1.8.2
short_description: manage stingray pools
description:
    - Manage pools in a Stingray Traffic Manager
author: Kim Nørgaard
options:
    name:
        description:
            - Name of pool to work on
        required: true
        default: null
        aliases: ['pool']
    operation:
        description:
            - Operation to perform on named pool
        required: false
        default: 'show'
        choices: ['show', 'enablenodes', 'disablenodes', 'drainnodes']
        aliases: ['op', 'command']
    server:
        description:
            - Server to connect to (without URI scheme or port)
        required: true
        default: null
    port:
        description:
            - Port used to connect to server
        required: false
        default: 9070
    timeout:
        description:
            - Timeout for HTTP connections
        required: false
        default: 3
    user:
        description:
            - Username used for authentication
        required: true
        default: null
    password:
        description:
            - Password used for authentication
        required: true
        default: null
    nodes:
        description:
            - List of nodes to perform node operations on
        required: false
        default: null
"""
# TODO: examples

def show(response, client, nodes):
    body = response.text

    if body:
        return json.loads(body)
    else:
        return {}

# Some parameters are required depending on the operation:
OP_REQUIRED = dict(enablenodes=['nodes'],
                   disablenodes=['nodes'],
                   drainnodes=['nodes'],
                   show=[])

def main():
    module = AnsibleModule(
            argument_spec = dict(
                name      = dict(required=True,
                            aliases=['pool']),
                server    = dict(required=True),
                port      = dict(default=9070, required=False),
                user      = dict(required=True),
                password  = dict(required=True),
                timeout   = dict(default=3, required=False),
                operation = dict(choices=['enablenodes', 'disablenodes', 'drainnodes', 'show'],
                                 aliases=['op', 'command'], required=True),
                nodes     = dict(require=False),
            ),
            supports_check_mode = True,
    )

    server   = module.params['server']
    port     = module.params['port']
    user     = module.params['user']
    password = module.params['password']
    pool     = module.params['name']
    op       = module.params['operation']
    nodes    = module.params['nodes']
    timeout  = module.params['timeout']

    url = 'https://{0}:{1}/api/tm/2.0/config/active/pools/{2}'.format(server, port, pool)

    jsontype = {'content-type': 'application/json'}

    # Check we have the necessary per-operation parameters
    missing = []
    for parm in OP_REQUIRED[op]:
        if not module.params[parm]:
            missing.append(parm)
    if missing:
        module.fail_json(msg="Operation %s require the following missing parameters: %s" % (op, ",".join(missing)))

    client = requests.Session()
    client.auth = (user, password)
    client.verify = False

    try:
        response = client.get(url, timeout=timeout)
    except requests.exceptions.ConnectionError as e:  
        return module.fail_json(msg="Unable to connect to {0}: {1}".format(url, e.message))

    #TODO: if module.check_mode:

    if response.status_code == 404:
        return module.fail_json(msg="Pool {0} not found".format(pool))

    try:
        thismod = sys.modules[__name__]
        method = getattr(thismod, op)

        ret = method(response, client, nodes)

    except Exception as e:
        return module.fail_json(msg=e.message)

    return module.exit_json(changed=True, properties=ret['properties'])

from ansible.module_utils.basic import *
main()
