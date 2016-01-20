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

def get_response(data, module):
    try:
        json = module.from_json(data)
    except ValueError:
        json = None
    return dict(data=data, json=json)

def get_value(data, key):
    for k in key.split('.'):
        data = data.get(k)
    return data

def eq(this, other):
    return this == other

def ne(this, other):
    return this != other

def gt(this, other):
    return this > other

def ge(this, other):
    return this >= other

def lt(this, other):
    return this < other

def le(this, other):
    return this <= other

def contains(this, other):
    return this in other

def to_re(expression):
    expression = '^{}$'.format(expression)
    return re.compile(expression)

def match_re(regexp, values):
    for value in values:
        if regexp.match(value):
            return True

OPERATORS = {
    eq: ['eq', '=='],
    ne: ['ne', '!='],
    gt: ['gt', '>'],
    ge: ['ge', '>='],
    lt: ['lt', '<'],
    le: ['le', '<='],
    contains: ['contains', 'in']
}

def main():
    spec = dict(
        command=dict(),
        waitfor=dict(),
        retries=dict(default=10, type='int'),
        interval=dict(default=1, type='int')
    )

    module = get_module(argument_spec=spec,
                        supports_check_mode=True)

    command = module.params['command']
    waitfor = module.params['waitfor']
    retries = module.params['retries']
    interval = module.params['interval']

    if waitfor:
        key, operator, value = shlex.split(waitfor)

        if value in BOOLEANS_TRUE:
            value = True
        elif value in BOOLEANS_FALSE:
            value = False

        if key[0] == 'r':
            match = re.match(r'^r"(.*)"$')
            if match:
                regexp = to_re(match.group(1))

        for func, operators in OPERATORS.items():
            if operator in operators:
                break
        else:
            module.fail_json(msg='unknown operator')

        count = 0
        while count != retries:
            data = module.execute(command)
            response = get_response(data[0], module)

            curval = get_value(response.get('json'), key)
            if func(curval, value):
                break

            time.sleep(interval)
            count += 1
        else:
            module.fail_json(msg='timeout waiting for value')

    result = dict(changed=False)
    return module.exit_json(**result)


from ansible.module_utils.basic import *
from ansible.module_utils.urls import *
from ansible.module_utils.shell import *
from ansible.module_utils.netcfg import *
from ansible.module_utils.eos import *
if __name__ == '__main__':
        main()

