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

def get_config(conn, module):
    config = module.params['config'] or dict()
    if not config and not module.params['force']:
        cmd = 'show running-config'
        if module.params['include_all']:
            cmd += ' all'
        resp = conn.send(cmd)
        config = resp[0]
    return config

def backup_config(config, module):
    host = module.params['cli_host']
    open('backup_%s' % host, 'w').write(config)

def on_connect(conn, module):
    conn.send('terminal length 0')
    if module.params['cli_authorize']:
        conn.authorize(module.params['cli_auth_pass'])

def on_configure(conn):
    conn.send('configure terminal')

def main():

    argument_spec = dict(
        src=dict(),
        backup=dict(default=False, type='bool'),
        force=dict(default=False, type='bool'),
        replace=dict(default=False, type='bool'),
        include_all=dict(default=True, type='bool'),
        config=dict()
    )

    mutually_exclusive = [('config', 'backup'), ('config', 'force')]

    module = cli_module(argument_spec=argument_spec,
                        mutually_exclusive=mutually_exclusive,
                        supports_check_mode=True)

    connection = cli_connection(module)

    src = module.params['src']
    force = module.params['force']
    backup = module.params['backup']
    replace = module.params['replace']

    candidate = parse(src, indent=1)

    contents = get_config(connection, module)
    config = parse(contents, indent=1)

    if backup and not module.check_mode:
        backup_config(contents, module)

    result = dict(changed=False)

    commands = collections.OrderedDict()
    toplevel = [c.text for c in config]

    for line in candidate:
        if line.text in ['!', '']:
            continue

        if not line.parents:
            if line.text not in toplevel:
                expand(line, commands)
        else:
            item = compare(line, config)
            if item:
                expand(item, commands)

    commands = flatten(commands, list())

    if commands:
        if not module.check_mode:
            try:
                commands = [str(c).strip() for c in commands]
                response = connection.configure(commands)
            except ShellError, exc:
                return module.fail_json(msg=exc.message, command=exc.command)
        result['changed'] = True

    result['commands'] = commands
    return module.exit_json(**result)


from ansible.module_utils.basic import *
from ansible.module_utils.issh import *
from ansible.module_utils.cli import *
from ansible.module_utils.net_config import *
if __name__ == '__main__':
    main()

