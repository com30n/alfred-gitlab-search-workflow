import argparse
import json
import sys
from functools import partial
from urlparse import urlparse

from constants import ACCOUNTS_MANAGE_CMD, ACCOUNTS_ACTIONS, MAIN_MANAGE_CMD, VARIABLES
from utils import get_wf_variable, merge_two_dicts
from workflow import Workflow3 as Workflow, ICON_WEB, ICON_WARNING, PasswordNotFound, Workflow3, util, ICON_ERROR
from workflow.notify import notify

wf = Workflow()
logger = wf.logger

GITLAB_ACCOUNTS_TEMP = "GITLAB_ACCOUNTS_TEMP"
GITLAB_ACCOUNTS = "GITLAB_ACCOUNTS"


class Account:
    class _possible_project_visibilities:
        public = "public"
        internal = "internal"
        private = "private"

        @classmethod
        def as_list(cls):
            return [cls.public, cls.internal, cls.private]

    class _possible_project_mempership:
        true = True
        false = False

        @classmethod
        def as_list(cls):
            return [cls.true, cls.false]

    def __init__(self, account_dict):
        logger.debug("account_dict: {}".format(account_dict))
        self._account_dict = account_dict
        self.__name = ""
        self.__url = ""
        self.__project_visibility = None
        self.__project_membership = None

    @property
    def name(self):
        if not self.__name and self._account_dict:
            self.__name = self._account_dict.keys()[0]
        logger.debug("name: {}".format(self.__name))
        return self.__name

    @name.setter
    def name(self, value):
        self.__name = value

    @property
    def token(self):
        token = None

        if self._account_dict.get("token"):
            token = self._account_dict.get("token")
        elif self.name:
            try:
                keychain_token = wf.get_password(self.name)
                token = keychain_token
            except PasswordNotFound:
                token = None
        return token

    @token.setter
    def token(self, value):
        if self.__name:
            wf.save_password(self.__name, value)

    @property
    def project_visibility(self):
        if not self.__project_visibility:
            self.__project_visibility = self._account_dict.get(self.name, {}).get("project_visibility", None)
        logger.debug("project_visibility: {}".format(self.__project_visibility))
        return self.__project_visibility

    @project_visibility.setter
    def project_visibility(self, value):
        if value in self._possible_project_visibilities.as_list():
            self.__project_visibility = value

    @property
    def project_membership(self):
        if not self.__project_membership:
            self.__project_membership = self._account_dict.get(self.name, {}).get("project_membership", None)
        logger.debug("project_membership: {}".format(self.__project_membership))
        return self.__project_membership

    @project_membership.setter
    def project_membership(self, value):
        if value in self._possible_project_mempership.as_list():
            self.__project_membership = value

    @property
    def url(self):
        if not self.__url:
            url = self._account_dict.get(self.name, {}).get("url", "")
            self.__url = get_validated_url(url)
        logger.debug("url: {}".format(self.__url))
        return self.__url

    @url.setter
    def url(self, value):
        self.__url = get_validated_url(value)

    @property
    def complete(self):
        complete = True
        if not self.name:
            complete = False
        if not self.url:
            complete = False
        if not self.token:
            complete = False
        if self.project_membership is None:
            complete = False
        if self.project_visibility is None:
            complete = False
        return complete

    def update_setting(self, setting_name, setting_value):
        if setting_name in self.props():
            setattr(self, setting_name, setting_value)

    @classmethod
    def props(cls):
        return [i for i in cls.__dict__.keys() if i[:1] != '_']

    def as_dict(self):
        return {
            self.name: {
                "url": self.url,
                "project_visibility": self.project_visibility,
                "project_membership": self.project_membership,
            }
        }


