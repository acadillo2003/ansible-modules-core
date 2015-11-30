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
module: ios_config
version_added: "2.0"
author: "Peter Sprygada (@privateip)"
short_description: Send and receive ios configuration commands over ssh
description:
  - Sends and receives ios configuration commands using ssh over a
    SSH transport.  This module supports sending either a single
    command or an ordered set of the remote host.
notes:
  - Supports additional arguments via the ssh shared modules.  See
    module_utils/ssh.py for details.
options:
  line:
    description:
      - The configuration line in the device configuration that should be
        present  The current node configuration is evaluated and if
        the line is not found it will be added
    required: false
    default: null
  block:
    description:
      - The block of configuration to apply to the node.  Use block
        to configure more than one line statement.  For each line
        in the block, the configuration is evaluated and missing lines
        are added to the configuration based on the C(strategy).  The
        C(block) and C(line) arguments are mutually exclusive.
    type: list
    required: false
    default: null
  parent:
    description:
      - The configuration parent for the C(line) or C(block).  The
        C(parent) argument is a one line configuration statement
        for entering sub mode configuration commands.  It is mutually
        exclusive with C(ancestors).  See EXAMPLES for details.
    required: false
    default: null
  ancestors:
    description:
      - The ancestors of the block or line of configuration.  The
        C(ancestors) argument allows for nested configuration options and
        is mutually exclusive with C(parent).  See EXAMPLES for details.
    type: list
    required: false
    default: null
  before_block:
    description:
      - A set of configuration commands to execute before the block.  The
        C(before_block) is execute if and only if the commands in either
        C(line) or C(block) trigger a configuration change.
    required: false
    default: null
  after_block:
    description:
      - a set of configuration commands to execute after the block.  This
        argument is the same as C(before_block) only it is configured
        once the C(block) statements are completed
    required: false
    default: null
  strategy:
    description:
      - Specifies the strategy to use to install a block of configuration
        on the node.  By default the config block is evaluated against
        the current nodes configuration.  Any line that doesn't match
        is added to the config.  If the value is set to C(all) will cause
        the entire block to be applied if any line is not in the current
        config.  Finally setting the value to C(force) will not evalue
        the current config and simply configure the node with the block.
    required: false
    default: changed
    choices: ['changed', 'all', 'force']
  config:
    description:
      - Overrides the device configuration file with this value.  By
        default, this module will attach to the node to collect the current
        running-config.  Using this argument will override that behavior
        and validate the configuration passed
    required: false
    default: null
  config_file:
    description:
      - The path to the device configuration for offline access to the
        configuration file.  This option is the same as the C(config)
        option only it will read the config contents from a file.  The
        C(config) and C(config_file) arguments are mutually exclusive
    required: false
    default: null
"""

EXAMPLES = """
# Note: These examples do not set ssh parameters, see module_utils/ssh.py

# make a simple configuration change
- ios_config:
    line: "hostname switch"
# configure an interface block
- ios_config:
    block:
      - "description example config block"
      - "ip address 1.1.1.1/32"
      - "no shutdown"
    parent: "interface loopback0"

# configure an access list.  this example will evalue the current
# configuration and if any statement doesn't match in the acl
# it will remove the acl (the before_block)  and reconfigured
# it with statements in block
- ios_config:
    block:
      - "10 permit ip 172.30.10.0/24 any"
      - "20 permit ip 172.30.11.0/24 any"
      - "30 permit ip 172.30.12.0/24 any"
      - "40 permit ip 172.30.13.0/24 any"
    parent: "ip access-list example"
    before_block:
      - "no ip access-list example"
    strategy: all

# use ancestors to configure nested commands
- ios_config:
    block:
      - "remote-as 65000"
      - "update source loopback0"
    ancestors: ["router bgp 65000", "neighbor 1.1.1.1"]
"""

RETURN = """
commands:
  description: The list of commands used to configure the device
  returned: success
  type: list
  sample: "[{ ... }]"
