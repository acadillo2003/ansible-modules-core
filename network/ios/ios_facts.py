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

IOS_FACTS = ['vlans', 'routing', 'interfaces', 'neighbors', 'config']

def do_vlans(module):
    if module.params['include_vlans']:
        return ('vlans', 'show vlans')

def do_routing(module):
    if module.params['include_routing']:
        return ('routing', 'show ip route')

def do_interfaces(module):
    if module.params['include_interfaces']:
        return ('interfaces', 'show interfaces')

def do_neighbors(module):
    if module.params['include_neighbors']:
        if module.params['use_lldp']:
            cmd = 'show lldp neighbors'
        else:
            cmd = 'show cdp neighbors'
        return ('neighbors', cmd)

def do_config(module):
    if module.params['include_config']:
        cmd = 'show running-config'
        if module.params['use_config_all']:
            cmd += ' all'
        return ('config', cmd)

def main():
    spec = dict(
        include_vlans=dict(default=True, type='bool'),
        include_routing=dict(default=True, type='bool'),
        include_interfaces=dict(default=True, type='bool'),
        include_neighbors=dict(default=True, type='bool'),
        include_config=dict(default=False, type='bool'),
        commands=dict(type='list'),
        use_lldp=dict(default=False, type='bool'),
        use_config_all=dict(default=True, type='bool')
    )
    argument_spec = ios_argument_spec(spec)

    argument_spec = ios_argument_spec(spec)
    required_one_of = ios_required_one_of()

    module = AnsibleModule(argument_spec=argument_spec,
                           required_one_of=required_one_of,
                           supports_check_mode=False)

    commands = dict(version='show version')
    for fact in IOS_FACTS:
        func = globals().get('do_%s' % fact)
        if func:
            cmd = func(module)
            if cmd:
                commands[cmd[0]] = cmd[1]

    connection = ios_connection(module)
    response = connection.send(commands.values())

    ios_facts = dict()
    for (key, cmd), resp in zip(commands.items(), response):
        ios_facts[key] = resp

    if module.params['include_config']:
        if not module.params['enable_mode']:
            msg = 'enable_mode must be true if include_config is true'
            return module.fail_json(msg=msg)
        cmd = 'show running-config'
        if module.params['use_config_all']:
            cmd += ' all'
        response = connection.send(cmd)
        ios_facts['config'] = response[0]

    if module.params['commands']:
        response = connection.send(module.params['commands'])
        ios_facts['commands'] = response

    ansible_facts = {'ios_facts': ios_facts}
    return module.exit_json(ansible_facts=ansible_facts)


from ansible.module_utils.basic import *
from ansible.module_utils.ssh import *
from ansible.module_utils.ios import *

if __name__ == '__main__':
    main()
