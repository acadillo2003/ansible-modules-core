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

def compare(this, other):
    parents = [item.text for item in this.parents]
    for entry in other:
        if this == entry:
            return None
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

def get_config(provider):
    config = provider.module.params['config'] or dict()
    if not config and not provider.module.params['force']:
        config = provider.config
    return config

def backup_config(config, module):
    host = module.params['host']
    open('backup_%s' % host, 'w').write(config)


def main():

    argument_spec = dict(
        src=dict(),
        backup=dict(default=False, type='bool'),
        force=dict(default=False, type='bool'),
        config_replace=dict(default=False, type='bool'),
        include_defaults=dict(default=True, type='bool'),
        config=dict(),
        log_path=dict(default='./nxos_config.log', type='str')
    )
    
    mutually_exclusive = [('config', 'backup'), ('config', 'force')]

    module = net_module(argument_spec=argument_spec,
                        mutually_exclusive=mutually_exclusive,
                        supports_check_mode=True)

    logger = Log(module)
    module.logger = logger 
    
    for p in module.params:
        logger.debug("%s: %s" % (p, module.params[p]))
    
    src = module.params['src']
    force = module.params['force']
    backup = module.params['backup']
    replace = module.params['config_replace']
    
    logger.debug("candidate:")
    logger.debug(src)
    
    provider = get_provider(module)
    candidate = provider.parse(src)
    contents = get_config(provider)    
    config = provider.parse(contents)

    if backup and not module.check_mode:
        backup_config(contents, module)

    result = dict(changed=False)

    commands = collections.OrderedDict()
    toplevel = [c.text for c in config]

    for line in candidate:
        if line.text.startswith('!') or line.text == '':
            continue

        if not line.parents:
            if line.text not in toplevel:
                expand(line, commands)
        else:
            item = compare(line, config)
            if item:
                expand(item, commands)
    
    commands = flatten(commands, list())

    if commands:
        if not module.check_mode:
            try:
                commands = [str(c).strip() for c in commands]
                logger.info('Executing commands: ')
                for c in commands:
                    logger.info(c)
                response = provider.configure(commands)
            except Exception, exc:
                return module.fail_json(msg=exc.message)
        result['changed'] = True

    result['commands'] = commands
    return module.exit_json(**result)


from ansible.module_utils.basic import *
from ansible.module_utils.network import *
from ansible.module_utils.urls import * 
from ansible.module_utils.nxapi import *

if __name__ == '__main__':
    main()