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
module: vyos_ethernet
version_added: "2.2"
author: "Peter Sprygada (@privateip)"
short_description: Manage Ethernet interfaces in VyOS
description:
  - Configuration resource for managing Ethernet interfaces in the
    VyOS network operating system on remote devices.  This module
    provides arguments for mananing Ethernet interface properties.
extends_documentation: vyos
options:
  interface:
    description:
      - The name of the interface to apply the configuration to.  The
        interface must exist on the remote device for the configuration
        to be valid.
    required: true
    aliases: ['name']
  description:
    description:
      - Configures the interface description parameter for the specified
        interface.  The description argument accepts an ASCII string
        to be configured on the remote device.
    required: false
    default: null
  enabled:
    description:
      - Specifies the administrative state of the interface in the
        device configuration.  When set to true, the interface is
        administratively enabled and when set ot false the interface
        is administratively disabled
    required: false
    default: null
  addresses:
    description:
      - Specifies the IPv4 addresses to be configured on the Ethernet
        interface of the remote device.  The interface can be configured
        with one or more IPv4 addresses.  This argument also accepts
        `dhcp` as a valid value.
    required: false
    default: null
    aliases: ['address']
  mac:
    description:
      - Configures the physical Ethernet MAC address on the remote
        device.  The MAC address must be specified in the form of
        <h:h:h:h:h:h> to be valid.
    required: false
    default: null
  mtu:
    description:
      - Set the interface Maximum Transmission Unit on the Ethernet
        interface of the remote device.  Valid values for the interface
        MTU are in the range of 68 to 9000.
    required: false
    default: null
  speed:
    description:
      - Configures the interface speed value to one of the predefined
        settings for the Ethernet interface.
    required: false
    default: null
    choices: ['auto', '10', '100', '1000', '2500', '10000']
  duplex:
    description:
      - Configures the interface duplex value to on of the predefined
        settings for the Ethernet interface.
    choices: ['auto', 'half', 'full']
  flow_control:
    description:
      - Enables or disables flow control on the Ethernet interface for
        the remote device.  When this argument is set to true, flow
        control is enabled on the device and when this argument is set
        to false, flow control is disabled.
    required: false
    default: null
  link_detect:
    descriptoin:
      - Enables or disables link state detection on the Ethernet interface
        for the remote device.  When the argument is set to true,
        link state detection is enabled and when the argument is set to
        false, link state detection is disabled.
    required: false
    default: null
  firewall_in_ipv4:
    description:
      - Configures the name of the firewall instance to apply to IPv4
        inbound traffic on the interface.  The firewall instance must
        already be defined in the current device configuration.
    required: false
    default: null
  firewall_in_ipv6:
    description:
      - Configures the name of the firewall instance to apply to IPv6
        inbound traffic on the interface.  The firewall instance must
        already be defined in the current device configuration.
    required: false
    default: null
  firewall_local_ipv4:
    description:
      - Configures the name of the firewall instance to apply to IPv4
        local traffic on the interface.  The firewall instance must
        already be defined in the current device configuration.
    required: false
    default: null
  firewall_local_ipv6:
    description:
      - Configures the name of the firewall instance to apply to IPv6
        local traffic on the interface.  The firewall instance must
        already be defined in the current device configuration.
    required: false
    default: null
  firewall_out_ipv4:
    description:
      - Configures the name of the firewall instance to apply to IPv4
        outgoing traffic on the interface.  The firewall instance must
        already be defined in the current device configuration.
    required: false
    default: null
  firewall_out_ipv6:
    description:
      - Configures the name of the firewall instance to apply to IPv6
        outgoing traffic on the interface.  The firewall instance must
        already be defined in the current device configuration.
    required: false
    default: null
  traffic_policy_in:
    description:
      - Configures the name of the traffic policy shapper instance to
        apply to incoming traffic on thie interface. The traffic policy
        shaper instance must already be defined in the current
        device configuration.
    required: false
    default: null
  traffic_policy_out:
    description:
      - Configures the name of the traffic policy shapper instance to
        apply to outgoing traffic on thie interface. The traffic policy
        shaper instance must already be defined in the current
        device configuration.
    required: false
    default: null
  lines:
    description:
      - Provides a free form list of configuration commands to be applied
        at the interface level.  Commands should take the form of `set` or
        `delete` commands.  See EXAMPLES.
    required: false
    default: null
  oper_status:
    choices: ['up', 'down']
  neighbors:
  delay:
    default: 0
