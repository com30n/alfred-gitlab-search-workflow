import os
import sys
from utils import get_wf_variable
from workflow import Workflow3

ICON_TERM = os.path.join('/System/Library/CoreServices/CoreTypes.bundle/Contents/Resources',
                         'ExecutableBinaryIcon.icns')


def get_clone_links(wf):
    try:
        ssh_url_to_repo = wf.getvar("ssh_url_to_repo")
        http_url_to_repo = wf.getvar("http_url_to_repo")
        wf.add_item(
            title='Clone by SSH',
            subtitle=ssh_url_to_repo,
            arg=ssh_url_to_repo,
            valid=True,
            icon=ICON_TERM,
        )
        wf.add_item(
            title='Clone by HTTPS',
            subtitle=http_url_to_repo,
            arg=http_url_to_repo,
            valid=True,
            icon=ICON_TERM,
        )

        wf.send_feedback()

    except Exception as e:
        logger.exception(e)
        sys.stdout.write('1')

    return


def main(wf):
    ssh_url_to_repo = get_wf_variable("ssh_url_to_repo")
    http_url_to_repo = get_wf_variable("http_url_to_repo")

    wf.add_item(
        title='Clone by SSH',
        subtitle=ssh_url_to_repo,
        arg=ssh_url_to_repo,
        valid=True,
        icon=ICON_TERM,
    )
    wf.add_item(
        title='Clone by HTTPS',
        subtitle=http_url_to_repo,
        arg=http_url_to_repo,
        valid=True,
        icon=ICON_TERM,
    )

    wf.send_feedback()


if __name__ == "__main__":
    wf = Workflow3()
    logger = wf.logger
    logger.debug(wf.args)
    logger.debug(wf.variables)
    main(wf)
