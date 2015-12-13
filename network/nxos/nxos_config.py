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
module: nxos_config
version_added: "2.0"
author: "Peter Sprygada (@privateip)"
short_description: Send and receive NXOS configuration commands over NXAPI
description:
  - Sends and receives NXOS configuration commands using NXAPI over a
    HTTP/S transport.  This module supports sending either a single
    command or an ordered set of the remote host.  This module
    requires that NXAPI support has been enabled on the device.
notes:
  - Supports additional arguments via the NXAPI shared modules.  See
    module_utils/nxapi.py for details.
options:
  line:
    description:
      - The configuration line in the device configuration that should be
        present  The current node configuration is evaluated and if
        the line is not found it will be added
    required: false
    default: null
  replace:
    description:
      - The value for the replace argument will be inserted into the
        current nodes running configuraiton if the value of C(line) is
        not found.  The C(replace) argument is mutually exclusive with the
        C(block) argument
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
  match:
    description:
      - Specifies the match strategy to use when evaluting a block of
        configuration from the node.  By default, the match strategy is
        configured to evaluate a line and if the line isn't present it
        will be added to the config.  If the match strategy is set to
        block, the entire block is added to the configuration if any line
        is invalid.  If the match strategy is set of exact, the config
        block must match exactly. Finally setting the value to C(force)
        will not evalue the current config and simply configure the node
        with the block.
    required: false
    default: line
    choices: ['line', 'block', 'exact', 'force]
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
  offline:
    description:
      - This flag controls if the module runs in online or offline mode.  When
        in online mode, the module will connect to the device to get the
        config and push config changes.  When in offline mode, the module
        expects the config or config_file argument to provided and it
        generates a list of commands in the result
    required: false
    default: false
"""

EXAMPLES = """
# Note: These examples do not set nxapi parameters, see module_utils/nxapi.py

# make a simple configuration change
- nxos_config:
    line: "hostname switch"

# configure an interface block
- nxos_config:
    block:
      - "description example config block"
      - "ip address 1.1.1.1/32"
      - "no shutdown"
    parent: "interface loopback0"

# configure an access list.  this example will evalue the current
# configuration and if any statement doesn't match in the acl
# it will remove the acl (the before_block)  and reconfigured
# it with statements in block
- nxos_config:
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
- nxos_config:
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

config:
  description: The block extracted from the running-config
  returned: success
  type: list
  sample: "[...]"

"""
import re
import collections

def parse(config, indent=2):
    regexp = re.compile(r'^\s*(.+)$')
    line_re = re.compile(r'\S')
    invalid_re = re.compile(r'^(!|end)')

    ancestors = list()
    data = collections.OrderedDict()
    banner = False

    for line in config:
        text = str(line).strip()

        # TODO: add support for parsing banners
        if not invalid_re.match(text):

            # handle top level commands
            if line_re.match(line):
                data[text] = collections.OrderedDict()
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
                        child[text] = collections.OrderedDict()
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
        return []

def get_config(module):
    config = module.params['config']
    if not config:
        cmd = 'show running-config'
        if  module.params['all']:
            cmd += ' all'
        config = nxapi_command(module, cmd)
        config = config[0]['ins_api']['outputs']['output']['body']
    return config or dict()

def load_config(module):
    try:
        filename = module.params['config_file']
        return open(filename).read()
    except IOError, exc:
        return module.fail_json(msg=exc.strerror, errno=exc.errno)

def parse_config(config, ancestors=None):
    config = parse(str(config).split('\n'))
    try:
        for ancestor in ancestors:
            config = config[ancestor]
    except KeyError:
        return dict()
    except TypeError:
        pass
    return config

def match_re(pattern, values):
    regexp = re.compile(r'%s' % pattern)
    for value in values:
        match = regexp.search(value)
        if match:
            return match

def apply_positional(value, match):
    if match is None:
        return value
    # TODO: trap IndexError
    for v in re.findall(r"\\\d+", value):
        index = int(v.replace('\\', ''))
        val = match.group(index)
        value = value.replace(v, val)
    return value

def apply_named(values, matches):
    for value in values:
        for match in matches:
            if match:
                value = value.format(**match.groupdict())
        yield value


def main():

    spec = dict(
        line=dict(),
        replace=dict(),
        block=dict(type='list'),
        block_replace=dict(type='list'),
        parent=dict(),
        ancestors=dict(type='list'),
        before_block=dict(type='list'),
        after_block=dict(type='list'),
        match=dict(default='line', choices=['line', 'block', 'force']),
        config=dict(),
        config_file=dict(),
        include_all=dict(default=True, type='bool'),
        offline=dict(default=False, type='bool'),
        state=dict(default='present', choices=['present', 'absent'])
    )

    required_one_of = [('line', 'block')]
    mutually_exclusive = [('parent', 'ancestors'), ('config', 'config_file'),
                          ('block', 'replace'), ('line', 'block')]

    module = nxapi_module(argument_spec=spec,
                          mutually_exclusive=mutually_exclusive,
                          required_one_of=required_one_of,
                          supports_check_mode=True)

    offline = module.params['offline']
    if offline:
        if not module.params['config'] and not module.params['config_file']:
            module.fail_json(msg='config or config_file must be specified '
                                 'when offline is enabled')
    else:
        if not module.params['host'] and not module.params['device']:
            module.fail_json(msg='host or device argument must be specified '
                                 'when using module in online mode')

    before_block = module.params['before_block']
    after_block = module.params['after_block']

    line = module.params['line']
    block = module.params['block'] or [line]

    replace = module.params['replace']

    parent = module.params['parent']
    ancestors = module.params['ancestors']
    if not ancestors and parent:
        ancestors = [parent]

    replace = module.params['replace']
    block_replace = module.params['block_replace']
    if not block_replace and replace:
        block_replace = [replace]
    elif not block_replace:
        block_replace = list(block)

    parent = module.params['parent']
    ancestors = module.params['ancestors']
    if not ancestors and parent:
        ancestors = [parent]

    if module.params['config_file']:
        contents = load_config(module)
    else:
        contents = get_config(module)
    config = parse_config(contents, ancestors)
    config = config.keys()

    result = dict(changed=False)
    commands = list()
    matches = list()

    for cmd, replace in zip(block, block_replace):
        match = match_re(cmd, config)
        matches.append(match)
        if (not match and module.params['state'] == 'present') or \
           (match and module.params['state'] == 'absent') or \
           (module.params['match'] == 'force'):
            commands.append(apply_positional(replace, match))

    if commands:
        if ancestors:
            commands[:0] = ancestors

        if before_block:
            commands[:0] = before_block

        if after_block:
            commands.extend(after_block)

        if not module.check_mode and not offline:
            response = nxapi_command(module, commands, 'cli_conf')
            output = to_list(response[0]['ins_api']['outputs']['output'])
            for resp in output:
                if int(resp['code']) != 200:
                    module.fail_json(**resp)

        result['changed'] = True

    result['commands'] = commands
    return module.exit_json(**result)


from ansible.module_utils.basic import *
from ansible.module_utils.urls import *
from ansible.module_utils.nxapi import *

if __name__ == '__main__':
    main()