"""

EXAMPLES = """
# NOTE examples do not include required arguments for device credentials

- name: sample use of lines
  vyos_ethernet:
    name: eth1
    lines:
      - set disable
      - delete traffic-policy in DOWN

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
import time

def invoke(name, *args, **kwargs):
    func = globals().get(name)
    if func:
        return func(*args, **kwargs)

def present(module, commands):
    config = get_config(module)
    for key, value in module.argument_spec.iteritems():
        setter = value.get('setter') or 'set_%s' % key
        if module.params[key] is not None:
            invoke(setter, module, commands, config)

def do(module):
    time.sleep(module.params['delay'])
    for key in module.argument_spec.keys():
        if module.params[key] is not None:
            invoke('do_%s' % key, module)

def add(module, commands, cmd, action='set'):
    base = 'interfaces ethernet %s' % module.params['interface']
    commands.append('%s %s %s' % (action, base, cmd))

def set_address(module, commands, config):
    name = module.params['interface']
    have = re.findall(r'set interfaces ethernet %s address (.+)', config)
    want = module.params['addresses']

    if 'dhcp' in have and 'dhcp' not in want:
        add(module, commands, 'address dhcp', 'delete')
    elif have and 'dhcp' in want:
        for addr in have:
            add(module, commands, 'address %s' % addr, 'delete')
    else:
        for item in set(have).difference(want):
            add(mdoule, commands, 'address %s' % item, 'delete')
        for item in set(want).difference(have):
            add(module, commands, 'address %s' % item)

def set_description(module, commands, config):
    cmd = "description '%s'" % module.params['description']
    add(module, commands, cmd)

def set_enabled(module, commands, config):
    if module.params['enabled'] is True:
        action = 'delete'
    else:
        action = 'set'
    add(module, commands, 'disable', action)

def set_flow_control(module, commands, config):
    if module.params['flow_control'] is True:
        action = 'delete'
    else:
        action = 'set'
    add(module, commands, 'disable-flow-control', action=action)

def set_link_detect(module, commands, config):
    action = 'delete' if module.params['link_detect'] is True else 'set'
    add(module, commands, 'disable-link-detect', action)

def set_mac(module, commands, config):
    add(module, commands, 'mtu %s' % module.params['mac'])

def set_mtu(module, commands, config):
    if not 68 <= module.params['mtu'] <= 9000:
        module.fail_json(msg='mtu must be between 68 and 9000')
    add(module, commands, 'mtu %s' % module.params['mtu'])

def set_speed(module, commands, config):
    add(module, commands, 'speed %s' % module.params['speed'])

def set_duplex(module, commands, config):
    add(module, commands, 'duplex %s' % module.params['duplex'])

def set_firewall_in_ipv4(module, commands, config):
    value = module.params['firewall_in_ipv4']
    if 'set firewall name %s' % value not in str(config):
        module.fail_json(msg='firewall_in_ipv4 does not reference a '
                             'configured firewall instance')
    add(module, commands, 'firewall in name %s' % value)

def set_firewall_in_ipv6(module, commands, config):
    value = module.params['firewall_in_ipv6']
    if 'set firewall ipv6-name %s' % value not in str(config):
        module.fail_json(msg='firewall_in_ipv6 does not reference a '
                             'configured firewall instance')
    add(module, commands, 'firewall in ipv6-name %s' % value)

def set_firewall_local_ipv4(module, commands, config):
    value = module.params['firewall_local_ipv4']
    if 'set firewall name %s' % value not in str(config):
        module.fail_json(msg='firewall_local_ipv4 does not reference a '
                             'configured firewall instance')
    add(module, commands, 'firewall local name %s' % value)

def set_firewall_local_ipv6(module, commands, config):
    value = module.params['firewall_local_ipv6']
    if 'set firewall ipv6-name %s' % value not in str(config):
        module.fail_json(msg='firewall_local_ipv6 does not reference a '
                             'configured firewall instance')
    add(module, commands, 'firewall local ipv6-name %s' % value)

def set_firewall_out_ipv4(module, commands, config):
    value = module.params['firewall_out_ipv4']
    if 'set firewall name %s' % value not in str(config):
        module.fail_json(msg='firewall_out_ipv4 does not reference a '
                             'configured firewall instance')
    add(module, commands, 'firewall out name %s' % value)

