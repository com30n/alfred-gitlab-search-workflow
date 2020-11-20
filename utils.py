import os
from workflow import Workflow3

wf = Workflow3()


def get_wf_variable(var_name):
    """Returns workflow variable, if exists. If doesn't - return value from OS environ."""
    if wf.variables and wf.getvar(var_name):
        return wf.getvar(var_name)
    else:
        return os.getenv(var_name)