"""

import re
import collections

def parse(config, indent=1):
    regexp = re.compile(r'^\s*(.+)$')
    line_re = re.compile(r'\S')
    invalid_re = re.compile(r'^(!|end)')

    ancestors = list()
    data = dict()
    #data = collections.OrderedDict()
    banner = False

    for line in config:
        text = str(line).strip()

        if not invalid_re.match(text):

            # handle top level commands
            if line_re.match(line):
                data[text] = dict()
                ancestors = [text]

            # handle sub level commands
            else:
                match = regexp.match(line)
                if match:
                    line_indent = match.start(1)
                    level = line_indent / indent

                    try:
                        ancestors[level] = text
                    except IndexError:
                        ancestors.append(text)

                    try:
                        child = data[ancestors[0]]
                        for a in ancestors[1:level]:
                            child = child[a]
                        child[text] = dict()
                    except KeyError:
                        # FIXME deal with indent inconsistencies
                        if '_errors' not in data:
                            data['_errors'] = list()
                        data['_errors'].append((ancestors, text))

    return data

def to_list(arg):
    if isinstance(arg, (list, tuple)):
        return list(arg)
    elif arg is not None:
        return [arg]
    else:
        return

def get_config(conn, module):
    config = module.params['config']
    if not config:
        cmd = 'show running-config'
        if module.params['include_all']:
            cmd += ' all'
        config = conn.send('show running-config all')[0]
    return config or list()

def load_config(module):
    try:
        filename = module.params['config_file']
        return open(filename).read()
    except IOError, exc:
        module.fail_json(msg=exc.message)

def parse_config(config, ancestors=None):
    config = parse(str(config).split('\n'))
    if not ancestors:
        return [key for key, value in config.iteritems() if not value]

    try:
        for ancestor in ancestors:
            config = config[ancestor]
    except KeyError:
        return list()

    return config


def main():

    spec = dict(
        line=dict(),
        block=dict(type='list'),
        parent=dict(),
        ancestors=dict(type='list'),
        before_block=dict(type='list'),
        after_block=dict(type='list'),
        strategy=dict(default='changed', choices=['changed', 'all', 'force', 'exact']),
        config=dict(),
        config_file=dict(),
        enable_mode=dict(default=True, choices=[True]),
        enable_password=dict(),
        include_all=dict(default=True, type='bool')
    )
    argument_spec = ios_argument_spec(spec)
    mutually_exclusive = [('parent', 'ancestors'), ('config', 'config_file')]
    required_one_of = ios_required_one_of([('line', 'block')])

    module = AnsibleModule(argument_spec=argument_spec,
                           mutually_exclusive=mutually_exclusive,
                           required_one_of=required_one_of,
                           supports_check_mode=True)

    connection = None

    before_block = module.params['before_block']
    after_block = module.params['after_block']

    line = module.params['line']
    block = module.params['block']
    if not block:
        block = [line]

    parent = module.params['parent']
    ancestors = module.params['ancestors']
    if not ancestors and parent:
        ancestors = [parent]

    candidate = (ancestors, block)
    if module.params['strategy'] == 'force':
        config = list()
    else:
        if module.params['config_file']:
            contents = load_config(module)
        else:
            connection = ios_connection(module)
            contents = get_config(connection, module)
        config = parse_config(contents, ancestors)

    result = dict(changed=False)

    if module.params['strategy'] == 'exact':
        cmds = list(set(block).intersection(config))
        commands = list(set(block).difference(cmds))
    else:
        commands = list(set(block).difference(config))

    if commands and module.params['strategy'] == 'all':
        commands = block

    if commands:
        if ancestors:
            commands[:0] = ancestors

        if before_block:
            commands[:0] = before_block

        if after_block:
            commands.extend(after_block)

        if not module.check_mode:
            if not connection:
                connection = ios_connection(module)

            try:
                response = connection.configure(commands)
            except ShellError, exc:
                return module.fail_json(msg=exc.message, command=exc.command)

        result['changed'] = True

    result['commands'] = commands
    return module.exit_json(**result)


from ansible.module_utils.basic import *
from ansible.module_utils.ssh import *
from ansible.module_utils.ios import *

if __name__ == '__main__':
    main()
