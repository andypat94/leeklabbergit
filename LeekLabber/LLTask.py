from LeekLabber import *

class LLTask(LLObject):
    def __init__(self, parent=None):
        super(LLTask,self).__init__(parent)

    def create_or_update_subtasks(self):
        # signal children to also create or update their subtasks
        for child in [child for child in self.ll_children if isinstance(child, LLTask)]:
            child.create_or_update_subtasks()

    def prepare_experiment(self):
        # prepare all child tasks also
        for child in [child for child in self.ll_children if isinstance(child, LLTask)]:
            child.prepare_experiment()

    def process_experiment(self):
        # allow all child tasks to process also
        for child in [child for child in self.ll_children if isinstance(child, LLTask)]:
            child.process_experiment()


