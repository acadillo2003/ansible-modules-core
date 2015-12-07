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
module: eos_command
version_added: "2.0"
author: "Peter Sprygada (@privateip)"
short_description: Send and receive EOS commands over eAPI to Arista devices
description:
  - Sends and receives EOS commands using eAPI over a HTTP/S transport.  This
    module supports sending either a single command or an ordered set of
    the remote host.  This module requires that eAPI support has been enabled
    on the device.
notes:
  - Supports shared module arguments via the EAPI shared module.  See
    module_utils/eapi.py for details
  - EOS 4.14 or later
options:
  command:
    description:
      - Sends a single command to the Arista EOS node over eAPI and returns
        the response.
    required: false
    default: null
  commands:
    description:
      - Sends an ordered set of commadns to the EOS node over eAPI.  Commands
        are batch sent.  If any one command fails, the module will stop
        executing any futher commands.
    required: false
    default: null
  encoding:
    description:
      - Specifies the desired encoding for the response.  Responses from
        commands can be encoded as either C(json) or C(text).  Note: some
        EOS commands do not support JSON encoding.  All commands will be
        encoded using the same method
    required: false
    default: json
    choices: ['json', 'text']

"""

EXAMPLES = """

# Note: These examples do not set eapi parameters, see module_utils/eapi.py

# Execute the show version command on the remote host
- eos_command: command='show version'

# Execute multiple commands and return as text
- eos_command:
    commands:
      - show version
      - show ip route
    encoding: text

"""

RETURN = """

result:
  description: the output from the command run in in desired encoding
  returned: success
  type: list
  sample: "[{ ... }]"

"""

def main():
    spec = dict(
        command=dict(),
        commands=dict(type='list'),
        encoding=dict(default='json', choices=['json', 'text'])
    )
    mutually_exclusive = [('command','commands')]
    required_one_of = [('command', 'commands')]

    module = eapi_module(argument_spec=spec,
                         mutually_exclusive=mutually_exclusive,
                         required_one_of=required_one_of,
                         supports_check_mode=True)

    commands = module.params['commands'] or module.params['command']
    encoding = module.params['encoding']

    response, headers = eapi_command(module, commands, encoding)

    result = dict(changed=False, result=response)
    return module.exit_json(**result)


from ansible.module_utils.basic import *
from ansible.module_utils.urls import *
from ansible.module_utils.eapi import *

if __name__ == '__main__':
    main()