class Accounts:
    def __init__(self, accounts_dict):
        self.dict = {
            acc_name: Account({acc_name: acc_settings})
            for acc_name, acc_settings in accounts_dict.items()
        }

    def get_acc(self, account_name):
        return self.dict.get(account_name)

    def add_acc(self, account):
        if account.name in self.dict.keys():
            return
        self.dict.update({account.name: account})

    def del_acc(self, account):
        if account.name in self.dict.keys():
            self.dict.pop(account.name)

    def update_acc(self, account):
        if account.name not in self.dict.keys():
            return
        self.dict.update({account.name: account})

    def as_dict(self):
        return {acc_name: acc_settings.as_dict().values()[0] for acc_name, acc_settings in self.dict.items()}


def get_validated_url(url):
    url = urlparse(url)
    logger.debug("parsed url: {}".format(url))
    if url.netloc:
        return "https://{url_netloc}".format(url_netloc=url.netloc)
    if url.path:
        return "https://{url_netloc}".format(url_netloc=url.path)
    return ""


def _get_accs(wf, value_name):
    gitlab_accounts = json.loads(get_wf_variable(wf, value_name, default="{}"))
    return gitlab_accounts


def get_accounts(wf):
    return _get_accs(wf, GITLAB_ACCOUNTS)


def get_temp_accounts(wf):
    return _get_accs(wf, GITLAB_ACCOUNTS_TEMP)


def _save_accs(wf, value_name, accounts_dict):
    util.set_config(value_name, json.dumps(accounts_dict))


def save_accounts(wf, accounts_dict):
    _save_accs(wf, GITLAB_ACCOUNTS, accounts_dict.as_dict())


def save_temp_accounts(wf, account):
    _save_accs(wf, GITLAB_ACCOUNTS_TEMP, account.as_dict())


def del_temp_accounts(wf):
    _save_accs(wf, GITLAB_ACCOUNTS_TEMP, {})


def get_accounts_list(wf, cmd_var=None, action_var=None):
    gitlab_accounts = Accounts(get_accounts(wf))

    if gitlab_accounts:
        for account in gitlab_accounts.dict.values():
            try:
                has_token = bool(wf.get_password(account.name))
            except PasswordNotFound:
                has_token = False
            it = wf.add_item(
                title=account.name,
                subtitle="Has token: {has_token}, URL: {url}".format(has_token=has_token, url=account.url),
                valid=True,
            )
            it.setvar(VARIABLES.account, account.name)
            if action_var:
                it.setvar(VARIABLES.action, action_var)
            if cmd_var:
                it.setvar(VARIABLES.cmd, cmd_var)
    else:
        wf.add_item(
            title="You don't have any gitlab accounts yet.",
            subtitle="Please create at least one.",
            icon=ICON_ERROR,
            valid=False
        )
        it = wf.add_item(
            title="Create new account",
            subtitle="Choose the item to create new account",
            valid=True,
        )
        it.setvar(VARIABLES.cmd, ACCOUNTS_MANAGE_CMD.CMD_ADD_ACCOUNT.name)

    return wf


def get_account_settings(wf, account):
    wf.add_item(
        title="Account settings: {}".format(account.name),
        valid=False
    )
    {}.values()
    for key, value in account.as_dict()[account.name].items():
        it = wf.add_item(
            title="{key}: {value}".format(key=key, value=value),
            subtitle="Enter to change",
            valid=True
        )
        it.setvar(VARIABLES.cmd, ACCOUNTS_MANAGE_CMD.CMD_ACCOUNT_SETTINGS.name)
        it.setvar(VARIABLES.account, account.name)
        it.setvar(VARIABLES.action, ACCOUNTS_ACTIONS.update_account_settings)
        it.setvar(VARIABLES.acc_setting, key)
    it = wf.add_item(
        title="token: 'hidden'",
        subtitle="Enter to change",
        valid=True
    )
    it.setvar(VARIABLES.cmd, ACCOUNTS_MANAGE_CMD.CMD_ACCOUNT_SETTINGS.name)
    it.setvar(VARIABLES.account, account.name)
    it.setvar(VARIABLES.action, ACCOUNTS_ACTIONS.update_account_settings)
    it.setvar(VARIABLES.acc_setting, "token")
    return wf


