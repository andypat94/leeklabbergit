class LLObjectParameter(object):
    def __init__(self, refLLObj, strVarName):
        super(object, self).__init__()
        self.refLLObj = refLLObj
        self.strParam = strVarName

    def getValue(self):
        return getattr(self.refLLObj, self.strVarName)

    def setValue(self, value):
        return setattr(self.refLLObj, self.strVarName, value)


class LLObject(object):
    def __init__(self):
        super(object, self).__init__()
        self.LLObjectParameters = []
