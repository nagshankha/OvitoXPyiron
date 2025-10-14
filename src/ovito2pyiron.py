import ovito
from ovito.modifiers import PythonModifier
from pyiron_workflow import Workflow
from .utils import make_function_node_from_dict

class Ovito2Pyiron:
    def __init__(self, ovito_state_filepath):
        ovito.scene.load(ovito_state_filepath)
        if len(ovito.scene.pipelines) != 1:
            raise NotImplementedError("This package supports Ovito scene "+
                                      "with only a single pipeline")
        self._imported_pipeline = ovito.scene.pipelines[0]

    @property
    def imported_pipeline(self):
        return self._imported_pipeline

    def _create_pyiron_workflow(self):

        wf = Workflow("structure_creation_with_OVITO")

        for i in len(self.imported_pipeline.modifiers):
            mod = self.imported_pipeline.modifiers[i]

            if isinstance(mod, ovito.modifiers.PythonModifier):
                # User-defined PythonModifier
                args_dict = vars(mod.delegate)

                @Workflow.wrap.as_function_node
                def func(args_dict = args_dict):
                    cls = type(mod.delegate)
                new_delegate = cls(**args_dict)

                new_mod = PythonModifier(function=new_delegate.modify)
                new_mod.delegate = new_delegate
                new_pipeline.modifiers.append(new_mod)

            else:
                # Built-in modifier
                cls = type(mod)
                arg_names = [
                    name for name, attr in vars(cls).items()
                    if type(attr) is property
                ]
                args_dict = {name: getattr(mod, name) for name in arg_names}
                new_pipeline.modifiers.append(cls(**args_dict))