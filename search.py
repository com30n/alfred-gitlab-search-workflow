# -*- coding: utf-8 -*-
import os
import struct
import sys
from time import time

import sqlite3

from urlparse import urlparse

from config import INDEX_DB
from workflow import Workflow3, ICON_WEB, ICON_WARNING, ICON_INFO, web

from workflow.background import run_in_background, is_running

ICON_TERM = os.path.join('/System/Library/CoreServices/CoreTypes.bundle/Contents/Resources',
                         'ExecutableBinaryIcon.icns')
wf = Workflow3()
logger = wf.logger


def check_gitlab_url(url):
    parsed_url = urlparse(url)
    if not parsed_url.netloc:
        raise Exception('Please, verify the presence of the net scheme (http:// or https://)')

    response = web.get('https://{url}/'.format(url=parsed_url.netloc))
    response.raise_for_status()


# Search ranking function
# Adapted from http://goo.gl/4QXj25 and http://goo.gl/fWg25i
def make_rank_func(weights):
    """`weights` is a list or tuple of the relative ranking per column.
    Use floats (1.0 not 1) for more accurate results. Use 0 to ignore a
    column.
    """

    def rank(matchinfo):
        # matchinfo is defined as returning 32-bit unsigned integers
        # in machine byte order
        # http://www.sqlite.org/fts3.html#matchinfo
        # and struct defaults to machine byte order
        bufsize = len(matchinfo)  # Length in bytes.
        matchinfo = [struct.unpack(b'I', matchinfo[i:i + 4])[0]
                     for i in range(0, bufsize, 4)]
        it = iter(matchinfo[2:])
        return sum(x[0] * w / x[1]
                   for x, w in zip(zip(it, it, it), weights)
                   if x[1])

    return rank


def main(wf):
    query = wf.args[0]

    if wf.update_available:
        # Add a notification to top of Script Filter results
        wf.add_item('New version available',
                    'Action this item to install the update',
                    autocomplete='workflow:update',
                    icon=ICON_INFO)

    index_exists = True

    # Create index if it doesn't exist
    if not os.path.exists(INDEX_DB):
        index_exists = False
        run_in_background('indexer', ['/usr/bin/python', 'update_index.py'])

    # Can't search without an index. Inform user and exit
    if not index_exists:
        wf.add_item('Creating search index…', 'Please wait a moment',
                    icon=ICON_INFO)
        wf.send_feedback()
        return

    # Inform user of update in case they're looking for something
    # recently added (and it isn't there)
    if is_running('indexer'):
        wf.add_item('Updating search index…',
                    'Fresher results will be available shortly',
                    icon=ICON_INFO)

    # Search!
    start = time()
    db = sqlite3.connect(INDEX_DB)
    # Set ranking function with weightings for each column.
    # `make_rank_function` must be called with a tuple/list of the same
    # length as the number of columns "selected" from the database.
    # In this case, `url` is set to 0 because we don't want to search on
    # that column
    # id, name, name_with_namespace, web_url, ssh_url_to_repo, http_url_to_repo
    db.create_function('rank', 1, make_rank_func((0, 1.0, 0.9, 0, 0, 0)))
    cursor = db.cursor()

    try:
        sql = """
        SELECT id, name, name_with_namespace, web_url, ssh_url_to_repo, http_url_to_repo 
        FROM (
            SELECT rank(matchinfo(gitlab))
            AS r, id, name, name_with_namespace, web_url, ssh_url_to_repo, http_url_to_repo
            FROM gitlab WHERE gitlab MATCH "%s*"
        )
      ORDER BY r DESC LIMIT 100
      """ % query
        logger.info(sql)
        cursor.execute(sql)
        results = cursor.fetchall()
    except sqlite3.OperationalError as err:
        # If the query is invalid, show an appropriate warning and exit
        if b'malformed MATCH' in err.message:
            wf.add_item('Invalid query', icon=ICON_WARNING)
            wf.send_feedback()
            return
        # Otherwise raise error for Workflow to catch and log
        else:
            raise err

    if not results:
        wf.add_item('No matches', 'Try a different query', icon=ICON_WARNING)

    logger.info('{} results for `{}` in {:0.3f} seconds'.format(
        len(results), query, time() - start))

    # Output results to Alfred
    for (_, name, name_with_namespace, web_url, ssh_url_to_repo, http_url_to_repo) in results:
        it = wf.add_item(
            title=name_with_namespace,
            subtitle=web_url,
            arg=name,
            valid=True,
            icon=ICON_WEB,
        )
        it.setvar("web_url", web_url)
        it.setvar("ssh_url_to_repo", ssh_url_to_repo)
        it.setvar("http_url_to_repo", http_url_to_repo)

        mod = it.add_modifier(
            key="shift",
            subtitle="Show git clone options",
            valid=True
        )
        mod.setvar("cmd", "CMD_CLONE")

        mod = it.add_modifier(
            key="fn",
            subtitle="Show some related links",
            arg=name,
            valid=True,
        )
        mod.setvar("cmd", "CMD_RELATED_LINKS")
        mod.setvar("project_url", web_url)

    wf.send_feedback()


if __name__ == "__main__":
    wf = Workflow3(update_settings={
        # Your username and the workflow's repo's name.
        'github_slug': 'com30n/alfred-gitlab-search-workflow',

        # The version (i.e. release/tag) of the installed workflow.
        # If you've set a Workflow Version in Alfred's workflow
        # configuration sheet or if a `version` file exists in
        # the root of your workflow, this key may be omitted
        # 'version': __version__,

        # Optional number of days between checks for updates.
        'frequency': 1,

        # Force checking for pre-release updates.
        # This is only recommended when distributing a pre-release;
        # otherwise allow users to choose whether they want
        # production-ready or pre-release updates with the
        # `prereleases` magic argument.
        # 'prereleases': '-beta' in __version__
    })
    logger = wf.logger

    sys.exit(wf.run(main))
