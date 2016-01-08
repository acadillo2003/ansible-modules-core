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

def compare(this, other, ignore_missing=False):
    parents = [item.text for item in this.parents]
    for entry in other:
        if this == entry:
            return None
    if not ignore_missing:
        return this

def expand(obj, queue):
    block = [item.raw for item in obj.parents]
    block.append(obj.raw)

    current_level = queue
    for b in block:
        if b not in current_level:
            current_level[b] = collections.OrderedDict()
        current_level = current_level[b]
    for c in obj.children:
        if c.raw not in current_level:
            current_level[c.raw] = collections.OrderedDict()

def flatten(data, obj):
    for k, v in data.items():
        obj.append(k)
        flatten(v, obj)
    return obj

def get_config(module):
    config = module.params['config'] or dict()
    if not config and not module.params['force']:
        config = module.config
    return config

def backup_config(config, module):
    host = module.params['host']
    open('backup_%s' % host, 'w').write(config)


def main():

    argument_spec = dict(
        src=dict(),
        force=dict(default=False, type='bool'),
        include_defaults=dict(default=True, type='bool'),
        backup=dict(default=False, type='bool'),
        ignore_missing=dict(default=False, type='bool'),
        config=dict(),
        log_path=dict(default='./nxos_config.log', type='str')
    )
    
    mutually_exclusive = [('config', 'backup'), ('config', 'force')]

    module = get_module(argument_spec=argument_spec,
                        mutually_exclusive=mutually_exclusive,
                        supports_check_mode=True)

    ignore_missing = module.params['ignore_missing']
    result = dict(changed=False)

    for p in module.params:
        module.logger.debug("%s: %s" % (p, module.params[p]))
    
    candidate = module.parse_config(module.params['src'])
    contents = get_config(module)
    config = module.parse_config(contents)
    

    # if backup and not module.check_mode:
    #    backup_config(contents, module)

    commands = collections.OrderedDict()
    toplevel = [c.text for c in config]

    for line in candidate:
        if line.text.startswith('!') or line.text == '':
            continue

        if not line.parents:
            if line.text not in toplevel:
                expand(line, commands)
        else:
            item = compare(line, config, ignore_missing)
            if item:
                expand(item, commands)
    
    commands = flatten(commands, list())

    if commands:
        if not module.check_mode:
            try:
                commands = [str(c).strip() for c in commands]
                module.logger.info('Executing commands: ')
                for c in commands:
                    module.logger.info(c)
                response = module.configure(commands)
            except Exception, exc:
                return module.fail_json(msg=exc.message)
        result['changed'] = True

    result['commands'] = commands
    return module.exit_json(**result)

from ansible.module_utils.basic import *
from ansible.module_utils.urls import *
from ansible.module_utils.shell import *
from ansible.module_utils.netcfg import *
from ansible.module_utils.nxos import *
from ansible.module_utils.log import *

if __name__ == '__main__':
    main()