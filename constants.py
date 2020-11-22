from enum import Enum

CMD_SEARCH_ITEM = {
    'title': 'Search project in your GitLab',
    'valid': True,
}
CMD_UPDATE_ITEM = {
    'title': 'Update cache',
    'valid': True,
}
CMD_CLONE_ITEM = {
    'title': 'Clone repo',
    'valid': True
}
CMD_RELATED_LINKS_ITEM = {
    'title': 'Show repo related links',
    'valid': True
}
CMD_ACCOUNTS_ITEM = {
    'title': 'Add, list or delete accounts',
    'valid': True,
}
CMD_ACCOUNT_LIST_ITEM = {
    'title': 'Show accounts list',
    'valid': True,
}
CMD_ACCOUNT_SETTINGS_ITEM = {
    'title': 'Change an account settings',
    'valid': True,
}
CMD_ADD_ACCOUNT_ITEM = {
    'title': 'Add new gitlab account',
    'subtitle': 'Add account to keychain',
    'valid': True
}
CMD_DEL_ACCOUNT_ITEM = {
    'title': 'Del gitlab account',
    'subtitle': 'Remove account from keychain',
    'valid': True
}


class MAIN_MANAGE_CMD(Enum):
    CMD_SEARCH = CMD_SEARCH_ITEM
    CMD_UPDATE = CMD_UPDATE_ITEM
    CMD_ACCOUNTS = CMD_ACCOUNTS_ITEM


class ACCOUNTS_MANAGE_CMD(Enum):
    CMD_ACCOUNT_LIST = CMD_ACCOUNT_LIST_ITEM
    CMD_ADD_ACCOUNT = CMD_ADD_ACCOUNT_ITEM
    CMD_DEL_ACCOUNT = CMD_DEL_ACCOUNT_ITEM
    CMD_ACCOUNT_SETTINGS = CMD_ACCOUNT_SETTINGS_ITEM


class ACCOUNTS_ACTIONS:
    add_new_account = "add_new_account"
    add_url = "add_url"
    add_token = "add_token"
    flush_ongoing = "flush_ongoing"
    del_account = "del_account"
    get_account_settings = "get_account_settings"
    update_account_settings = "update_account_settings"
    add_project_visibility = "add_project_visibility"
    add_project_membership = "add_project_membership"
    save_account_settings = "save_account_settings"


class VARIABLES:
    cmd = "cmd"
    action = "action"
    account = "account"
    var_data = "var_data"
    acc_setting = "acc_setting"
