"""Builtin datatype enhancement and self-defined datatype"""

from types import MethodType
from types import FunctionType

class CommonItem:
    """ base class for items contained in CommonDict """
    def __str__(self):
        """ support a nice string representation with all attribute values"""
        tmp = ",".join(sorted([ "%s=%s" % (item, getattr(self, item)) 
                               for item in dir(self) 
                               if not item.startswith("_") and 
                               getattr(self, item) != None and
                               type(getattr(self, item)) not in 
                               [MethodType, FunctionType]]))
        for i in range(len(tmp)):
            if ord(tmp[i]) > 127:
                tmp = tmp.replace(tmp[i], " ")
        return str(self.__class__.__name__) + '(' + tmp + ')'

    def __repr__(self):
        return self.__str__()

    def __unicode__(self):
        return self.__str__()

class ObjectDict(dict):
    """A dictionary that allows attribute-based access (dictionary.key instead 
    of dictionary['key']).
    """
    def __getattr__(self, attr):
        value = self[attr]
        return ObjectDict(value) if isinstance(value, dict) else value

    def __setattr__(self, name, value):
        self[name] = value

    def __delattr__(self, name):
        del self[name]

class RobotObjectDict(dict):
    """A dictionary that allows attribute-based access (dictionary.key instead 
    of dictionary['key']), it will ignore case incentive type when you use it.
    """
    def __getattr__(self, attr):
        value = self[str(attr).upper()]
        return RobotObjectDict(value) if isinstance(value, dict) else value
    
    def __setattr__(self, name, value):
        self[str(name).upper()] = value

    def __delattr__(self, name):
        del self[name]

class KeywordClass(object):
    """Class inherit from KeywordClass will be parsed as keyword.
    """


class SortedDict(dict):
    """ A specialization of generic python dict with the following extensions/differences:
    - if a key/index does not exits Common dict will not raise KeyError but return None
    - may be used like a list an element is addressed via an integer as index
      (does not work if you use integers as keys)
    - support a list of keys in the order they have been inserted: ordered_keys
    - supporting sorting of this ordered_keys attribute and thus the "list" CommonDict itself
    - nice string representation also if objects are contained
    - contained object should be derived from CommonItem (not mandatory)
    """
    def __init__(self,*args):
        """ should also be called by subclasses,
        otherwise you might have problems with empty CommonDicts when the attribute ordered_keys is not present
        """
        dict.__init__(self,*args)
        self.ordered_keys = []

    def __str__(self):
        """ support a nice string representation """
        try:
            tmp = "\n".join([ str(key) + ':' + str(self[key]) for key in self.ordered_keys ])
            for i in range(len(tmp)):
                if ord(tmp[i]) > 127:
                    tmp = tmp.replace(tmp[i], " ")
            return tmp
        except AttributeError:
            return ""

    def __repr__(self):
        return self.__str__()

    def __unicode__(self):
        return self.__str__()

    def __getitem__(self, key):
        """ access the item identified by key, either behave like a dictionary or like a list
        return None is no item is found
        """
        if len(self)==0:
            return None
        try:
            return dict.__getitem__(self,key)
        except KeyError:
            pass
        if type(key) == type(1):
            try:
                return dict.__getitem__(self, self.ordered_keys[key])
            except IndexError:
                pass
        return None

    def __setitem__(self, key, item):
        """ store the new item in the dictionary and append the key to ordered_list """
        #if type(key) == type(1):
        #    raise RuntimeError("CommonDict does not support integer as key")
        dict.__setitem__(self, key, item)
        try:
            if key in self.ordered_keys:
                self.ordered_keys.remove(key)
            self.ordered_keys.append(key)
        except AttributeError:
            self.ordered_keys = [key, ]

    def __delitem__(self, key):
        """ remove the new item from the dictionary and remove the key from ordered_list,
        works both with key and index """
        try:
            dict.__delitem__(self, key)
            self.ordered_keys.remove(key)
        except KeyError:
            if type(key) == type(1):
                dict.__delitem__(self, self.ordered_keys[key])
                del(self.ordered_keys[key])


    def __getattr__(self, name):
        """ support direct access to the item's attributes if only a single item is contained """
        if len(self) != 1:
            raise AttributeError
        return getattr(self.values()[0], name)

    def length(self):
        """ only because x.length() looks nicer than x.__len__()"""
        return len(self)

    def _get_empty_container(self):
        """ needed so that select_entries_from_list can return the correct type of container,
        can be overwritten by subclasses """
        return CommonDict()

    def sort(self,*args):
        """ sorts attribute orderd_keys and thus also CommonDict itself if used as a list
        can be overwritten by subclasses if a special sorting algortihm is needed. """
        try:
            self.ordered_keys.sort(*args)
        except AttributeError:
            pass
