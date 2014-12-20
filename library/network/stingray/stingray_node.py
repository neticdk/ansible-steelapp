#!/usr/bin/python
# -*- coding: utf-8 -*-

import json
import requests

DOCUMENTATION = """
module: stingray_node
version_added: 1.8.2
short_description: manage nodes in stingray traffic managers
description:
    - Manage nodes in a Stingray Traffic Managers
author: Kim Nørgaard
options:
    name:
        description:
            - Name of node to work on
        required: true
        default: null
        aliases: ['node']
    pool:
        description:
            - Name of pool to work on
        required: true
        default: null
    state:
        description:
            - Operation to perform on node
        required: false
        default: 'present'
        choices: ['present', 'absent', 'enabled', 'disabled', 'draining']
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
"""
# TODO: examples
# TODO: priority, weight

class StingrayNode(object):
    def __init__(self, module, server, port, timeout, user, password, pool, node):
        self.module      = module
        self.server      = server
        self.port        = port
        self.timeout     = timeout
        self.user        = user
        self.password    = password
        self.pool        = pool
        self.node        = node
        self.msg         = ''
        self.changed     = False

        self._url = 'https://{0}:{1}/api/tm/3.0/config/active/pools/{2}'.format(server, port, pool)
        self._jsontype = {'content-type': 'application/json'}

        self._client = requests.Session()
        self._client.auth = (user, password)
        self._client.verify = False

        try:
            response = self._client.get(self._url, timeout=self.timeout)
        except requests.exceptions.ConnectionError as e:
            self.module.fail_json(msg=
                    "Unable to connect to {0}: {1}".format(self._url, e.message))

        if response.status_code == 404:
            self.module.fail_json(msg="Pool {0} not found".format(self.pool))

        try:
            self.pool_data = json.loads(response.text)
        except Exception as e:
            self.module.fail_json(msg=str(e))

    def _nodes(self):
        return self.pool_data['properties']['basic']['nodes_table']

    def _node_exists(self):
        return bool([n for n in self._nodes()
            if n['node'] == self.node])

    def _has_state(self, state):
        return bool([n for n in self._nodes()
            if n['node'] == self.node and n['state'] == state])

    def set_nodes(self, nodes):
            pool_data = {
                    'properties': {
                        'basic': {
                            'nodes_table': nodes
                        }
                    }
            }

            return self._client.put(self._url, data = json.dumps(pool_data),
                                    headers = self._jsontype)

    def set_present(self):
        if not self._node_exists():
            if self.module.check_mode:
                self.msg = "Add %s to %s" % (self.node, self.pool)
                self.changed = True
                return

            new_nodes = self._nodes()+[{'node': self.node, 'state': 'active'}]
            response = self.set_nodes(new_nodes)

            if response.status_code == 200:
                self.changed = True
                self.msg = "Added {0} to {1}".format(self.node, self.pool)
                self.pool_data = json.loads(response.text)
            else:
                self.module.fail_json(msg=
                        "Failed to add {0} to {1} - got HTTP {2} from \
                        server".format(self.node, self.pool,
                                       response.status_code))
        else:
            self.changed = False
            self.msg = "{0} in {1} already present".format(self.node, self.pool)

    def set_absent(self):
        if self._node_exists():
            if self.module.check_mode:
                self.msg = "Remove {0} from {1}".format(self.node, self.pool)
                self.changed = True
                return

            new_nodes = [n for n in self._nodes() if n['node'] != self.node]
            response = self.set_nodes(new_nodes)

            if response.status_code == 200:
                self.changed = True
                self.msg = "Removed {0} from {1}".format(self.node, self.pool)
                self.pool_data = json.loads(response.text)
            else:
                self.module.fail_json(msg=
                        "Failed to remove {0} from {1} - got HTTP {2} from \
                        server".format(self.node, self.pool,
                                       response.status_code))
        else:
            self.changed = False
            self.msg = "{0} in {1} already absent".format(self.node, self.pool)

    def set_state(self, new_state):
        if self._node_exists():
            if not self._has_state(new_state):
                if self.module.check_mode:
                    self.msg = "Set {0} in {1} to {2}".format(
                            self.node, self.pool, new_state)
                    self.changed = True
                    return

                new_nodes = self._nodes()
                for node in new_nodes:
                    node.update(
                            ('state', new_state) for k, v in node.iteritems()
                            if v == self.node)

                response = self.set_nodes(new_nodes)

                if response.status_code == 200:
                    self.changed = True
                    self.msg = "Set {0} in {1} to {2}".format(
                            self.node, self.pool, new_state)
                    self.pool_data = json.loads(response.text)
                else:
                    self.module.fail_json(msg=
                            "Failed to set {0} in {1} to {2} - got HTTP {3} \
                            from server".format(self.node, self.pool,
                                                new_state,
                                                response.status_code))
            else:
                self.changed = False
                self.msg = "{0} in {1} already set to {2}".format(
                        self.node, self.pool, new_state)
        else:
            if self.module.check_mode:
                self.msg = "Add and set {0} in {1} to {2}".format(
                        self.node, self.pool, new_state)
                self.changed = True
                return

            new_nodes = self._nodes()+[{'node': self.node, 'state': new_state}]
            response = self.set_nodes(new_nodes)

            if response.status_code == 200:
                self.changed = True
                self.msg = "Added and set {0} in {1} to {2}".format(
                        self.node, self.pool, new_state)
                self.pool_data = json.loads(response.text)
            else:
                self.module.fail_json(msg=
                    "Failed to add and set {0} in {1} to {2} - got HTTP {4} \
                    from server".format(self.node, self.pool, new_state,
                                        response.status_code))

    def set_disabled(self):
        self.set_state('disabled')

    def set_enabled(self):
        self.set_state('active')

    def set_draining(self):
        self.set_state('draining')


def main():
    module = AnsibleModule(
            argument_spec = dict(
                name      = dict(required=True, aliases=['node']),
                pool      = dict(required=True),
                state     = dict(choices=['absent','present','disabled','enabled','draining'],
                                 required=False,
                                 default='present'),
                server    = dict(required=True),
                port      = dict(default=9070, required=False),
                timeout   = dict(default=3, required=False),
                user      = dict(required=True),
                password  = dict(required=True),
            ),
            supports_check_mode = True,
    )

    server     = module.params['server']
    port       = module.params['port']
    timeout    = module.params['timeout']
    user       = module.params['user']
    password   = module.params['password']
    pool       = module.params['pool']
    node       = module.params['name']
    state      = module.params['state']

    stingray_node = StingrayNode(module, server, port, timeout, user, password, pool, node)

    try:
        if state == 'present':
            stingray_node.set_present()
        elif state == 'enabled':
            stingray_node.set_enabled()
        elif state == 'absent':
            stingray_node.set_absent()
        elif state == 'disabled':
            stingray_node.set_disabled()
        elif state == 'draining':
            stingray_node.set_draining()

        module.exit_json(changed=stingray_node.changed, msg=stingray_node.msg, data=stingray_node.pool_data)
    except Exception as e:
        module.fail_json(msg=str(e))


from ansible.module_utils.basic import *
if __name__ == '__main__':
    main()
