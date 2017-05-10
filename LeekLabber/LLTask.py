from LeekLabber import *
import LeekLabber as LL


class LLTask(LLObject):
    def __init__(self, parent=None):
        super(LLTask,self).__init__(parent)

        self.p_dependences = []
        self.p_pulses = []

        self.add_parameter('p_dependences', label="Task Dependences", ptype=LLObjectParameter.PTYPE_LLOBJECT_LIST, viewable=False, read_only=True)
        self.add_parameter('p_pulses', label="Pulses", ptype=LLObjectParameter.PTYPE_LLOBJECT_LIST, viewable=False, read_only=True)

    def add_pulse(self):
        pulse = LLPulse()
        self.p_pulses.append(pulse)
        return pulse

    def dependences_submitted(self):
        submitted = True
        for task in self.p_dependences:
            submitted = submitted and task.submitted
        return submitted

    def dependences_finished_time(self):
        t = self.ll_parent.timeslot_start
        for task in self.p_dependences:
            if task.timeslot_end>t:
                t = task.timeslot_end
        return t

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
        self.submitted = False

    def submit_experiment_internal(self, timeslot_start=0.0, increment=0):
        self.timeslot_start = timeslot_start

        print(("    "*increment)+ "BEGIN " +  self.__class__.__name__ + " @ " + str(timeslot_start))

        self.clear_task_length()
        self.submit_experiment()

        ordered_children = []
        child_task_lengths = 0.

        something_was_run = True
        while len(ordered_children)<len(self.ll_children) and something_was_run:
            something_was_run = False
            for child in [child for child in self.ll_children if isinstance(child, LLTask)]:
                if (not child.submitted) and child.dependences_submitted():
                    something_was_run = True
                    child.submit_experiment_internal(child.dependences_finished_time(),increment+1)
                    child_task_lengths += child.get_task_length()
                    ordered_children.append(child)
        if not something_was_run:
            print("Cyclic dependencies in task structure.  Experiment will not complete succesffully.")
        else:
            # we reorder the children into execution order as we go, to speed up subsequent runs
            self.ll_children = ordered_children

        self.update_task_length(child_task_lengths)
        # at this point, this is the final task length ( all three options of submitted pulse lengths, submitted delays and child lengths have been considered)
        self.timeslot_end = timeslot_start + self.get_task_length()
        self.submitted = True

        print(("    "*increment)+ "END "+ self.__class__.__name__ + " @ " + str(self.timeslot_end))

    def process_experiment_internal(self):
        # process child tasks first
        for child in [child for child in self.ll_children if isinstance(child, LLTask)]:
             child.process_experiment_internal()

        self.process_experiment()

    def execute(self, exp_setup=None): #execute as the top level task on an experimental setup as passed in
        if exp_setup is None:
            exp_setup =  LL.LL_ROOT.expsetups.ll_children[0]
        exp_setup.prepare_experiment()
        self.prepare_experiment_internal()
        # todo: consider not replanning the experiment unless necessary (i.e. if submit_experiment fails?)
        exp_setup.plan_experiment()
        self.submit_experiment_internal()
        length = self.get_task_length()
        if length > 1e-3: #todo make this a configurable parameter?
            length = 1e-3
        exp_setup.execute(length)
        self.process_experiment_internal()

    def prepare_pulse(self, pulse, device, frequency, power, pulsed=False, measured=False):
        pulse.prepare_pulse(device,frequency,power,pulsed,measured)

    def get_timebase(self, pulse, length):
        self.update_task_length(length)
        return pulse.get_timebase(self.timeslot_start, length)

    def submit_pulse(self, pulse, dc_i, dc_q, basis_phase=0.0):
        pulse.submit_pulse(dc_i, dc_q, basis_phase)

    def submit_delay(self, delay_time):
        self.update_task_length(delay_time)

    def clear_task_length(self):
        self.task_length = 0.

    def get_task_length(self):
        return self.task_length

    def update_task_length(self, length):
        if(length>self.task_length):
            self.task_length = length


