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
module: nxos_command
version_added: "2.0"
author: "Peter Sprygada (@privateip)"
short_description: Send and receive NXOS commands over NXAPI to Cisco devices
description:
  - Sends and receives NXOS commands using NXAPI over a HTTP/S transport.  This
    module supports sending either a single command or an ordered set of
    the remote host.  This module requires that NXAPI support has been enabled
    on the device.
notes:
  - Supports additional arguments via the NXAPI shared modules.  See
    module_utils/nxapi.py for details.
options:
  command:
    description:
      - Sends a single command over NXAPI and returns the results.  The
        command is any valid NXOS command that the user is allowed to
        execute.  This argument is mutually exclusive with the
        C(commands) argument
    required: false
    default: null
  commands:
    description:
      - Sends a block of commands to the remote host over NXAPI.  The
        commands are listed in order.  This argument is mutually
        exclusive with C(command)
    type: list
    required: false
    default: null
  encoding:
    description:
      - The type of command response to return from the node.  By default
        commands are returned in JSON format.  Setting this value to C(text)
        will return the value as in text.
    required: false
    default: json
    choices: ['json', 'text']
"""

EXAMPLES = """
# Note: These examples do not set nxapi parameters, see module_utils/nxapi.py

# send a single command and return its result
- nxos_command:
    command: "show version"

# send multiple commands returning them in text format
- nxos_command:
    commands:
      - "show version"
      - "show ip route"
    encoding: text

"""

RETURN = """

response:
  description: The response generated from the device based on the command
  returned: always
  type: list
  sample: [...]

"""

ENCODINGS = {'json': 'cli_show', 'text': 'cli_show_ascii'}

def main():
    spec = dict(
        command=dict(),
        commands=dict(type='list'),
        encoding=dict(default='json', choices=ENCODINGS.keys())
    )

    mutually_exclusive = [('command', 'commands')]
    required_one_of = [('command', 'commands')]

    module = nxapi_module(argument_spec=spec,
                          mutually_exclusive=mutually_exclusive,
                          required_one_of=required_one_of)

    commands = module.params['commands'] or module.params['command']
    command_type = ENCODINGS.get(module.params['encoding'])

    response, headers = nxapi_command(module, commands, command_type)
    response = response['ins_api']['outputs']['output']

    result = dict(changed=False, response=response)
    return module.exit_json(**result)


from ansible.module_utils.basic import *
from ansible.module_utils.urls import *
from ansible.module_utils.nxapi import *

if __name__ == '__main__':
    main()
