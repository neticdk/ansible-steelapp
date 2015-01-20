#!/usr/bin/python
# -*- coding: utf-8 -*-

import json
import requests

DOCUMENTATION = """
---
module: steelapp_pool
version_added: 1.8.2
short_description: manage steelapp pools
description:
    - Manage pools in a SteelApp Traffic Manager
author: Kim Nørgaard
options:
    name:
        description:
            - Name of pool to work on
        required: true
        default: null
        aliases: ['pool']
    state:
        description:
            - State of pool
        required: false
        default: 'present'
        choices: ['present', 'absent']
    properties:
        description:
            - Configuration hash of pool properties
        required: false
        default: {}
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
EXMPLES="""
# Create a pool
- name: Create pool
  steelapp_pool:
    name: mypool
    state: present
    server: myserver.mydomain.com
    user: myuser
    password: mypassword

# Destroy a pool
- name: Create pool
  steelapp_pool:
    name: mypool
    state: absent
    server: myserver.mydomain.com
    user: myuser
    password: mypassword

# Set properties on a pool
- name: Set note for pool
  steelapp_pool:
    name: mypool
    state: absent
    properties:
      basic:
        note: "This pool is cool"
    server: myserver.mydomain.com
    user: myuser
    password: mypassword
"""

class SteelAppPool(object):

    def __init__(self, module, server, port, timeout, user, password, pool,
                 properties):
        self.module = module
        self.server = server
        self.port = port
        self.timeout = timeout
        self.user = user
        self.password = password
        self.pool = pool
        non_empty_props = dict((k,v,) for k,v in properties.iteritems() if v is not None)
        self.properties = non_empty_props
        self.msg = ''
        self.changed = False

        self._url = 'https://{0}:{1}/api/tm/3.0/config/active/pools/{2}'
        self._url = self._url.format(server, port, pool)

        self._content_type = {'content-type': 'application/json'}

        self._client = requests.Session()
        self._client.auth = (user, password)
        self._client.verify = False

        try:
            response = self._client.get(self._url, timeout=self.timeout)
            self.exists = True
        except requests.exceptions.ConnectionError as e:
            self.module.fail_json(
                msg="Unable to connect to {0}: {1}".format(self._url, str(e)))

        if response.status_code == 404:
            self.exists = False

        try:
            self.pool_data = json.loads(response.text)
        except Exception as e:
            self.module.fail_json(msg=str(e))

        if 'error_id' in self.pool_data:
            self.module.fail_json(msg=self.pool_data)

    def _pool_changes(self, new_pool, current_pool, parent=''):
        """Recursively compare new_pool to current_pool."""
        changes=[]
        for k in new_pool.keys():
            if current_pool.get(k, None) is None:
                continue
            if type(new_pool[k]) == type({}):
                changes.extend(self._pool_changes(new_pool[k],
                               current_pool[k], k))
            else:
                if new_pool[k] != current_pool[k]:
                    if parent=='':
                        changes.append({
                            k: {
                                'before': current_pool[k],
                                'after': new_pool[k]
                            }})
                    else:
                        changes.append({
                            "{0}.{1}".format(parent,k): {
                                'before': current_pool[k],
                                'after': new_pool[k]
                            }})
        return changes


    def set_absent(self):
        self.changed = False
        changes = { 'pool': self.pool }

        if self.exists:
            self.changed = True
            changes['action'] = 'destroy_pool'
            self.msg = changes

            if self.module.check_mode: return

            try:
                response = self._client.delete(self._url)
            except Exception as e:
                self.module.fail_json(msg=str(e))

            if response.status_code != 204:
                changes['error'] = response.text
                self.module.fail_json(msg=changes)
        else:
            self.changed = False
            self.msg = changes


    def set_present(self):
        self.changed = False
        changes = { 'pool': self.pool }

        if not self.exists:
            self.changed = True
            changes['action'] = 'create_pool'
            self.msg = changes

            if self.module.check_mode: return

            if self.properties:
                new_pool = {'properties': self.properties}
            else:
                new_pool = {'properties': {'basic': {}}}

            try:
                response = self._client.put(
                    self._url, data=json.dumps(new_pool),
                    headers=self._content_type)
            except Exception as e:
                self.module.fail_json(msg=str(e))

            if response.status_code == 201:
                self.pool_data = json.loads(response.text)
            else:
                changes['error'] = response.text
                self.module.fail_json(msg=changes)
        else:
            self.msg = changes

            changes = self._pool_changes(self.properties, self.pool_data['properties'])
            if len(changes): self.changed = True

            self.msg = changes

            if self.module.check_mode: return

            if self.changed:
                new_pool = {'properties': self.properties}

                try:
                    response = self._client.put(
                        self._url, data=json.dumps(new_pool),
                        headers=self._content_type)
                    print response
                except Exception as e:
                    self.module.fail_json(msg=str(e))

                if response.status_code == 200:
                    self.pool_data = json.loads(response.text)
                else:
                    self.module.fail_json(msg=changes)


def main():
    module = AnsibleModule(
        argument_spec = dict(
            name = dict(required=True, aliases=['pool']),
            state = dict(choices=['absent','present'],
                         required=False,
                         default='present'),
            properties = dict(required=False, default={}),
            server = dict(required=True),
            port = dict(default=9070, required=False),
            timeout = dict(default=3, required=False),
            user = dict(required=True),
            password  = dict(required=True),
        ),
        supports_check_mode = True,
    )

    state = module.params['state']
    server = module.params['server']
    port = module.params['port']
    timeout = module.params['timeout']
    user = module.params['user']
    password = module.params['password']
    pool = module.params['name']
    properties = module.params['properties']

    steelapp_pool = SteelAppPool(
        module, server, port, timeout, user, password, pool, properties)

    try:
        if state == 'present':
            steelapp_pool.set_present()
        elif state == 'absent':
            steelapp_pool.set_absent()
        else:
            module.fail_json(msg="Unsupported state: {0}".format(state))

        module.exit_json(changed=steelapp_pool.changed, msg=steelapp_pool.msg,
                         data=steelapp_pool.pool_data)
    except Exception as e:
        module.fail_json(msg=str(e))

from ansible.module_utils.basic import *
if __name__ == '__main__':
    main()
