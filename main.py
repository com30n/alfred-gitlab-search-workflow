# -*- coding: utf-8 -*-
import sys

import search
import accounts
import update_index
from clone import get_clone_links

from workflow import Workflow3

from constants import CMD_SEARCH, CMD_UPDATE, CMD_ACCOUNT_LIST, CMD_ADD_ACCOUNT, CMD_DEL_ACCOUNT, CMD_CLONE

manage_cmd = [
    {'name': 'CMD_SEARCH', 'item': CMD_SEARCH, 'action': search.main},
    {'name': 'CMD_UPDATE', 'item': CMD_UPDATE, 'action': update_index.main},
    {'name': 'CMD_ACCOUNT_LIST', 'item': CMD_ACCOUNT_LIST, 'action': accounts.ManageGitlabAccounts.print_all_accounts},
    {'name': 'CMD_CLONE', 'item': CMD_CLONE, 'action': get_clone_links},
    {'name': 'CMD_ADD_ACCOUNT', 'item': CMD_ADD_ACCOUNT, },
    {'name': 'CMD_DEL_ACCOUNT', 'item': CMD_DEL_ACCOUNT, },
]


def get_cmd_from_var(wf):
    cmd = ''
    if wf.getvar('cmd'):
        cmd = wf.getvar('cmd')
    elif len(wf.args) > 0 and wf.args[0] != u'':
        cmd = wf.args[0]

    logger.debug("CMD was set: %s" % cmd)
    return cmd


def run_cmd(command):
    for cmd in manage_cmd:
        # If item has an action, just run it
        if command == cmd['name'] and cmd.get('action'):
            func = cmd['action']
            return func()
        # If item doesn't have an action, provide item['arg'] as a 'query' to a next filter
        # and it will decide which of the chains of functions it has to execute
        elif command == cmd['name']:
            print(cmd['name'])
            return


def show_manager_menu(wf):
    for cmd in manage_cmd:
        it = wf.add_item(**cmd['item'])
        it.setvar('cmd', cmd['name'])
    return wf


def manager(wf):
    # Get a 'cmd' variable, if it exists into the context
    cmd = get_cmd_from_var(wf)

    # If manager run not as a manager ('glm'), it has to just only run a chosen command
    if cmd:
        return run_cmd(cmd)

    # If manager run as a manager ('glm'), it has to show the main menu
    wf = show_manager_menu(wf)
    wf.send_feedback()


if __name__ == u'__main__':
    wf = Workflow3()
    logger = wf.logger
    sys.exit(wf.run(manager))
