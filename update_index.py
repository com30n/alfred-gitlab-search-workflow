#!/usr/bin/env python

from __future__ import print_function, unicode_literals

import os
import sys
import json
import sqlite3

from time import time
from urlparse import urljoin

from utils import get_wf_variable
from workflow import Workflow3, PasswordNotFound, web, util
from workflow.notify import notify

from accounts import get_accounts, Accounts, Account

from config import INDEX_DB, DATA_FILE

log = None


def get_all_pages(wf, account):
    result = []
    notification_title = "Loading all projects..."
    notification_text_template = "From {base_url} loading page: {page}"
    gitlab_api_base = urljoin(account.url, 'api/v4/')
    gitlab_api_per_page = 'per_page=100'
    membership = "&membership={}".format(account.project_membership) if account.project_membership else ""
    visibility = "&visibility={}".format(account.project_visibility) if account.project_visibility else ""

    gitlab_api_projects_url = '{gitlab_api}?private_token={gitlab_token}&simple={simple}&{per_page}{membership}{visibility}'.format(
        gitlab_api=urljoin(gitlab_api_base, 'projects'),
        gitlab_token=account.token,
        per_page=gitlab_api_per_page,
        simple=True,
        membership=membership,
        visibility=visibility,
    )
    log.debug("api url: {}".format(gitlab_api_projects_url))
    notify(notification_title, notification_text_template.format(base_url=account.url, page=1))
    response = web.get('{api_url}&page={page}'.format(api_url=gitlab_api_projects_url, page=0))
    response.raise_for_status()
    result.extend(response.json())

    while response.headers['X-Next-Page'] != '':
        notify(
            notification_title,
            notification_text_template.format(base_url=account.url, page=response.headers['X-Next-Page'])
        )
        response = web.get(
            '{api_url}&page={page}'.format(api_url=gitlab_api_projects_url, page=response.headers['X-Next-Page']))
        response.raise_for_status()
        result.extend(response.json())

    return result


def load_all_projects(wf):
    log.debug('start updating the cache')
    wf = Workflow3()

    all_accounts = None
    try:
        all_accounts = Accounts(get_accounts(wf))
    except PasswordNotFound:  # API key has not yet been set
        notify(
            "WARNING",
            "No API key saved"
        )

        log.error('No API key saved')

    log.debug('loading accounts...')

    if not all_accounts:
        # just paste gitlab url to the variables page and token to the keychain and start using the workflow
        url = get_wf_variable(wf, "gitlab_url")
        token = get_wf_variable(wf, "gitlab_token")
        all_accounts = Account(
            {"simple_account": {
                "url": url,
                "token": token,
                "project_membership": "true",
                "project_visibility": "internal",
            }}
        )

    log.info('Removing cache: {}'.format(DATA_FILE))
    # if os.path.exists(DATA_FILE):
    #     return
    try:
        os.remove(DATA_FILE)
    except:
        pass

    result = []
    for acc_name, acc_settings in all_accounts.dict.items():
        log.info('base api url is: {url}; api token is: {token_name}'.format(
            url=acc_settings.url,
            token_name=acc_settings.token)
        )
        result.extend(get_all_pages(wf, account=acc_settings))

    with open(DATA_FILE, 'w+') as fp:
        json.dump(result, fp)

    notify(
        "Cache was updated",
        "Was loaded {projects} projects from all gitlab instances".format(projects=len(result))
    )


def create_index_db():
    """Create a "virtual" table, which sqlite3 uses for its full-text search
    Given the size of the original data source (~45K entries, 5 MB), we'll put
    *all* the data in the database.
    Depending on the data you have, it might make more sense to only add
    the fields you want to search to the search DB plus an ID (included here
    but unused) with which you can retrieve the full data from your full
    dataset.
    """
    log.info('Creating index database')
    con = sqlite3.connect(INDEX_DB)
    with con:
        cur = con.cursor()
        # cur.execute(
        #     "CREATE TABLE books(id INT, author TEXT, title TEXT, url TEXT)")
        cur.execute(
            str(
                "CREATE VIRTUAL TABLE gitlab USING fts3(id, name, name_with_namespace, web_url, ssh_url_to_repo, http_url_to_repo)"
            )
        )


def update_index_db():
    """Read in the data source and add it to the search index database"""
    start = time()
    log.info('Updating index database')
    con = sqlite3.connect(INDEX_DB)
    count = 0
    with con:
        cur = con.cursor()
        with open(DATA_FILE, 'rb+') as fp:
            projects = json.load(fp)

        for project in projects:
            cur.execute(str("SELECT * FROM gitlab WHERE name_with_namespace=?"), (project["name_with_namespace"],))
            fetch = cur.fetchone()
            if fetch:
                pass
            else:
                cur.execute(
                    str("""
                    INSERT OR IGNORE INTO
                    gitlab (id, name, name_with_namespace, web_url, ssh_url_to_repo, http_url_to_repo)
                    VALUES (?, ?, ?, ?, ?, ?)
                    """),
                    (
                        project["id"],
                        project["name"],
                        project["name_with_namespace"],
                        project["web_url"],
                        project["ssh_url_to_repo"],
                        project["http_url_to_repo"],
                    )
                )
            # log.info('Added {} by {} to database'.format(title, author))
            count += 1
    log.info('{} items added/updated in {:0.3} seconds'.format(
        count, time() - start))


def main(wf):
    log.info("{}".format(INDEX_DB))
    load_all_projects(wf)

    if not os.path.exists(INDEX_DB):
        create_index_db()

    update_index_db()
    log.info('Index database update finished')


if __name__ == '__main__':
    wf = Workflow3()
    log = wf.logger
    sys.exit(wf.run(main))
