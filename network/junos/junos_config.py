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
module: junos_config
version_added: "2.1"
author: "Peter sprygada (@privateip)"
short_description: Manage Juniper JUNOS device configurations
description:
  - Manages network device configurations over SSH.  This module
    allows implementors to work with the device configuration.  It
    provides a way to push a set of commands onto a network device
    by evaluting the current configuration and only pushing
    commands that are not already configured.
extends_documentation_fragment: junos
options:
  src:
    description:
      - The path to the config source.  The source can be either a
        file with config or a template that will be merged during
        runtime.  By default the task will search for the source
        file in role or playbook root folder in templates directory.
    required: false
    default: null
  force:
    description:
      - The force argument instructs the module to not consider the
        current devices configuration.  When set to true, this will
        cause the module to push the contents of I(src) into the device
        without first checking if already configured.
    required: false
    default: false
    choices: BOOLEANS
  backup:
    description:
      - When this argument is configured true, the module will backup
        the configuration from the node prior to making any changes.
        The backup file will be written to backup_{{ hostname }} in
        the root of the playbook directory.
    required: false
    default: false
    choices: BOOLEANS
  encoding:
    description:
      - Specifies the type of encoding used in the source template.  Junos
        configuraiton templates can be evaluated as either I(block)
        configurations or I(line) configurations.  Block configurations are
        the default way to represent the configuration using the standard
        curly brace ({ or }) notation.  The other mechanism is to use single
        lines as I(set) or I(delete).
    required: false
    default: block
    choices: ['block', 'line']
  config:
    description:
      - The module, by default, will connect to the remote device and
        retrieve the current configuration to use as a base for comparing
        against the contents of source.  There are times when it is not
        desirable to have the task get the current configuration for
        every task in a playbook.  The I(config) argument allows the
        implementer to pass in the configuruation to use as the base
        config for comparision.
    required: false
    default: null
"""

EXAMPLES = """

- name: push a configuration onto the device
  junos_config:
    src: config.j2

- name: forceable push a configuration onto the device
  junos_config:
    src: config.j2
    force: yes

- name: provide the base configuration for comparision
  junos_config:
    src: candidate_config.txt
    config: current_config.txt

"""

RETURN = """

commands:
  description: The set of commands that will be pushed to the remote device
  returned: always
  type: list
  sample: [...]

"""

def compare(this, other):
    parents = [item.text for item in this.parents]
    for entry in other:
        if this == entry:
            return None
    return this

def expand(obj, action='set'):
    cmd = [action]
    cmd.extend([p.text for p in obj.parents])
    cmd.append(obj.text)
    return ' '.join(cmd)

def flatten(data, obj):
    for k, v in data.items():
        obj.append(k)
        flatten(v, obj)
    return obj

def get_config(module):
    config = module.params['config'] or dict()
    if not config and not module.params['force']:
        config = module.config
    return config

def main():
    """ main entry point for module execution
    """

    argument_spec = dict(
        src=dict(),
        encoding=dict(default='block', choices=['block', 'line']),
        force=dict(default=False, type='bool'),
        backup=dict(default=False, type='bool'),
        config=dict(),
    )

    mutually_exclusive = [('config', 'backup'), ('config', 'force')]

    module = get_module(argument_spec=argument_spec,
                        mutually_exclusive=mutually_exclusive,
                        supports_check_mode=True)

    encoding = module.params['encoding']

    result = dict(changed=False)

    if encoding == 'line':
        candidate = list()
        for item in str(module.params['src']).split('\n'):
            if item and not item.startswith('#'):
                candidate.append(item)
    else:
        candidate = module.parse_config(module.params['src'])

    contents = get_config(module)
    result['_backup'] = module.config

    config = module.parse_config(contents)

    lines = list()
    for line in config:
        if line.raw.endswith(';'):
            lines.append(expand(line))

    commands = list()

    if encoding == 'line':
        for line in candidate:
            action = line.split()[0]
            if action == 'set':
                if line not in lines:
                    commands.append(line)
            elif action == 'delete':
                if line in lines:
                    commands.append(line)
    else:
        toplevel = [c.text for c in config]

        for line in candidate:
            if not line or line.text[0] == '#':
                continue

            if not line.parents:
                if line.text not in toplevel and line.raw.endswith(';'):
                    commands.append(line)
            else:
                item = compare(line, config)
                if item and item.raw.endswith(';'):
                    commands.append(item)

        commands = [expand(c) for c in commands]

    if commands:
        if not module.check_mode:
            module.configure(commands)
        result['changed'] = True

    result['commands'] = commands
    return module.exit_json(**result)


from ansible.module_utils.basic import *
from ansible.module_utils.shell import *
from ansible.module_utils.netcfg import *
from ansible.module_utils.junos import *
if __name__ == '__main__':
    main()