def process_account_creation(wf, wf_query, account):
    if not account.name:
        it = wf.add_item(
            title="Enter account name",
            subtitle="Enter uniq name, needs to store your token in keychain",
            valid=True
        )
        it.setvar(VARIABLES.cmd, ACCOUNTS_MANAGE_CMD.CMD_ADD_ACCOUNT.name)
        it.setvar(VARIABLES.action, ACCOUNTS_ACTIONS.add_new_account)
        it.setvar(VARIABLES.account, wf_query)


    elif not account.url:
        url = get_validated_url(wf_query)
        it = wf.add_item(
            title="Enter here your gitlab url, for account '{}'".format(account.name),
            subtitle="Please check: {}".format(url),
            valid=True
        )
        it.setvar(VARIABLES.cmd, ACCOUNTS_MANAGE_CMD.CMD_ADD_ACCOUNT.name)
        it.setvar(VARIABLES.action, ACCOUNTS_ACTIONS.add_url)
        it.setvar(VARIABLES.account, account.name)
        it.setvar(VARIABLES.var_data, url)

    elif not account.token:
        it = wf.add_item(
            title="Enter here your gitlab token, for account '{}'".format(account.name),
            subtitle="Please check: {}".format(wf_query),
            valid=True
        )
        it.setvar(VARIABLES.cmd, ACCOUNTS_MANAGE_CMD.CMD_ADD_ACCOUNT.name)
        it.setvar(VARIABLES.action, ACCOUNTS_ACTIONS.add_token)
        it.setvar(VARIABLES.account, account.name)
        it.setvar(VARIABLES.var_data, wf_query)

    # elif account.project_membership is None:
    #     wf.add_item(
    #         title="Please choose projects membership for account '{}'".format(account.name),
    #         subtitle="Only projects where you have a membership will be cached",
    #         valid=False
    #     )
    #     it = wf.add_item(
    #         title="True",
    #         subtitle="Only projects where you have a membership will be cached",
    #         valid=True
    #     )
    #     it.setvar(VARIABLES.cmd, ACCOUNTS_MANAGE_CMD.CMD_ADD_ACCOUNT.name)
    #     it.setvar(VARIABLES.action, ACCOUNTS_ACTIONS.add_project_membership)
    #     it.setvar(VARIABLES.account, account.name)
    #     it.setvar(VARIABLES.var_data, str(True))
    #     it = wf.add_item(
    #         title="False",
    #         subtitle="All available projects where will be cached (Do not use with gitlab.com!)",
    #         valid=True
    #     )
    #     it.setvar(VARIABLES.cmd, ACCOUNTS_MANAGE_CMD.CMD_ADD_ACCOUNT.name)
    #     it.setvar(VARIABLES.action, ACCOUNTS_ACTIONS.add_project_membership)
    #     it.setvar(VARIABLES.account, account.name)
    #     it.setvar(VARIABLES.var_data, str(False))

    # elif not account.project_visibility:
    #     wf.add_item(
    #         title="Please choose projects visibility for account '{}'".format(account.name),
    #         subtitle="By default will be selected 'private'",
    #         icon=ICON_WARNING,
    #         valid=False
    #     )
    #
    #     it = wf.add_item(
    #         title="Default",
    #         subtitle="By default is using 'private'",
    #         valid=True
    #     )
    #     it.setvar(VARIABLES.cmd, ACCOUNTS_MANAGE_CMD.CMD_ADD_ACCOUNT.name)
    #     it.setvar(VARIABLES.action, ACCOUNTS_ACTIONS.add_project_visibility)
    #     it.setvar(VARIABLES.account, account.name)
    #     it.setvar(VARIABLES.var_data, account._possible_project_visibilities.private)
    #
    #     for visibility in account._possible_project_visibilities.as_list():
    #         it = wf.add_item(
    #             title=visibility,
    #             valid=True,
    #         )
    #         it.setvar(VARIABLES.cmd, ACCOUNTS_MANAGE_CMD.CMD_ADD_ACCOUNT.name)
    #         it.setvar(VARIABLES.action, ACCOUNTS_ACTIONS.add_project_visibility)
    #         it.setvar(VARIABLES.account, account.name)
    #         it.setvar(VARIABLES.var_data, visibility)

    else:
        it = wf.add_item(
            title="Save account '{}'".format(account.name),
            subtitle="URL: '{url}', project membership: '{membership}', project visibility: '{visibility}'".format(
                url=account.url,
                membership=account.project_membership,
                visibility=account.project_visibility,
            ),
            valid=True,
        )
        it.setvar(VARIABLES.cmd, ACCOUNTS_MANAGE_CMD.CMD_ADD_ACCOUNT.name)
        it.setvar(VARIABLES.account, account.name)
        it.setvar(VARIABLES.action, ACCOUNTS_ACTIONS.save_account_settings)

    return wf


