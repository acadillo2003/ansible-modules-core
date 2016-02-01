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
import re

def get_config(module):
    config = module.params['config'] or dict()
    if not config and not module.params['match'] == 'force':
        config = module.config
    return config


def build_candidate(commands, config, match):
    candidate = list()
    if len(commands) == len(config):
        for cmd, cfg in itertools.izip(commands, config):
            if cmd == cfg:
                candidate.append(cmd)
    elif match == 'block':
        candidate = list(commands)
    else:
        for index, cmd in enumerate(commands):
            try:
                if cmd != config[index]:
                    candidate.append(cmd)
            except IndexError:
                candidate.append(cmd)
    return candidate


def main():

    argument_spec = dict(
        commands=dict(required=True, type='list'),
        section=dict(required=True, type='list'),
        before=dict(type='list'),
        after=dict(type='list'),
        match=dict(default='line', choices=['line', 'block', 'force']),
        config=dict()
    )

    required_one_of = [('line', 'block')]

    module = get_module(argument_spec=argument_spec,
                         supports_check_mode=True)

    commands = module.params['commands']
    section = module.params['section']

    before = module.params['before']
    after = module.params['after']

    match = module.params['match']

    contents = get_config(module)
    config = module.parse_config(contents)

    cfg = list(config)
    for parent in section:
        for item in config:
            if item.text == parent:
                cfg = item

    result = dict(changed=False)

    children = [c.text for c in cfg.children]
    candidate = build_candidate(commands, children, match)

    if candidate:
        if match == 'line':
            candidate[:0] = section

        elif match == 'block':
            candidate = list(section)
            candidate.extend(commands)

        if before:
            candidate[:0] = before

        if after:
            candidate.extend(after)

        if not module.check_mode:
            if replace:
                response = module.config_replace(commands)
            else:
                response = module.configure(commands)
        result['changed'] = True

    result['commands'] = candidate
    return module.exit_json(**result)

from ansible.module_utils.basic import *
from ansible.module_utils.urls import *
from ansible.module_utils.shell import *
from ansible.module_utils.netcfg import *
from ansible.module_utils.eos import *
if __name__ == '__main__':
    main()

