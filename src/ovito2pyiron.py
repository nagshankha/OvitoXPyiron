import ovito

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
        for i in len(self.imported_pipeline.modifiers)