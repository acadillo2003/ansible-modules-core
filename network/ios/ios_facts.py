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
module: ios_facts
version_added: "2.0"
author: "Peter Sprygada (@privateip)"
short_description: Collects fact information from an ios node over SSH
description:
  - Collects predetermined fact information from an ios node.
notes:
  - Supports additional arguments via the ssh shared modules.  See
    module_utils/ssh.py for details.
options:
  include_neighbors:
    description:
      - Collects the current set of CDP (or LLDP) neighbors from
        the target device.  Setting this argument to True will
        instruct it to collect the neighbors.  By default it will
        attempt to collect CDP information
    required: false
    default: true
    choices: BOOLEANS
  commands:
    description:
      - Adds an additional list of commands to collect from the
        target device.  The list of commands will be returned in
        the response.
      - Note: This should not be used for configuring the device.
    required: false
    default: []
  use_lldp:
    description:
      - By default, the ios_facts module will collect neighbor
        output using CDP.  This argument will instruct the module
        to collect LLDP information instead.
    required: false
    default: false
    choices: BOOLEANS
  use_config_all:
    description:
      - By default, the facts module will issue the command 'show
        running-config all' on the target host when include_config is
        true.  Some older versions of IOS do not support the all keyword.
        This parameter will change the behavior to drop the all keyword
        from the command issued
    required: false
    default: false
    choices: BOOLEANS
  include_interfaces:
    description:
      - Instructs the module to either collect or not collect
        interface details from the target host.  Collection of
        interface details is on by default
    required: false
    default: true
    choices: BOOLEANS
  include_routing:
    description:
      - Informs the ios_facts module to collect the current IP
        routing table from the target device.  This feature is
        enabled by default.  To disable it, set the value to False
    required: false
    default: true
    choices: BOOLEANS
  include_vlans:
    description:
      - Informs the ios_facts module to collect the set of VLANs
        from the current device configuration.  Tis feature is enabled
        by default.
    required: false
    default: true
    choices: BOOLEANS
  include_config:
    description:
      - By default, the module does not collect the current nodes
        running configuration.  Setting this argument to True will
        instruct it to collect the running-config
    required: false
    default: true
    choices: BOOLEANS
"""

EXAMPLES = """
# Note: These examples do not set ssh parameters, see module_utils/ssh.py

# collect facts from device
- ios_facts:
    include_neighbors: yes
    include_interfaces: yes
    include_config: yes
"""

RETURN = """
version:
  description: Returns the output from 'show version'
  returned: success
  type: dict
  sample: "{...}"
interfaces:
  description: Returns the output from 'show interface brief'
  returned: success
  type: dict
  sample: "{...}"
config:
  description: Returns the output from 'show running-config all'
  returned: success
  type: dict
  sample: "{...}"
routing:
  description: Returns the output from 'show ip route'
  returned: success
  type: dict
  sample: "{...}"
neighbors:
  description: Returns the output from 'show cdp neighbors' or 'show lldp neighbors'
  returned: success
  type: dict
  sample: "{...}"
vlans:
  description: Returns the output from 'show vlans'
  returned: success
  type: dict
  sample: "{...}"
commands:
  description: Returns the output from a list of commands provided as arguments
  returned: when configured
  type: dict
  sample: "[{...}, {...}]"
"""

IOS_FACTS = ['vlans', 'routing', 'interfaces', 'neighbors', 'config']

def do_vlans(module):
    if module.params['include_vlans']:
        return ('vlans', 'show vlans')

def do_routing(module):
    if module.params['include_routing']:
        return ('routing', 'show ip route')

def do_interfaces(module):
    if module.params['include_interfaces']:
        return ('interfaces', 'show interfaces')

def do_neighbors(module):
    if module.params['include_neighbors']:
        if module.params['use_lldp']:
            cmd = 'show lldp neighbors'
        else:
            cmd = 'show cdp neighbors'
        return ('neighbors', cmd)

def do_config(module):
    if module.params['include_config']:
        cmd = 'show running-config'
        if module.params['use_config_all']:
            cmd += ' all'
        return ('config', cmd)

def main():
    spec = dict(
        include_vlans=dict(default=True, type='bool'),
        include_routing=dict(default=True, type='bool'),
        include_interfaces=dict(default=True, type='bool'),
        include_neighbors=dict(default=True, type='bool'),
        include_config=dict(default=False, type='bool'),
        commands=dict(type='list'),
        use_lldp=dict(default=False, type='bool'),
        use_config_all=dict(default=True, type='bool')
    )

    module = AnsibleModule(argument_spec=spec,
                           supports_check_mode=False)

    commands = dict(version='show version')
    for fact in IOS_FACTS:
        func = globals().get('do_%s' % fact)
        if func:
            cmd = func(module)
            if cmd:
                commands[cmd[0]] = cmd[1]

    connection = ios_connection(module)
    response = connection.send(commands.values())

    ios_facts = dict()
    for (key, cmd), resp in zip(commands.items(), response):
        ios_facts[key] = resp

    if module.params['include_config']:
        if not module.params['enable_mode']:
            msg = 'enable_mode must be true if include_config is true'
            return module.fail_json(msg=msg)
        cmd = 'show running-config'
        if module.params['use_config_all']:
            cmd += ' all'
        response = connection.send(cmd)
        ios_facts['config'] = response[0]

    if module.params['commands']:
        response = connection.send(module.params['commands'])
        ios_facts['commands'] = response

    ansible_facts = {'ios_facts': ios_facts}
    return module.exit_json(ansible_facts=ansible_facts)


from ansible.module_utils.basic import *
from ansible.module_utils.ssh import *
from ansible.module_utils.ios import *

if __name__ == '__main__':
    main()
