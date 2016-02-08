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
from lxml import etree

def build_candidate(updates):
    config = """<config><interfaces xmlns="urn:ietf:params:xml:ns:yang:ietf-interfaces">"""

    if 'operation' in updates:
        config += '<interface operation="%s">' % updates['operation']
    else:
        config += "<interface>"

    config += "<name>%s</name>" % updates['name']
    config += '<type xmlns:ianaift="urn:ietf:params:xml:ns:yang:iana-if-type">ianaift:softwareLoopback</type>'

    if 'description' in updates:
        config += "<description>%s</description>" % updates['description']

    config += """</interface></config>"""

    return config

def parse_element(element):
    data = dict()
    for attr in element:
        key = attr.xpath("local-name()")
        if not attr.getchildren():
            if key not in ['ipv4', 'ipv6']:
                data[key] = attr.text
        else:
            data[key] = parse_element(attr)
    return data

def get_interface(module):
    name = module.params['name']
    resp = module.connection.manager.get(filter=('subtree', '<interfaces/>')).data_xml
    config = etree.fromstring(resp)

    path = '{urn:ietf:params:xml:ns:yang:ietf-interfaces}interfaces'
    for item in config.find(path):
        interface = parse_element(item)
        if interface['name'] == name:
            interface['state'] = 'present'
            return interface
    return dict(name=name, state='absent')

def main():

    argument_spec = dict(
        name=dict(required=True),
        description=dict(),
        enabled=dict(default=True, type='bool'),
        state=dict(default='present', choices=['absent', 'present'])
    )

    module = get_module(argument_spec=argument_spec,
                         supports_check_mode=True)

    config = get_interface(module)

    result = dict(changed=False)

    updates = dict()

    if config['state'] == 'absent' and module.params['state'] == 'present':
        updates['operation'] = 'create'
        updates['description'] = module.params['description']

    elif config['state'] == 'present' and module.params['state'] == 'absent':
        updates['operation'] = 'remove'

    elif config['state'] == 'present':
        if module.params['description'] != None:
            if config.get('description') != module.params['description']:
                updates['description'] = module.params['description']

    if updates:
        updates['name'] = module.params['name']
        candidate = build_candidate(updates)
        #result['candidate'] = candidate
        module.configure(candidate)
        result['changed'] = True

    result['config'] = get_interface(module)

    return module.exit_json(**result)

from ansible.module_utils.basic import *
from ansible.module_utils.shell import *
from ansible.module_utils.netcfg import *
from ansible.module_utils.iosxe import *
if __name__ == '__main__':
    main()

