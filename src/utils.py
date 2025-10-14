import numpy as np
import inspect
from pyiron_workflow import Workflow

def make_function_node_from_dict(name: str, param_info: dict, body_func: callable):
    """
    Dynamically create a pyiron_workflow function node with rich metadata.

    Args:
        name (str): Name of the function node.
        param_info (dict): Mapping of parameter name -> default.
        body_func (callable): Function body implementation. 

    Returns:
        callable: pyiron_workflow-compatible function node.
    """
    # Build inspect.Parameter list
    parameters = []
    for key, default in param_info.items():
        parameters.append(
            inspect.Parameter(
                name=key,
                kind=inspect.Parameter.POSITIONAL_OR_KEYWORD,
                default=default
            )
        )

    sig = inspect.Signature(parameters)

    # Create wrapper function that uses the signature
    def func_template(**kwargs):
        return body_func(**kwargs)

    # Attach metadata
    func_template.__name__ = name
    func_template.__signature__ = sig

    # Wrap as pyiron_workflow node
    wrapped = Workflow.wrap.as_function_node(func_template)
    return wrapped
