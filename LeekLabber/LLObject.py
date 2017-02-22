import numpy as np
import xml.etree.ElementTree as xmlet
import base64
from ast import literal_eval
import LeekLabber as LL
from ctypes import *
from LeekLabber import *

class LLObjectParameter(object):
    PTYPE_BOOL  = 0
    PTYPE_INT   = 1
    PTYPE_FLOAT = 2
    PTYPE_STR   = 3
    PTYPE_NUMPY = 4
    PTYPE_LLOBJECT = 5
    PTYPE_LLPARAMETER = 6
    PTYPE_LLPARAMETER_LIST = 7
    PTYPE_LLOBJECT_LIST = 8
    PTYPE_UNKNOWN_LIST = 254
    PTYPE_UNKNOWN = 255

    def __init__(self, ref_obj, var_name, label=None, ptype=None, value_list=None, unit='', xvals=None, xlabel=None, xunit=None, onChange=None):
        super(LLObjectParameter, self).__init__()
        self.binary_share_location = 0
        self.ref_obj = ref_obj
        self.var_name = var_name
        if label is None:
            label = var_name
        self.label = label
        self.onChange=onChange
        if ptype is None:
            val = self.get_value()
            if isinstance(val, list):
                if len(val)>0:
                    if isinstance(val[0], LLObjectParameter):
                        ptype = self.PTYPE_LLPARAMETER_LIST
                    if isinstance(val[0], LLObject):
                        ptype = self.PTYPE_LLOBJECT_LIST
                    else:
                        ptype = self.PTYPE_UNKNOWN_LIST
                else:
                    ptype = self.PTYPE_UNKNOWN_LIST
            elif isinstance(val, LLObject):
                ptype =  self.PTYPE_LLOBJECT
            elif isinstance(val, LLObjectParameter):
                ptype = self.PTYPE_LLPARAMETER
            elif isinstance(val, bool):
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

    def get_xvals(self):
        return getattr(self.ref_obj, self.xvals)

    def set_xvals(self, value):
        return setattr(self.ref_obj, self.xvals, value)


    def set_value(self, value):
        retval = setattr(self.ref_obj, self.var_name, value)
        if self.onChange is None:
            pass
        else:
            self.onChange()
        return retval

    def get_abs_path(self, topobj=None):
        myIndex = self.ref_obj.ll_params.index(self)
        return (self.ref_obj.get_abs_path(topobj),myIndex)

    def create_xml_element(self, parent_element=None, topobj=None):
        if parent_element is None:
            element = xmlet.Element(self.label)
        else:
            element = xmlet.SubElement(parent_element, self.label)

        val = self.get_value()

        if self.ptype in (self.PTYPE_BOOL,self.PTYPE_INT,self.PTYPE_FLOAT,self.PTYPE_STR):
            element.text = str(val)
        elif self.ptype in (self.PTYPE_NUMPY,):
            element.set('shape', str(val.shape))
            element.set('dtype', str(val.dtype.str))
            element.text = base64.b64encode(val)
        elif self.ptype in (self.PTYPE_LLOBJECT,self.PTYPE_LLPARAMETER,):
            if val is None:
                element.text = ""
            else:
                element.text = str(val.get_abs_path())
        elif self.ptype in (self.PTYPE_LLOBJECT_LIST,self.PTYPE_LLPARAMETER_LIST):
            if val is None:
                element.text = ""
            else:
                tuple = ()
                for obj in val:
                    if obj is None:
                        tuple += (None,)
                    else:
                        tuple += (obj.get_abs_path(),)
                element.text = str(tuple)
        elif self.ptype in (self.PTYPE_UNKNOWN,self.PTYPE_UNKNOWN_LIST):
            element.text = ""
        else:
            element.text = ""

        return element

    def from_xml_element(self,element,topobj):
        #print("loading param", self.ref_obj, self.label)
        if self.ptype in (self.PTYPE_BOOL,self.PTYPE_INT,self.PTYPE_FLOAT):
            self.set_value(literal_eval(element.text))
        elif self.ptype in (self.PTYPE_STR,):
            self.set_value(element.text)
        elif self.ptype in (self.PTYPE_NUMPY,):
            shape = literal_eval(element.get('shape'))
            dtype = element.get('dtype')
            array = np.frombuffer(base64.decodestring(element.text),dtype=dtype)
            array.reshape(shape)
            self.set_value(array)
        elif self.ptype in (self.PTYPE_LLOBJECT,):
            if element.text=="":
                self.set_value(None)
            else:
                self.set_value(topobj.get_object_from_abs_path(literal_eval(element.text)))
        elif self.ptype in (self.PTYPE_LLPARAMETER,):
            if element.text=="":
                self.set_value(None)
            else:
                path = literal_eval(element.text)
                objpath = path[0]
                parampath = path[1]
                self.set_value(topobj.get_object_from_abs_path(objpath).ll_params[parampath])
        elif self.ptype in (self.PTYPE_LLOBJECT_LIST,):
            lst = self.get_value()
            del lst[:]
            if element.text=="":
                pass
            else:
                for objpath in literal_eval(element.text):
                    if objpath is None:
                        lst.append(None)
                    else:
                        lst.append(topobj.get_object_from_abs_path(objpath))
        elif self.ptype in (self.PTYPE_LLPARAMETER_LIST,):
            lst = self.get_value()
            if element.text=="":
                pass
            else:
                for path in literal_eval(element.text):
                    if path is None:
                        lst.append(None)
                    else:
                        objpath = path[0]
                        parampath = path[1]
                        lst.append(topobj.get_object_from_abs_path(objpath).ll_params[parampath])

    def binaryshare_set_location_get_length(self, location):
        self.binary_share_location = location
        length = sizeof(c_int) # foreign id storage
        length += sizeof(c_int) # length storage
        length += sizeof(c_int) # ptype storage
        length += len(self.label)+sizeof(c_int) # label storage (length first)
        if self.ptype<=1: #bool or int
            length += sizeof(c_int)
        elif self.ptype==2: #float
            length += sizeof(c_double)
        elif self.ptype==3: #string
            length += sizeof(c_int)
            length += len(self.get_value())
        elif self.ptype==4: #numpy
            nparray = self.get_value()
            length += (3+(nparray.ndim))*sizeof(c_int) + len(nparray.dtype.str)*sizeof(c_char) + nparray.nbytes
        elif self.ptype<=6: #llobject, llparam
            length += sizeof(c_int)
        elif self.ptype<=8: ##llobject list, llparam list
            length += sizeof(c_int)*(len(self.get_value())+1) #+1 to store length
        else:
            length += 0
        self.binary_share_length = length
        return length

    def binaryshare_dump(self, dump_addr):
        loc = dump_addr+self.binary_share_location+sizeof(c_int) #skip over foreign id storage

        c_int.from_address(loc).value = self.binary_share_length
        loc += sizeof(c_int)

        c_int.from_address(loc).value = self.ptype
        loc += sizeof(c_int)


        lenlabel = len(self.label)
        c_int.from_address(loc).value = lenlabel
        loc += sizeof(c_int)

        (c_char*lenlabel).from_address(loc).value = self.label
        loc += sizeof(c_char)*lenlabel

        if self.ptype<=1: #bool or int
            c_int.from_address(loc).value = int(self.get_value())
            loc += sizeof(c_int)
        elif self.ptype==2: #float
            c_double.from_address(loc).value = self.get_value()
            loc += sizeof(c_double)
        elif self.ptype==3: #string
            val = self.get_value()
            lenval = len(val)
            c_int.from_address(loc).value = lenval
            loc += sizeof(c_int)
            (c_char*lenval).from_address(loc).value =  val
            loc += sizeof(c_char)*lenval
        elif self.ptype==4: #numpy
            nparray = self.get_value()

            c_int.from_address(loc).value = nparray.ndim
            loc += sizeof(c_int)

            for i in range(nparray.ndim):
                c_int.from_address(loc).value =  nparray.ctypes.shape[i]
                loc += sizeof(c_int)

            dtypestr = nparray.dtype.str
            c_int.from_address(loc).value = len(dtypestr)
            loc += sizeof(c_int)
            (c_char*len(dtypestr)).from_address(loc).value = dtypestr
            loc += sizeof(c_char)*len(dtypestr)


            c_int.from_address(loc).value =  nparray.nbytes
            loc += sizeof(c_int)

            memmove(byref(c_int.from_address(nparray.ctypes.data)), byref(c_int.from_address(loc)), nparray.nbytes)
            loc += nparray.nbytes
        elif self.ptype<=6: #llobject, llparam
            val = self.get_value()
            if val is None:
                c_int.from_address(loc).value = -1
            else:
                c_int.from_address(loc).value = self.get_value().binary_share_location
            loc += sizeof(c_int)
        elif self.ptype<=8: ##llobject list, llparam list
            val = self.get_value()
            c_int.from_address(loc).value =  len(val)
            loc+=sizeof(c_int)
            for obj in val:
                if obj is None:
                    c_int.from_address(loc).value = -1
                else:
                    c_int.from_address(loc).value = obj.binary_share_location
                loc += sizeof(c_int)

