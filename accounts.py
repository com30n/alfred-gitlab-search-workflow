import sys
from urlparse import urlparse

from collections import OrderedDict

from workflow import Workflow3 as Workflow, ICON_WEB, PasswordNotFound, Workflow3

wf = Workflow()
logger = wf.logger

# indexes of values in accounts list
url_id = 0
token_id = 1
token_name_id = 2


def get_validated_url(url):
    url = urlparse(url)
    return "https://{url_netloc}".format(url_netloc=url.netloc)


class ManageGitlabAccounts:
    # pointer is indicator for accounts length list
    ACCOUNT_POINTER_URL_FSTRING = 'gitlab_account_url_{pointer}'
    ACCOUNT_POINTER_TOKEN_FSTRING = 'gitlab_account_token_{pointer}'
    ACCOUNT_POINTER_TOKEN_NAME_FSTRING = 'gitlab_account_token_name_{pointer}'

    _token_name = None
    _token = None
    _url = None

    def __init__(self):
        pass

    @classmethod
    def add_token_name(cls, token_name):
        cls._token_name = token_name

    @classmethod
    def add_token(cls, token):
        cls._token = token

    @classmethod
    def add_url(cls, url):
        cls._url = url

    @classmethod
    def save_account(cls):

        if not cls._token_name:
            logger.warn('Can\'t save account. Didn\'t set token name.')
            return 1

        if not cls._token:
            logger.warn('Can\'t save account. Didn\'t set token.')
            return 1

        if not cls._url:
            logger.warn('Can\'t save account. Didn\'t set url.')
            return 1

        logger.info('Adding new account.')
        # pointer is indicator for accounts length list
        pointer = cls._get_pointer()

        cls._change_accounts_list(cls._token_name, cls._token, cls._url, pointer)
        cls._token_name = None
        cls._token = None
        cls._url = None

    @classmethod
    def get_url_by_id(cls, account_id):
        account = cls._get_account_by_id(int(account_id))
        return account[url_id]

    @classmethod
    def get_token_by_id(cls, account_id):
        account = cls._get_account_by_id(int(account_id))
        return account[token_id]

    @classmethod
    def get_token_name_by_id(cls, account_id):
        account = cls._get_account_by_id(int(account_id))
        return account[token_name_id]

    @classmethod
    def del_account(cls, account_id=None):
        logger.info('Deleting account: pointer={}'.format(account_id))
        account_id = int(account_id)
        # get all known accounts
        all_gitlab_accounts = cls._load_all_accounts()
        if not all_gitlab_accounts:
            logger.warn('Cannot delete account. No account was created')
            return 'Cannot delete account. No account was created'

        # just copy of dict, not to iterate through a mutable dict
        _temp_dict = all_gitlab_accounts.copy()
        deleted_acc = _temp_dict.pop(account_id)

        if not deleted_acc:
            logger.info("Account for delete doesn\'t exist.")
            return 'Account for delete doesn\'t exist.'

        # just save new accounts dict
        if _temp_dict:
            logger.debug('New accounts list: {}'.format(_temp_dict))
            # save new accounts dict (and get new length of this dict)
            k_counter = 0
            for k_counter, v_url_token_tuple in enumerate(_temp_dict.values()):
                cls._change_accounts_list(
                    token=v_url_token_tuple[token_id],
                    url=v_url_token_tuple[url_id],
                    token_name=v_url_token_tuple[token_name_id],
                    account_id=k_counter
                )

            accounts_list_len = k_counter

        # if deleted all accounts:
        else:
            logger.info('All accounts was delete.')
            accounts_list_len = 0

        # save new pointer of accounts length
        cls._set_pointer(accounts_list_len)
        return 'Account deleted from keychain.'

    @classmethod
    def print_all_accounts(cls):
        all_gitlab_accounts = cls._load_all_accounts()
        logger.debug('Loaded accounts: {}'.format(all_gitlab_accounts))

        for k_pointer, v_url_token_name in all_gitlab_accounts.items():
            wf.add_item(
                title=str(v_url_token_name[token_name_id]),
                subtitle=v_url_token_name[url_id],
                arg=str(k_pointer),
                valid=True,
                icon=ICON_WEB,
            )
        wf.send_feedback()
        return 0

    @classmethod
    def _get_account_by_id(cls, account_id):
        all_account = cls._load_all_accounts()
        return all_account[int(account_id)]

    @classmethod
    def _change_accounts_list(cls, token_name, token, url, account_id):
        account_id = str(account_id)
        logger.debug(
            'Save account changes in keychain. Account info: pointer={}, url={}, token={}'.format(
                token, url,
                account_id
            )
        )

        # save (or replace exists) new strings with tokens and url of gitlab
        wf.save_password(cls.ACCOUNT_POINTER_URL_FSTRING.format(pointer=account_id), url)
        wf.save_password(cls.ACCOUNT_POINTER_TOKEN_FSTRING.format(pointer=account_id), token)
        wf.save_password(cls.ACCOUNT_POINTER_TOKEN_NAME_FSTRING.format(pointer=account_id), token_name)

        cls._set_pointer(account_id)

        logger.debug('Changes saved successful.')

    @classmethod
    def _load_all_accounts(cls):
        logger.info('Loading accounts list.')
        pointer = cls._get_pointer()
        # ordered dict needed to second for in del_gitlab_account() func
        dict_of_gitlab_accounts = OrderedDict()
        try:
            for i in range(0, pointer):
                dict_of_gitlab_accounts[i] = (
                    wf.get_password(
                        cls.ACCOUNT_POINTER_URL_FSTRING.format(pointer=i)
                    ),
                    wf.get_password(
                        cls.ACCOUNT_POINTER_TOKEN_FSTRING.format(pointer=i)
                    ),
                    wf.get_password(
                        cls.ACCOUNT_POINTER_TOKEN_NAME_FSTRING.format(pointer=i)
                    ),
                )
        except PasswordNotFound:
            # if account with this pointer not exists, move pointer to last exist
            logger.warning('Pointer "{}" does not exist. Set pointer to {}'.format(i, i - 1))
            cls._set_pointer(i - 1)

        logger.info('Loaded accounts list: {}'.format(dict_of_gitlab_accounts))
        return dict_of_gitlab_accounts

    @classmethod
    def _get_pointer(cls):
        logger.info('Getting pointer from keychain.')
        try:
            pointer = int(wf.get_password('gitlab_pointer'))
        except PasswordNotFound:
            logger.warn('Cannot get pointer from keychain')
            pointer = 0
        except ValueError:
            logger.warn(ValueError)
            pointer = 0
        logger.info('Pointer is: {}'.format(pointer))
        return pointer

    @classmethod
    def _set_pointer(cls, pointer):
        pointer = int(pointer)
        if pointer < 0:
            pointer = 0
        logger.info('Moving pointer...')
        logger.debug('Pointer to set: {}'.format(pointer))

        # it need for use inside the range func
        pointer += 1

        wf.save_password('gpitlab_pointer', str(pointer))
        logger.info('Pointer was set successful.')


# WIP
def main(wf):
    pass


if __name__ == '__main__':
    wf = Workflow3()
    logger = wf.logger

    sys.exit(wf.run(main))
