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
module: vyos_system
version_added: "2.2"
author: "Peter Sprygada (@privateip)"
short_description: Manage VyOS device system resources on remote instances
description:
  - Provides a declarative resource for managing device system entries
    configured on VyOS remote devices.
extends_documentation_fragment: vyos
options:
  hostname:
    description:
      - This argument will configure the device hostname to the
        configured string.
    required: false
    default: null
  timezone:
    description:
      - Specifies the configured time-zone of the device to be set
        in the configuration.  The value for I(timezone) must be a
        valid value as specified by the CLI in the form of
        `Region/City`
    required: false
    default: null
  domain_name:
    description:
      - Configures the device domain name to be appended to the
        hostname to create the FQDN.  This argument accepts a
        valid string arugment for the domain name.
    required: false
    default: null
  domain_search:
    description:
      - Sets the list of doman names to service for DNS name
        completion.  The list of names specified using this argument
        will completely replace any previously configured domain
        search lists
    required: false
    default: null
  name_servers:
    description:
      - Sets the list of name servers to use for performing name
        resolution of DNS names.  The configured list will replace
        any previously configured name servers on the device in the
        current configuration
    required: false
    default: null
  gateway_address:
    description:
      - Configures the device default gateway address to use.  The
        value must be a valid IPv4 address in the form of A.B.C.D.
    required: false
    default: null
  ipv4_forwarding:
    description:
      - Configures the IPv4 forwarding value.  When the value is
        set to true, IPv4 fowarding is enabled and when set to
        false, IPv4 is administratively disabled.
    required: false
    default: null
  reboot_on_panic:
    description:
      - Enables or disables the action to perform on a kernel
        panic.  When set to true, the system will reboot on kernel
        panic and when set to false, the system will not reboot.
    required: false
    default: null
  ctrl_alt_del_action:
    description:
      - Configures the action to perform if the ctrl-alt-del key
        sequence is passed to the console.  Valid values must be
        choosen from the valid values.
    required: false
    default: null
    choices: ['ignore', 'reboot', 'poweroff']
"""

EXAMPLES = """
- vyos_system:
    hostname: vyos01
    domain_name: eng.ansible.com
    name_servers: 172.26.1.1
    gateway_address: 172.26.4.1
    ipv4_forwarding: yes
    reboot_on_panic: yes
"""

RETURN = """
warnings:
  description: Any warning messages returned from the device cli
  returned: always
  type: list
  sample: ['...']
connected:
  description: Boolean that specifies if the module connected to the device
  returned: always
  type: bool
  sample: true
updates:
  description: The list of configuration commands sent to the device
  returned: always
  type: list
  sample: ['...', '...']
"""

def invoke(name, *args, **kwargs):
    func = globals().get(name)
    if func:
        return func(*args, **kwargs)

def run(module, commands, config):
    for  key, value in module.argument_spec.iteritems():
        setter = value.get('setter') or 'set_%s' % key
        if module.params[key] is not None:
            invoke(setter, module, commands, config)

def check_args(module, warnings):
    pass

def set_hostname(module, commands, config):
    commands.append('set system host-name %s' % module.params['hostname'])

def set_timezone(module, commands, config):
    commands.append('set system time-zone' %s % module.params['timezone'])

def set_domain_name(module, commands, config):
    commands.extend([
        'delete system domain-search',
        'set system domain-name %s' % module.params['domain_name']
    ])

def set_domain_search(module, commands, config):
    wanted = module.params['domain_search']
    have = re.findall(r'domain-search domain (\S+)', config, re.M)

    commands.append('delete system domain-name')

    for name in set(have).difference(wanted):
        commands.append('delete system domain-search domain %s' % name)

    for name in set(wanted).difference(have):
        commands.append('set system domain-search domain %s' % name)

def set_name_servers(module, commands, config):
    wanted = module.params['name_servers']
    have = re.findall(r'name-server (\S+)', config, re.M)

    for name in set(have).difference(wanted):
        commands.append('delete system name-server %s' % name)

    for name in set(wanted).difference(have):
        commands.append('set system name-server %s' % name)

def set_gateway_address(module, commands, config):
    commands.append(
        'set system gateway-address %s' % module.params['gateway_address']
    )

def set_ipv4_forwarding(module, commands, config):
    if module.params['ipv4_forwarding'] is True:
        action = 'delete'
    else:
        action = 'set'
    commands.append('%s system ip disable-forwarding' % action)

def set_reboot_on_panic(module, commands, config):
    value = str(module.params['reboot_on_panic']).lower()
    commands.append('set system options reboot-on-panic %s' % value)

def set_ctrl_alt_del_action(module, commands, config):
    value = module.params['ctrl_alt_del_action']
    commands.append('set system options ctrl-alt-del-action %s' % value)


def main():
    """Main entry point for Ansible module
    """

    argument_spec = dict(
        hostname=dict(),
        timezone=dict(),

        domain_name=dict(),
        domain_search=dict(type='list'),
        name_servers=dict(type='list'),

        gateway_address=dict(),

        ipv4_forwarding=dict(type='bool'),

        reboot_on_panic=dict(type='bool'),
        ctrl_alt_del_action=dict(choices=['ignore', 'reboot', 'poweroff'])
    )

    argument_spec.update(vyos_argument_spec)

    mutually_exclusive = [('domain_name', 'domain_search')]

    module = get_module(argument_spec=argument_spec,
                        connect_on_load=False,
                        mutually_exclusive=mutually_exclusive,
                        supports_check_mode=True)

    result = dict(changed=False)

    warnings = list()
    invoke('check_args', module, warnings)

    config = get_config(module)

    commands = list()
    invoke('run', module, commands, str(config))

    try:
        response = load_commands(module, commands)
        result.update(response)
    except ValueError:
        exc = get_exception()
        module.fail_json(msg=str(exc))

    result['warnings'] = warnings
    result['connected'] = module.connected

    module.exit_json(**result)

from ansible.module_utils.vyos import *

if __name__ == '__main__':
    main()
