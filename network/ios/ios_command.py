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
module: ios_command
version_added: "2.0"
author: "Peter Sprygada (@privateip)"
short_description: Send and receive ios commands over ssh to Cisco devices
description:
  - Sends and receives ios commands using ssh over a SSH transport.  This
    module supports sending either a single command or an ordered set of
    the remote host.
notes:
  - Supports additional arguments via the ssh shared modules.  See
    module_utils/ssh.py for details.
options:
  command:
    description:
      - Sends a single command over ssh and returns the results.  The
        command is any valid ios command that the user is allowed to
        execute.  This argument is mutually exclusive with the
        C(commands) argument
    required: false
    default: null
  commands:
    description:
      - Sends a block of commands to the remote host over ssh.  The
        commands are listed in order.  This argument is mutually
        exclusive with C(command)
    type: list
    required: false
    default: null
"""

EXAMPLES = """
# Note: These examples do not set ssh parameters, see module_utils/ssh.py

# send a single command and return its result
- ios_command:
    command: "show version"

# send multiple commands and return the results
- ios_command:
    commands:
      - "show version"
      - "show ip route"
"""

RETURN = """
stdout:
  description: The responses generated from the device based on the command
  returned: always
  type: list
  sample: [...]

stdout_lines:
  description: The responses generated from the device based on the command
    split into a list at the line end
  returned: always
  type: list
  sample: [[...], [...]]
"""

def main():

    spec = dict(
        command=dict(),
        commands=dict(type='list')
    )
    mutually_exclusive = [('command','commands')]

    module = ios_module(argument_spec=spec,
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