def do_account_action(wf, account, action, data):
    if action == ACCOUNTS_ACTIONS.add_new_account:
        save_temp_accounts(wf, account)

    elif action == ACCOUNTS_ACTIONS.add_url:
        account.url = data
        save_temp_accounts(wf, account)

    elif action == ACCOUNTS_ACTIONS.add_token:
        account.token = data
        wf.save_password(account.name, data)

    elif action == ACCOUNTS_ACTIONS.add_project_membership:
        account.project_membership = bool(data)
        save_temp_accounts(wf, account)

    elif action == ACCOUNTS_ACTIONS.add_project_visibility:
        account.project_visibility = data
        save_temp_accounts(wf, account)


def add_account(wf):
    query = wf.args[-1]

    account_name = get_wf_variable(wf, "account")
    var_data = get_wf_variable(wf, "var_data")
    action = get_wf_variable(wf, "action")
    logger.debug("add_account vars: account {}, var_data {}, action {}".format(account_name, var_data, action))
    if action == ACCOUNTS_ACTIONS.flush_ongoing:
        del_temp_accounts(wf)
        account_name = None

    exist_gitlab_accounts = Accounts(get_accounts(wf))
    on_going_add = Account(get_temp_accounts(wf))
    logger.debug("add_account accounts: exists {}, ongoing_add {}".format(exist_gitlab_accounts, on_going_add))

    if action == ACCOUNTS_ACTIONS.save_account_settings:
        exist_gitlab_accounts.add_acc(on_going_add)
        save_accounts(wf, exist_gitlab_accounts)
        del_temp_accounts(wf)
        notify("Account '{}' has been saved".format(on_going_add.name))
        return wf

    if account_name and not on_going_add.name:
        on_going_add.name = account_name

    if on_going_add.name in exist_gitlab_accounts.as_dict().keys():
        it = wf.add_item(
            title="You've entered not uniq account name",
            subtitle="Try again",
            icon=ICON_ERROR,
        )
        it.setvar(VARIABLES.cmd, ACCOUNTS_MANAGE_CMD.CMD_ADD_ACCOUNT.name)
        del_temp_accounts(wf)
        return wf

    do_account_action(wf, on_going_add, action, var_data)
    wf = process_account_creation(wf, query, on_going_add)

    it = wf.add_item(
        title="Start from beginning",
        subtitle="Just forgot already entered data about '{}' account".format(on_going_add.name),
        valid=True
    )
    it.setvar(VARIABLES.cmd, ACCOUNTS_MANAGE_CMD.CMD_ADD_ACCOUNT.name)
    it.setvar(VARIABLES.action, ACCOUNTS_ACTIONS.flush_ongoing)

    return wf


