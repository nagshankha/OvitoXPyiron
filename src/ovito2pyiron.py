import ovito
from ovito.modifiers import PythonModifier
from ovito.pipeline import Pipeline, PythonSource
from pyiron_workflow import Workflow
from .utils import make_function_node_from_dict

class Ovito2Pyiron:
    def __init__(self, ovito_state_filepath):
        ovito.scene.load(ovito_state_filepath)
        if len(ovito.scene.pipelines) != 1:
            raise NotImplementedError("This package supports Ovito scene "+
                                      "with only a single pipeline")
        self._imported_pipeline = ovito.scene.pipelines[0]
        self._create_pyiron_workflow()

    @property
    def imported_pipeline(self):
        return self._imported_pipeline

    def _create_pyiron_workflow(self):

        self.wf = Workflow("structure creation with OVITO")

        @Workflow.wrap.as_function_node
        def pipeline_initiation():
            pipeline = Pipeline(source = PythonSource(function = 
                                        self.imported_pipeline.source.function))
            return pipeline
        
        self.wf.pipeline_initiation = pipeline_initiation()

        for i in range(len(self.imported_pipeline.modifiers)):
            mod = self.imported_pipeline.modifiers[i]

            if isinstance(mod, ovito.modifiers.PythonModifier):
                # User-defined PythonModifier

                def func(pipeline, **kwargs):
                    cls = type(mod.delegate)
                    for key, value in kwargs:
                        setattr(cls, key, value)
                    new_mod = PythonModifier(delegate=cls())
                    pipeline.modifiers.append(new_mod)
                    return pipeline
                
                args_dict = vars(mod.delegate)                
            else:
                # Built-in modifier
                cls = type(mod)

                def func(pipeline, **kwargs):
                    new_mod = cls(**kwargs)
                    pipeline.modifiers.append(new_mod)
                    return pipeline

                arg_names = [
                    name for name, attr in vars(cls).items()
                    if type(attr) is property
                ]
                args_dict = {name: getattr(mod, name) for name in arg_names}

            if i == 0:
                self.wf.modifier_1 = make_function_node_from_dict(mod.title, 
                                                     args_dict, 
                                                     func)(pipeline = 
                                                             self.wf.pipeline_initiation.pipeline
                                                     )
            else:
                setattr(self.wf, f"modifier_{i+1}", 
                        make_function_node_from_dict(mod.title, 
                                                     args_dict, 
                                                     func)(
                                                         pipeline = getattr(
                                                             self.wf, 
                                                             f"modifier_{i}").pipeline
                                                     ))
                
