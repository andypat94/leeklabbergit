from LeekLabber import *
import LeekLabber as LL

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

    def submit_experiment(self):
        # prepare all child tasks also
        for child in [child for child in self.ll_children if isinstance(child, LLTask)]:
            child.submit_experiment()

    def process_experiment(self):
        # allow all child tasks to process also
        for child in [child for child in self.ll_children if isinstance(child, LLTask)]:
            child.process_experiment()

    def execute(self, exp_setup=None): #execute as the top level task on an experimental setup as passed in
        if exp_setup is None:
            exp_setup =  LL.LL_ROOT.expsetups.ll_children[0]
        exp_setup.prepare_experiment()
        self.prepare_experiment()
        exp_setup.plan_experiment()
        self.submit_experiment()
        exp_setup.execute()
        self.process_experiment()
