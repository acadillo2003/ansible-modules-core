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

    argument_spec = dict(
    )

    module = get_module(argument_spec=argument_spec,
                         supports_check_mode=True)

    config = str(module.config)

    facts = dict(config=config)
    result = dict(changed=False, ansible_facts=facts)
    module.exit_json(**result)

from ansible.module_utils.basic import *
from ansible.module_utils.shell import *
from ansible.module_utils.netcfg import *
from ansible.module_utils.iosxe import *
if __name__ == '__main__':
    main()

