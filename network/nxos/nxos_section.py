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
import itertools

def get_config(module):
    config = module.params['config'] or dict()
    if not config and not module.params['force']:
        config = module.config
    return config


def build_candidate(commands, parents, config, strategy):
    candidate = list()

    if strategy == 'strict':
        if len(commands) != len(config):
            candidate = list(commands)
        else:
            for index, cmd in enumerate(commands):
                try:
                    if cmd != config[index]:
                        candidate.append(cmd)
                except IndexError:
                    candidate.append(cmd)

    elif strategy == 'exact':
        if len(commands) != len(config):
            candidate = list(commands)
        else:
            for cmd, cfg in itertools.izip(commands, config):
                if cmd != cfg:
                    candidate = list(commands)
                    break

    else:
        for cmd in commands:
            if cmd not in config:
                candidate.append(cmd)

    return candidate


def main():

    argument_spec = dict(
        commands=dict(required=True, type='list'),
        parents=dict(type='list'),
        before=dict(type='list'),
        after=dict(type='list'),
        match=dict(default='line', choices=['line', 'strict', 'exact']),
        replace=dict(default='line', choices=['line', 'block']),
        force=dict(default=False, type='bool'),
        config=dict()
    )

    module = get_module(argument_spec=argument_spec,
                         supports_check_mode=True)

    commands = module.params['commands']
    parents = module.params['parents'] or list()

    before = module.params['before']
    after = module.params['after']

    match = module.params['match']
    replace = module.params['replace']

    contents = get_config(module)
    config = module.parse_config(contents)

    if parents:
        for parent in parents:
            for item in config:
                if item.text == parent:
                    config = item

        try:
            children = [c.text for c in config.children]
        except AttributeError:
            children = [c.text for c in config]

    else:
        children = [c.text for c in config if not c.parents]

    result = dict(changed=False)

    candidate = build_candidate(commands, parents, children, match)

    if candidate:
        if replace == 'line':
            candidate[:0] = parents
        else:
            candidate = list(parents)
            candidate.extend(commands)

        if before:
            candidate[:0] = before

        if after:
            candidate.extend(after)

        if not module.check_mode:
            response = module.configure(candidate)
            result['response'] = response
        result['changed'] = True

    result['commands'] = candidate
    return module.exit_json(**result)

from ansible.module_utils.basic import *
from ansible.module_utils.urls import *
from ansible.module_utils.shell import *
from ansible.module_utils.netcfg import *
from ansible.module_utils.nxos import *
if __name__ == '__main__':
    main()