def list_accounts(wf):
    wf = get_accounts_list(
        wf,
        cmd_var=ACCOUNTS_MANAGE_CMD.CMD_ACCOUNT_SETTINGS.name,
        action_var=ACCOUNTS_ACTIONS.get_account_settings
    )
    return wf


def account_settings(wf):
    wf = Workflow3()
    gitlab_accounts = Accounts(get_accounts(wf))
    account = gitlab_accounts.get_acc(get_wf_variable(wf, VARIABLES.account))
    action = get_wf_variable(wf, VARIABLES.action)
    acc_setting = get_wf_variable(wf, VARIABLES.acc_setting)
    var_data = get_wf_variable(wf, VARIABLES.var_data)
    query = wf.args[-1]
    logger.debug("var_data: {} action: {} acc_setting: {} query: {}".format(var_data, action, acc_setting, query))

    logger.debug("action: {}, account: {}".format(action, account))

    if account:
        if action == ACCOUNTS_ACTIONS.get_account_settings:
            wf = get_account_settings(wf, account)

        if acc_setting:
            if action == ACCOUNTS_ACTIONS.save_account_settings:
                if acc_setting == "token":
                    wf.save_password(account.name, var_data)
                else:
                    account.update_setting(acc_setting, var_data)
                    gitlab_accounts.update_acc(account)
                    save_accounts(wf, gitlab_accounts)
                notify("Account '{}' setting '{}' has been changed".format(account.name, acc_setting))

                return wf

            elif action == ACCOUNTS_ACTIONS.update_account_settings:
                if acc_setting == "url":
                    query = get_validated_url(query)
                it = wf.add_item(
                    title="Changing '{}', enter to save new value".format(acc_setting),
                    subtitle="Please check new value: '{}'".format(query),
                    valid=True
                )
                it.setvar(VARIABLES.action, ACCOUNTS_ACTIONS.save_account_settings)
                it.setvar(VARIABLES.acc_setting, acc_setting)
                it.setvar(VARIABLES.var_data, query)

    else:
        return list_accounts(wf)
    return wf


def del_account(wf):
    account = get_wf_variable(wf, "account")
    action = get_wf_variable(wf, "action")
    logger.debug("action: {}, account: {}".format(action, account))

    if action == ACCOUNTS_ACTIONS.del_account and account:
        exists_accounts = get_accounts(wf)
        exists_accounts.pop(account)
        wf.delete_password(account)
        save_accounts(wf, exists_accounts)
        notify("Account '{}' has been deleted".format(account))
        wf.add_item(
            title="Account '{}' has been deleted".format(account),
            valid=False,
        )
    else:
        wf = get_accounts_list(
            wf,
            cmd_var=ACCOUNTS_MANAGE_CMD.CMD_DEL_ACCOUNT.name,
            action_var=ACCOUNTS_ACTIONS.del_account,
        )
    return wf


def main(wf, args):
    logger.debug("Accounts")
    logger.debug("args: {}".format(args))

    if args.list_accounts:
        logger.debug("List accounts")
        wf = list_accounts(wf)

    if args.acc_settings:
        logger.debug("Change account settings")
        wf = account_settings(wf)

    if args.add_acc:
        logger.debug("Add account")
        wf = add_account(wf)

    if args.del_acc:
        logger.debug("Delete account")
        wf = del_account(wf)

    wf.send_feedback()


if __name__ == '__main__':
    wf = Workflow3()
    logger = wf.logger
    logger.debug("Main")

    parser = argparse.ArgumentParser()
    parser.add_argument('-l', '--ls', dest='list_accounts', action='store_true')
    parser.add_argument('-a', '--add', dest='add_acc', action='store_true')
    parser.add_argument('-d', '--del', dest='del_acc', action='store_true')
    parser.add_argument('-s', '--set', dest='acc_settings', action='store_true')
    args = parser.parse_known_args()

    main = partial(main, args=args[0])

    sys.exit(wf.run(main))
