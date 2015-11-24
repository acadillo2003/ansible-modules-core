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


def main():

    spec = dict(
        command=dict(),
        commands=dict(type='list')
    )
    argument_spec = ios_argument_spec(spec)

    mutually_exclusive = [('command','commands')]

    module = AnsibleModule(argument_spec=argument_spec,
                           mutually_exclusive=mutually_exclusive)

    command = module.params['command']
    commands = module.params['commands'] or command

    connection = ios_connection(module)

    try:
        response = connection.send(commands)
    except ShellError, exc:
        return module.fail_json(msg=exc.message, command=exc.command)

    stdout_lines = [str(s).split('\n') for s in response]

    result = dict(changed=False, stdout=response, stdout_lines=stdout_lines)
    return module.exit_json(**result)


from ansible.module_utils.basic import *
from ansible.module_utils.ssh import *
from ansible.module_utils.ios import *

if __name__ == '__main__':
    main()
