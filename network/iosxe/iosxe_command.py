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

import time
import shlex
import re
import json

INDEX_RE = re.compile(r'(\[\d+\])')

def get_response(data):
    try:
        json_data = json.loads(data)
    except ValueError:
        json_data = None
    return dict(data=data, json=json_data)

class Conditional(object):

    OPERATORS = {
        'eq': ['eq', '=='],
        'neq': ['neq', 'ne', '!='],
        'gt': ['gt', '>'],
        'ge': ['ge', '>='],
        'lt': ['lt', '<'],
        'le': ['le', '<='],
        'contains': ['contains', 'in']
    }

    def __init__(self, conditional):
        self.raw = conditional

        key, op, val = shlex.split(conditional)
        self.key = key
        self.func = self.func(op)
        self.value = self._cast_value(val)

    def __call__(self, data):
        value = self.get_value(dict(result=data))
        return self.func(value)

    def _cast_value(self, value):
        if value in BOOLEANS_TRUE:
            return True
        elif value in BOOLEANS_FALSE:
            return False
        elif re.match(r'^\d+\.d+$', value):
            return float(value)
        elif re.match(r'^\d+$', value):
            return int(value)
        else:
            return unicode(value)

    def func(self, oper):
        for func, operators in self.OPERATORS.items():
            if oper in operators:
                return getattr(self, func)
        raise AttributeError('unknown operator: %s' % oper)

    def get_value(self, result):
        for key in self.key.split('.'):
            match = re.match(r'^(\w+)\[(\d+)\]', key)
            if match:
                key, index = match.groups()
                result = result[key][int(index)]
            else:
                result = result.get(key)
        return result

    def eq(self, value):
        return value == self.value

    def neq(self, value):
        return value != self.value

    def gt(self, value):
        return value > self.value

    def ge(self, value):
        return value >= self.value

    def lt(self, value):
        return value < self.value

    def le(self, value):
        return value <= self.value

    def contains(self, value):
        return self.value in value

def main():
    spec = dict(
        commands=dict(type='list'),
        waitfor=dict(type='list'),
        retries=dict(default=10, type='int'),
        interval=dict(default=1, type='int')
    )

    module = get_module(argument_spec=spec,
                        supports_check_mode=True)


    commands = module.params['commands']

    retries = module.params['retries']
    interval = module.params['interval']

    try:
        queue = set()
        for entry in (module.params['waitfor'] or list()):
            queue.add(Conditional(entry))
    except AttributeError, exc:
        module.fail_json(msg=exc.message)

    result = dict(changed=False, result=list())

    kwargs = dict()
    if module.params['transport'] == 'nxapi':
        kwargs['command_type'] = 'cli_show'

    while retries > 0:
        try:
            response = module.execute(commands, **kwargs)
            result['result'] = response
        except ShellError:
            module.fail_json(msg='failed to run commands')

        for index, cmd in enumerate(commands):
            if cmd.endswith('json'):
                response[index] = json.loads(response[index])

        for item in list(queue):
            if item(response):
                queue.remove(item)

        if not queue:
            break

        time.sleep(interval)
        retries -= 1
    else:
        failed_conditions = [item.raw for item in queue]
        module.fail_json(msg='timeout waiting for value', failed_conditions=failed_conditions)

    return module.exit_json(**result)


from ansible.module_utils.basic import *
from ansible.module_utils.urls import *
from ansible.module_utils.shell import *
from ansible.module_utils.netcfg import *
from ansible.module_utils.nxos import *
if __name__ == '__main__':
        main()

