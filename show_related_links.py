import sys

from utils import get_wf_variable

from workflow import Workflow3, ICON_WEB, ICON_WARNING


def main(wf):
    """Generates and shows repo-related links e.g. 'Pipelines' or 'Commits'"""

    project_url = get_wf_variable("project_url")
    if not project_url:
        wf.add_item(
            title="No one project was chosen",
            valid=True,
            icon=ICON_WARNING,
        )

        wf.send_feedback()
        return

    urls_path_to_add = {
        'Files': 'tree/master',
        'Commits': 'commits/master',
        'Branches': 'branches',
        'Tags': 'tags',
        'Pipelines': 'pipelines'
    }

    for name, path in urls_path_to_add.items():
        web_url = "{}/{}".format(project_url, path)
        it = wf.add_item(
            title=name,
            subtitle=web_url,
            valid=True,
            icon=ICON_WEB,
        )
        it.setvar("web_url", web_url)

    wf.send_feedback()


if __name__ == '__main__':
    wf = Workflow3()
    # Assign Workflow logger to a global variable for convenience
    log = wf.logger
    sys.exit(wf.run(main))
