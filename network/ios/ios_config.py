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
"""

EXAMPLES = """
"""

RETURN = """
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
