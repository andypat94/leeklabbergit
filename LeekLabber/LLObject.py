import numpy as np


class LLObjectParameter(object):
    PTYPE_BOOL  = 0
    PTYPE_INT   = 1
    PTYPE_FLOAT = 2
    PTYPE_STR   = 3
    PTYPE_NUMPY = 4

    def __init__(self, ref_obj, var_name, label=None, ptype=None, value_list=None, unit='', xvals=None, xlabel=None, xunit=None):
        super(LLObjectParameter, self).__init__()
        self.ref_obj = ref_obj
        self.var_name = var_name
        if label is None:
            label = var_name
        self.label = label
        if ptype is None:
            val = self.get_value()
            if isinstance(val, bool):
                ptype = self.PTYPE_BOOL
            elif isinstance(val, int):
                ptype = self.PTYPE_INT
            elif isinstance(val, float):
                ptype = self.PTYPE_FLOAT
            elif isinstance(val, str):
                ptype = self.PTYPE_STR
            elif isinstance(val, np.ndarray):
                ptype = self.PTYPE_NUMPY
                self.xvals = xvals
                self.xunit = xunit
                self.xlabel = xlabel
        self.ptype = ptype
        self.unit = unit

    def get_value(self):
        return getattr(self.ref_obj, self.var_name)

    def set_value(self, value):
        return setattr(self.ref_obj, self.var_name, value)


class LLObject(object):
    def __init__(self):
        self.LLObjectParameters = []

    def add_parameter(self, *args, **kwargs):
        param = LLObjectParameter(self, *args, **kwargs)
        self.LLObjectParameters.append(param)

    def get_parameter(self, label):
        for param in self.LLObjectParameters:
            if param.label == item:
                return param
        return None

    def __getitem__(self, item):
        if isinstance(item, str):
            return self.get_parameter(item)
        else:
            return None