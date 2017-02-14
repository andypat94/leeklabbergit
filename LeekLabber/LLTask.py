from LeekLabber import *
import LeekLabber as LL


class LLTask(LLObject):
    def __init__(self, parent=None):
        super(LLTask,self).__init__(parent)

    def ensure_subtask(self, current, subtask):
        if current is None:
            return subtask(self)
        elif current.__class__.__name__ == subtask.__name__: # check they are exactly the same class (i.e. not even a subclass)
            return current
        else:
            current.remove()
            return subtask(self)

    def create_or_update_subtasks_internal(self):
        self.create_or_update_subtasks()
        # signal children to also create or update their subtasks
        for child in [child for child in self.ll_children if isinstance(child, LLTask)]:
            child.create_or_update_subtasks_internal()

    def prepare_experiment_internal(self):
        self.prepare_experiment()
        # prepare all child tasks also
        for child in [child for child in self.ll_children if isinstance(child, LLTask)]:
            child.prepare_experiment_internal()

    def submit_experiment_internal(self):
        self.clear_task_length()
        self.submit_experiment()
        # prepare all child tasks also
        for child in [child for child in self.ll_children if isinstance(child, LLTask)]:
            child.submit_experiment_internal()

    def process_experiment_internal(self):
        self.process_experiment()
        # allow all child tasks to process also
        for child in [child for child in self.ll_children if isinstance(child, LLTask)]:
            child.process_experiment_internal()

    def execute(self, exp_setup=None): #execute as the top level task on an experimental setup as passed in
        if exp_setup is None:
            exp_setup =  LL.LL_ROOT.expsetups.ll_children[0]
        exp_setup.prepare_experiment()
        self.prepare_experiment_internal()
        exp_setup.plan_experiment()
        self.submit_experiment_internal()
        exp_setup.execute()
        self.process_experiment_internal()

    def prepare_microwave_drive(self, device, freq, power, pulsed, measured):
        device.prepare_microwave_drive(freq, power, pulsed, measured)

    def get_timeslot(self, device, time, freq, power):
        self.update_task_length(time)
        return device.get_timeslot(time, freq, power)

    def submit_pulse(self, device, DC_I, DC_Q, freq, power):
        device.submit_pulse(DC_I, DC_Q, freq, power)

    def submit_delay(self, delay_time):
        self.update_task_length(delay_time)

    def clear_task_length(self):
        self.task_length = 0.

    def update_task_length(self, length):
        if(length>self.task_length):
            self.task_length = length


class LLTaskDelay(LLTask):
    def __init__(self, parent=None):
        super(LLTaskDelay,self).__init__(parent)

        self.p_delay = 0.

        self.add_parameter('p_delay', label="Delay Time", unit='s')

    def create_or_update_subtasks(self):
        pass

    def prepare_experiment(self):
        pass

    def submit_experiment(self):
        self.submit_delay(self.p_delay)

    def process_experiment(self):
        pass
