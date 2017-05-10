from LLSimpleTasks import *
#from LLMicrowaveTasks import *
from LLTasksSingleQubit import *

# for grabbing tasks names
import sys
import inspect

LLTASK_MODULES =  inspect.getmembers(sys.modules[__name__], lambda(m): inspect.ismodule(m) and m.__name__.startswith('LeekLabber.LLTasks'))
LLTASK_MODULENAMES = [m[0] for m in LLTASK_MODULES]
LLTASK_MODULES = [m[1] for m in LLTASK_MODULES]
LLTASK_CLASSNAMES = [[c[0] for c in inspect.getmembers(module, lambda(c): inspect.isclass(c) and c.__module__.startswith(module.__name__))] for module in LLTASK_MODULES]