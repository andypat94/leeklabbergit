from LeekLabber import LLTask

class LLTaskDelay(LLTask):
    def __init__(self, parent=None):
        super(LLTaskDelay,self).__init__(parent)

        self.p_delay = 10.0e-6

        self.add_parameter('p_delay', label="Delay Time", unit='s')

    def create_or_update_subtasks(self):
        pass

    def prepare_experiment(self):
        pass

    def submit_experiment(self):
        self.submit_delay(self.p_delay)

    def process_experiment(self):
        pass
