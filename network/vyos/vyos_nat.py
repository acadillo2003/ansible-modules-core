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
module: vyos_nat
version_added: "2.2"
author: "Peter Sprygada (@privateip)"
short_description: Manage VyOS NAT resources on remote instances
description:
  - Provides a declarative resource for managing NAT entries
    configured on VyOS remote devices.
extends_documentation_fragment: vyos
options:
  rule:
    description:
      - The I(rule) argument specifies the unique rule number to
        manage in the configuration.  All NAT rules have a unique
        rule number specified.
    required: true
    default: null
  rule_type:
    description:
      - The I(rule_type) argument specifies the type of NAT rule
        to configure on the device.  The rule type can be defined
        as either a source NAT rule or a destination NAT rule.
    required: true
    default: null
    choices: [source, destination]
  description:
    description:
      - This argument configures the free form descriptive text that
        is associated with the NAT rule in the configuration.
    required: false
    default: null
  enabled:
    description:
      - Configures the administrative state of the NAT rule as either
        enabled (when set to True) or disabled (when set to False)
    required: false
    defualt: null
  exclude:
    description:
      - The I(exclude) argument will exclude packets from matching this
        rule from NAT with it is set to True.
    required: false
    default: null
  log:
    description:
     - When the I(log) argument is set to True, the NAT rule will log
       entries in the devices local log file.  If the value is set to
       False, rules will not be logged.  The device default value is
       False
    required: false
    default: null
  protocol:
    description:
      - Configures the protocol to NAT with this rule is invoke on the
        remote device.  Please see the VyOS help text for valid values
        when using this argument.
    required: false
    default: null
  outbound_interface:
    description:
      - Configures the outgoing interface to NAT traffic when the rule
        type is specified as source.  If the rule type is configured
        as destination, this argument is ignored.
    required: false
    default: null
  inbound_interface:
    description:
      - Configures the incoming interface to NAT traffic when the rule
        type is specified as destination.  If the rule type is configured
        as source, this argument is ignored.
    required: false
    default: null
  dest_address:
    description:
      - Configures the destination address to NAT when this rule is
        applied on the remote device.  Please see the VyOS documentation
        for valid destination values.
    required: false
    default: null
  dest_port:
    description:
      - Configures the destination port to NAT when this rule is
        applied on the remote device.  Please see the VyOS documentation
        for valid destination values.
    required: false
    default: null
  src_address:
    description:
      - Configures the source address to NAT when this rule is
        applied on the remote device.  Please see the VyOS documentation
        for valid destination values.
    required: false
    default: null
  src_port:
    description:
      - Configures the source port to NAT when this rule is
        applied on the remote device.  Please see the VyOS documentation
        for valid destination values.
    required: false
    default: null
  translation_address:
    description:
      - Configures the translation address to NAT when this rule is
        applied on the remote device.  Please see the VyOS documentation
        for valid destination values.
    required: false
    default: null
  translation_port:
    description:
      - Configures the translation port to NAT when this rule is
        applied on the remote device.  Please see the VyOS documentation
        for valid destination values.
    required: false
    default: null
  state:
    description:
      - The I(state) argument controls the state of the configuration
        stanzas in the device running configuration. When the state
        is C(present), the resource is configured in the device configuration
        and when C(absent) is specified, the M(service dhcp-server)
        stanza is removed from the configuration
    required: false
    defualt: present
    choices: [present, absent]
"""

EXAMPLES = """
- vyos_nat:
    rule: 100
    rule_type: destination
    enabled: yes
    dest_port: 80
    protocol: tcp
    translation_address: 10.1.1.1

- vyos_dhcp_server_name:
    rule: 101
    rule_type: source
    state: absent
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

def check_args(module, warnings):
    if module.params['rule_type'] == 'source':
        if module.params['outbound_interface']:
            warnings.append('cannot specify an outbound interface when '
                            'the rule type is source.  The outbound_interface '
                            'argument will be ignored')

    if module.params['rule_type'] == 'destination':
        if module.params['inbound_interface']:
            warnings.append('cannot specify an inbound interface when '
                            'the rule type is destination.  The '
                            'inbound_interface argument will be ignored')

def present(module, commands):
    for key, value in module.argument_spec.iteritems():
        setter = value.get('setter') or 'set_%s' % key
        if module.params[key] is not None:
            invoke(setter, module, commands)

def absent(module, commands):
    rule = module.params['rule']
    rtype = module.params['rule_type']
    commands.append('delete nat %s rule %s' % (rtype, rule))

def add(module, commands, param, action='set'):
    rule = module.params['rule']
    rtype = module.params['rule_type']
    commands.append('%s nat %s rule %s %s' % (action, rtype, rule, param))

def set_description(module, commands):
    add(module, commands, 'description %s' % module.params['description'])

def set_enabled(module, commands):
    if module.param['enabled']:
        add(module, commands, 'disable', 'delete')
    else:
        add(module, commands, 'disable')

def set_exclude(module, commands):
    if module.params['exclude']:
        add(module, commands, 'exclude')
    else:
        add(module, commands, 'exclude', 'delete')

def set_log(module, commands):
    if module.params['log']:
        add(module, commands, 'log', 'enable')
    else:
        add(module, commands, 'log')

def set_protocol(module, commands):
    add(module, commands, 'protocol %s' % module.params['protocol'])

def set_output_interface(module, commands):
    value = 'outbound-interface %s' % module.params['outbound_interface']
    add(module, commands, value)

def set_inbound_interface(module, commands):
    value = 'inbound-interface %s' % module.params['inbound_interface']
    add(module, commands, value)

def set_dest_address(module, commands):
    value = 'destination address %s' % module.params['dest_address']
    add(module, commands, value)

def set_dest_port(module, commands):
    value = 'destination port %s' % module.params['dest_port']
    add(module, commands, value)

def set_src_address(module, commands):
    value = 'source address %s' % module.params['src_address']
    add(module, commands, value)

def set_src_port(module, commands):
    value = 'source port %s' % module.params['src_port']
    add(module, commands, value)

def set_translation_address(module, commands):
    value = 'translation address %s' % module.params['translation_address']
    add(module, commands, value)

def set_translation_port(module, commands):
    value = 'translation port %s' % module.params['translation_port']
    add(module, commands, value)

def main():
    argument_spec = dict(
        rule=dict(type='int', required=True),
        rule_type=dict(choices=['source', 'destination'], required=True),

        description=dict(),
        enabled=dict(type='bool'),
        exclude=dict(type='bool'),
        log=dict(type='bool'),
        protocol=dict(),

        outbound_interface=dict(),
        inbound_interface=dict(),

        dest_address=dict(),
        dest_port=dict(),

        src_address=dict(),
        src_port=dict(),

        translation_address=dict(),
        translation_port=dict(),

        state=dict(choices=['present', 'absent'], default='present')
    )
    argument_spec.update(vyos_argument_spec)

    module = get_module(argument_spec=argument_spec,
                        connect_on_load=False,
                        supports_check_mode=True)

    state = module.params['state']

    result = dict(changed=False)

    warnings = list()
    invoke('check_args', module, warnings)

    commands = list()
    invoke(state, module, commands)

    try:
        response = load_config(module, commands)
        result.update(response)
    except (ValueError, NetworkError):
        exc = get_exception()
        module.fail_json(msg=str(exc))

    invoke('do', module)

    result['warnings'] = warnings
    result['connected'] = module.connected

    module.exit_json(**result)

from ansible.module_utils.vyos import *

if __name__ == '__main__':
    main()

