import os
from workflow import Workflow3

wf = Workflow3()


def get_wf_variable(wf, var_name, default=""):
    """Returns workflow variable, if exists. If doesn't - return value from OS environ."""
    if wf.variables and wf.getvar(var_name):
        result = wf.getvar(var_name)
    else:
        result = os.getenv(var_name)

    if not result:
        return default
    return result

def merge_two_dicts(x, y):
    z = x.copy()  # start with x's keys and values
    z.update(y)  # modifies z with y's keys and values & returns None
    return z