class LLObject(object):

    def __init__(self, parent=None):
        self.xml_element = None
        self.ll_params = []
        self.ll_children = []
        self.ll_parent = None
        self.set_parent(parent)

        # hacky way of preventing an LLObject ever being removed from memory until remove() is called.  Ensures some safety when sending references across processes.
        # only works if cyclic garbage collection is disabled
        # pyinternal_refcount = c_int.from_address(id(self))
        self.self_ref = self # this increments the internal reference count

    def remove(self):
        self.set_parent(None)
        for child in self.ll_children:
            child.remove()
        del self.ll_children[:]
        self.self_ref = None

    def set_parent(self, parent):
        if self.ll_parent==parent:
            return
        elif self.ll_parent is None:
            pass
        else:
            self.ll_parent.ll_children = [child for child in self.ll_parent.ll_children if child!=self]
        self.ll_parent = parent
        if self.ll_parent is None:
            pass
        else:
            self.ll_parent.ll_children.append(self)

    def add_parameter(self, *args, **kwargs):
        param = LLObjectParameter(self, *args, **kwargs)
        self.ll_params.append(param)

    def get_parameter(self, label):
        for param in self.ll_params:
            if param.label == label:
                return param
        return None

    def __getitem__(self, item):
        if isinstance(item, str):
            return self.get_parameter(item).get_value()
        else:
            return None

    def __setitem__(self, item, val):
        if isinstance(item, str):
            return self.get_parameter(item).set_value(val)
        else:
            return None

    @staticmethod
    def from_xml_element(element,top_level=True,i=0):
        constructor = getattr(LL, element.tag)
        #print ('Creating',element.tag,'depth',i)
        obj = constructor()
        obj.xml_element = element
        for children_element in [children_element for children_element in element if children_element.tag=='children']:
            for child_element in children_element:
                child_obj = LLObject.from_xml_element(child_element,top_level=False,i=(i+1))
                child_obj.set_parent(obj)
        if top_level:
            obj.set_params_from_xml_element(obj)
        return obj

    def set_params_from_xml_element(self,topobj):
        for children in self.ll_children:
            children.set_params_from_xml_element(topobj)
        if self.xml_element is None:
            pass
        else:
            for params_element in [params_element for params_element in self.xml_element if params_element.tag == 'params']:
                for param_element in params_element:
                    self.get_parameter(param_element.tag).from_xml_element(param_element,topobj)


    def create_xml_element(self, parent_element=None, top_obj=None):
        if top_obj is None:
            top_obj = self

        if parent_element is None:
            objElement = xmlet.Element(self.__class__.__name__)
        else:
            objElement = xmlet.SubElement(parent_element, self.__class__.__name__)

        params_element = xmlet.SubElement(objElement,'params')
        children_element = xmlet.SubElement(objElement,'children')

        for child in self.ll_children:
            child.create_xml_element(children_element, top_obj)

        for param in self.ll_params:
            param.create_xml_element(params_element, top_obj)

        return objElement

    def get_abs_path(self, topobj=None):
        if self.ll_parent is None or self==topobj:
            return tuple()
        else:
            return self.ll_parent.get_abs_path(topobj) + (self.ll_parent.ll_children.index(self),)

    def get_object_from_abs_path(self, path):
        if(len(path)>0):
            return self.ll_children[path[0]].get_object_from_abs_path(path[1:])
        else:
            return self

    def binaryshare_set_location_get_length(self, location):
        self.binary_share_location = location
        length = sizeof(c_int) # foreign id storage
        length += sizeof(c_int) # length storage
        length += sizeof(c_int)+len(self.__class__.__name__) # store class type
        length += sizeof(c_int) # id storage
        length += sizeof(c_int) # child num storage
        length += sizeof(c_int) # param storage
        for child in self.ll_children:
            length += child.binaryshare_set_location_get_length(location+length)
        for param in self.ll_params:
            length += param.binaryshare_set_location_get_length(location+length)
        self.binary_share_length = length
        return length

    def binaryshare_dump(self, dump_addr):
        loc = dump_addr+self.binary_share_location+sizeof(c_int) #skip over foreign id storage

        # store length
        c_int.from_address(loc).value = self.binary_share_length
        loc += sizeof(c_int)

        # store classname
        string = self.__class__.__name__
        strlen = len(string)
        c_int.from_address(loc).value = strlen
        loc += sizeof(c_int)
        (c_char*strlen).from_address(loc).value = string
        loc += strlen

        # store id
        c_int.from_address(loc).value = id(self)
        loc += sizeof(c_int)

        # store children length
        c_int.from_address(loc).value = len(self.ll_children)
        loc += sizeof(c_int)

        #store param length
        c_int.from_address(loc).value = len(self.ll_params)
        loc += sizeof(c_int)

        # store children
        for child in self.ll_children:
            child.binaryshare_dump(dump_addr)

        # store parameters
        for param in self.ll_params:
            param.binaryshare_dump(dump_addr)

        return