def set_firewall_out_ipv6(module, commands, config):
    value = module.params['firewall_out_ipv6']
    if 'set firewall ipv6-name %s' % value not in str(config):
        module.fail_json(msg='firewall_out_ipv6 does not reference a '
                             'configured firewall instance')
    add(module, commands, 'firewall out ipv6-name %s' % value)

def set_traffic_policy_in(module, commands, config):
    value = module.params['traffic_policy_in']
    if 'set traffic-policy shaper in %s' % value not in str(config):
        module.fail_json(msg='traffic_policy_in does not reference a '
                             'configured traffic-policy')
    add(module, commands, 'traffic-policy in %s' % value)

def set_traffic_policy_out(module, commands, config):
    value = module.params['traffic_policy_out']
    if 'set traffic-policy shaper out %s' % value not in str(config):
        module.fail_json(msg='traffic_policy_out does not reference a '
                             'configured traffic-policy')
    add(module, commands, 'traffic-policy out %s' % value)

def set_lines(module, commands, config):
    for item in module.params['lines']:
        parts = item.split(' ')
        action = parts[0]
        if parts[0] not in ['set', 'delete']:
            action = 'set'
            option = ' '.join(parts)
        else:
            action = parts[0]
            option = ' '.join(parts[1:])
        add(module, commands, option, action)

def do_neighbors(module):
    interface = module.params['interface']
    response = module.cli('show lldp neighbors interface %s' % interface)[0]

    neighbors = set()
    for n in module.params['neighbors']:
        try:
            if sorted(n.keys()) != sorted(['host', 'port']):
                module.fail_json(
                    msg="neighbors must be specify both host and port keywords"
                )
            neighbors.add((n['host'], n['port']))
        except AttributeError:
            neighbors.add((n, None))

    cmd = 'show lldp neighbors interface %s' % interface
    response = module.cli(cmd)[0]

    results = dict()
    for neighbor in list(neighbors):
        for item in response.split('\n'):
            if neighbor[0] in item:
                if neighbor[1] is None or neighbor[1] in item:
                    neighbors.remove(neighbor)
                    break

    if neighbors:
        neighbors = ['%s:%s' % (n.host, n.port) for n in neighbors]
        module.fail_json(msg='not all neighbors matched: %s' % ','.join(neighbors))

def do_oper_status(module):
    interface = module.params['interface']
    oper_status = module.params['oper_status']

    runner = CommandRunner(module)
    runner.retries = 1

    waitfor = "result[0] contains 'state %s'" % str(oper_status).upper()
    runner.add_conditional(waitfor)

    cmd = 'show interfaces ethernet %s' % interface
    runner.add_command(cmd)

    try:
        runner.run()
    except FailedConditionsError:
        e = get_exception()
        module.fail_json(msg='desired oper_status invalid', e=e.failed_conditions)


def main():
    """Main entry point for Ansible module
    """

    argument_spec = dict(
        interface=dict(aliases=['name'], required=True),

        description=dict(),
        enabled=dict(type='bool'),

        addresses=dict(type='list', aliases=['address']),
        mac=dict(),
        mtu=dict(type='int'),

        speed=dict(choices=['auto', '10', '100', '1000', '2500', '10000']),
        duplex=dict(choices=['auto', 'half', 'full']),
        flow_control=dict(type='bool'),
        link_detect=dict(type='bool'),

        firewall_in_ipv4=dict(),
        firewall_in_ipv6=dict(),

        firewall_local_ipv4=dict(),
        firewall_local_ipv6=dict(),

        firewall_out_ipv4=dict(),
        firewall_out_ipv6=dict(),

        traffic_policy_in=dict(),
        traffic_policy_out=dict(),

        # set <option> (default)
        # delete <option>
        lines=dict(type='list'),

        oper_status=dict(choices=['up', 'down']),

        # { host: <str>, port: <str> }
        neighbors=dict(type='list'),
        delay=dict(type='int', default=0)
    )

    argument_spec.update(vyos_argument_spec)

    module = get_module(argument_spec=argument_spec,
                        connect_on_load=False,
                        supports_check_mode=True)

    result = dict(changed=False)

    warnings = list()
    invoke('check_args', module, warnings)

    commands = list()
    invoke('present', module, commands)

    try:
        response = load_config(module, commands)
        result.update(response)
    except ValueError:
        exc = get_exception()
        module.fail_json(msg=str(exc))

    invoke('do', module)

    result['warnings'] = warnings
    result['connected'] = module.connected

    module.exit_json(**result)

from ansible.module_utils.netcmd import *
from ansible.module_utils.vyos import *

if __name__ == '__main__':
    main()
