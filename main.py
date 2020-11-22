# -*- coding: utf-8 -*-
import os
import sys

from workflow import Workflow3

from constants import MAIN_MANAGE_CMD, ACCOUNTS_MANAGE_CMD


def get_cmd_from_var(wf):
    cmd = ''
    if wf.getvar('cmd'):
        cmd = wf.getvar('cmd')
    elif len(wf.args) > 0 and wf.args[0] != u'':
        cmd = wf.args[0]
    else:
        cmd = os.environ.get("cmd")

    logger.debug("CMD was set: %s" % cmd)
    return cmd


def show_manager_menu(wf, cmd_enum):
    for cmd_name, cmd in cmd_enum.__members__.items():
        it = wf.add_item(**cmd.value)
        it.setvar('cmd', cmd_name)
    return wf


def main(wf):
    cmd = get_cmd_from_var(wf)
    if cmd and cmd == "CMD_ACCOUNTS":
        wf = show_manager_menu(wf, cmd_enum=ACCOUNTS_MANAGE_CMD)
    else:
        wf = show_manager_menu(wf, cmd_enum=MAIN_MANAGE_CMD)

    wf.send_feedback()


if __name__ == u'__main__':
    wf = Workflow3()
    logger = wf.logger
    sys.exit(wf.run(main))

