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

        def pipeline_initiation():
            pipeline = Pipeline(source = PythonSource(function = 
                                        self.imported_pipeline.source.function))
            return pipeline
        
        pipeline_initiation.__qualname__ = pipeline_initiation.__name__
        pipeline_initiation_wrapped = Workflow.wrap.as_function_node(pipeline_initiation)        
        self.wf.pipeline_initiation = pipeline_initiation_wrapped()

        for i in range(len(self.imported_pipeline.modifiers)):
            mod = self.imported_pipeline.modifiers[i]

            if isinstance(mod, ovito.modifiers.PythonModifier):
                # User-defined PythonModifier

                def make_func(mod):
                    def func(pipeline, **kwargs):
                        cls = type(mod.delegate)
                        for key, value in kwargs:
                            setattr(cls, key, value)
                        new_mod = PythonModifier(delegate=cls())
                        pipeline.modifiers.append(new_mod)
                        return pipeline
                    return func

                func = make_func(mod)                
                args_dict = vars(mod.delegate)                
            else:
                # Built-in modifier
                cls = type(mod)

                def make_func(cls):
                    def func(pipeline, **kwargs):
                        new_mod = cls(**kwargs)
                        pipeline.modifiers.append(new_mod)
                        return pipeline
                    return func
                
                func = make_func(cls)
                arg_names = [
                    name for name, attr in vars(cls).items()
                    if type(attr) is property
                ]
                args_dict = dict([(name, getattr(mod, name)) for name in arg_names])

            node_name = mod.title if mod.title != '' else mod.__class__.__name__

            if i == 0:
                self.wf.modifier_1 = make_function_node_from_dict(node_name, 
                                                     args_dict, 
                                                     func)(pipeline = 
                                                             self.wf.pipeline_initiation
                                                     )
            else:
                setattr(self.wf, f"modifier_{i+1}", 
                        make_function_node_from_dict(node_name, 
                                                     args_dict, 
                                                     func)(
                                                         pipeline = getattr(
                                                             self.wf, 
                                                             f"modifier_{i}")
                                                     ))
                
