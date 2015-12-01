#!/usr/bin/python

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
module: eos_facts
version_added: "2.0"
author: "Peter Sprygada (@privateip)"
short_description: Collects fact information from an EOS node over eAPI
description:
  - Collects predetermined fact information from an EOS node.
notes:
  - Supports additional arguments via the eapi shared modules.  See
    module_utils/eapi.py for details.
options:
  include_neighbors:
    description:
      - Collects the current set of LLDP neighbors from the target
        device.  Setting this argument to True will instruct it to
        collect the neighbors.
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
      - Informs the eos_facts module to collect the current IP
        routing table from the target device.  This feature is
        enabled by default.  To disable it, set the value to False
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
# Note: These examples do not set eapi parameters, see module_utils/eapi.py

# collect facts from device
- eos_facts:
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
  description: Returns the output from 'show interfaces'
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
  description: Returns the output from 'show lldp neighbors'
  returned: success
  type: dict
  sample: "{...}"
commands:
  description: Returns the output from a list of commands provided as arguments
  returned: when configured
  type: dict
  sample: "[{...}, {...}]"
"""

EAPI_FACTS = ['version', 'interfaces', 'routing', 'neighbors', 'config']

def do_interfaces(module):
    if module.params['include_interfaces']:
        return ('interfaces', 'show interfaces')

def do_routing(module):
    if module.params['include_routing']:
        return ('routing', 'show ip route')

def do_neighbors(module):
    if module.params['include_neighbors']:
        return ('neighbors', 'show lldp neighbors')

def main():
    spec = dict(
        include_routing=dict(default=True, type='bool'),
        include_interfaces=dict(default=True, type='bool'),
        include_config=dict(default=False, type='bool'),
        include_neighbors=dict(default=True, type='bool'),
        commands=dict(type='list'),
        use_config_all=dict(default=True, type='bool')
    )

    module = eapi_module(argument_spec=spec)

    commands = dict(version='show version')
    for fact in EAPI_FACTS:
        func = globals().get('do_%s' % fact)
        if func:
            cmd = func(module)
            if cmd:
                commands[cmd[0]] = cmd[1]

    response = eapi_command(module, commands.values(), 'text')
    response = response[0]

    eos_facts = dict()

    for (key, output) in zip(commands.items(), response):
        eos_facts[key[0]] = output['output']

    if module.params['include_config']:
        if not module.params['enable_mode']:
            msg = 'enable_mode must be set to true to collect the running-config'
            module.fail_json(msg=msg)

        cmd = 'show running-config'
        if module.params['use_config_all']:
            cmd += ' all'
        response, headers = eapi_command(module, cmd, 'text')
        eos_facts['config'] = response[0]['output']

    if module.params['commands']:
        response = eapi_command(module, module.params['commands'], 'text')
        eos_facts['commands'] = response

    ansible_facts = {'eos_facts': eos_facts}
    return module.exit_json(ansible_facts=ansible_facts)


from ansible.module_utils.basic import *
from ansible.module_utils.urls import *
from ansible.module_utils.eapi import *

if __name__ == '__main__':
    main()
