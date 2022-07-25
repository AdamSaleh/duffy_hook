from ansible import context
from ansible.cli import CLI
from ansible.executor.playbook_executor import PlaybookExecutor
from ansible.inventory.manager import InventoryManager
from ansible.module_utils.common.collections import ImmutableDict
from ansible.parsing.dataloader import DataLoader
from ansible.vars.manager import VariableManager


def execute_playbook(inventory_string, playbook_path, extra_vars={}):
    loader = DataLoader()

    context.CLIARGS = ImmutableDict(
        tags={}, listtags=False, listtasks=False, listhosts=False,
        syntax=False, connection='ssh', module_path=None, forks=100,
        remote_user='root',
        private_key_file="/etc/duffy-ssh-key/ssh-privatekey",
        ssh_common_args=None,
        ssh_extra_args=None, sftp_extra_args=None, scp_extra_args=None,
        become=True, become_method='sudo', become_user='root',
        verbosity=True, check=False, start_at_task=None,
    )

    inventory = InventoryManager(loader=loader, sources=inventory_string)

    variable_manager = VariableManager(
        loader=loader, inventory=inventory,
        version_info=CLI.version_info(gitinfo=False),
    )

    variable_manager._extra_vars = extra_vars  # To accomodate other arguments

    pbex = PlaybookExecutor(
        playbooks=[playbook_path], inventory=inventory,
        variable_manager=variable_manager, loader=loader, passwords={},
    )
    try:
        pbex.run()
    except Exception as e:
        print(e)

    return pbex._tqm._stats
