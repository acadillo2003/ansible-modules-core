#!/usr/bin/python
#
# This file is part of Ansible
#
# Ansible is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Ansible is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Ansible.  If not, see <http://www.gnu.org/licenses/>.
#
DOCUMENTATION = """
---
module: ops_config
verions_added: "2.1"
author: "Peter Sprygada (@privateip)"
short_description: Push configuration to OpenSwitch using declarative config
description:
  - The OpenSwitch platform provides a library for pushing JSON structured
    configuration files into the current running-config.  This module
    will read the current configuration from OpenSwitch and compare it
    against a provided candidate configuration. If there are changes, the
    candidate configuration is merged with the current configuration and
    pushed into OpenSwitch
options:
  src:
    description:
      - The candidate configuration to evaluate.  The src argument should
        be the configuration to be used as the candidate configuration and
        evalutated against the current running configuration from the
        device.
    required: true
"""

EXAMPLES = """
# Pushes the candidate configuraition to the device using a variable

vars:
  config:
    System
      hostname: ops01

tasks:
  - ops_config:
      src: "{{ config }}"

# Reads the candidate configuration from a file

tasks:
  - ops_config:
      src: "{{ lookup('file', 'ops_config.json') }}"
"""

RETURN = """
updates:
  description: The list of configuration updates to be merged  The format
    of the return is 'key: new_value (old_value)'
  retured: always
  type: list
  sample: ["System.hostname: ops01 (switch)"]
"""
import time

from runconfig import runconfig
from opsrest.settings import settings
from opsrest.manager import OvsdbConnectionManager
from opslib import restparser

def get_idl():
    manager = OvsdbConnectionManager(settings.get('ovs_remote'),
                                     settings.get('ovs_schema'))
    manager.start()
    idl = manager.idl

    init_seq_no = 0
    while (init_seq_no == idl.change_seqno):
        idl.run()
        time.sleep(1)

    return idl

def get_schema():
    return restparser.parseSchema(settings.get('ext_schema'))

def sort(val):
    if isinstance(val, (list, set)):
        return sorted(val)
    return val

def diff(this, other, path=None):
    updates = list()
    path = path or list()
    for key, value in this.items():
        if key not in other:
            other_value = other.get(key)
            updates.append((list(path), key, value, other_value))
        else:
            if isinstance(this[key], dict):
                path.append(key)
                updates.extend(diff(this[key], other[key], list(path)))
                path.pop()
            else:
                other_value = other.get(key)
                if sort(this[key]) != sort(other_value):
                    updates.append((list(path), key, value, other_value))
    return updates

def merge(changeset, config=None):
    config = config or dict()
    for path, key, value, _ in changeset:
        current_level = config
        for part in path:
            if part not in current_level:
                current_level[part] = dict()
            current_level = current_level[part]
        current_level[key] = value
    return config


def main():

    argument_spec = dict(
        src=dict()
    )

    module = AnsibleModule(argument_spec=argument_spec,
                           supports_check_mode=True)

    src = module.params['src']

    idl = get_idl()
    schema = get_schema()

    run_config_util = runconfig.RunConfigUtil(idl, schema)
    config = run_config_util.get_running_config()

    result = dict(changed=False)

    changeset = diff(src, config)
    candidate = merge(changeset, config)

    updates = list()
    for path, key, new_value, old_value in changeset:
        update = '%s.%s' % ('.'.join(path), key)
        update += ': %s (%s)' % (new_value, old_value)
        updates.append(update)
    result['updates'] = updates

    if changeset:
        if not module.check_mode:
            run_config_util.write_config_to_db(config)
        result['changed'] = True

    module.exit_json(**result)

from ansible.module_utils.basic import *
if __name__ == '__main__':
        main()


