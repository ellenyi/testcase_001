from inspect import ismethod, isfunction
from RobotWS.CommonLib.errors import LteBaseException


class ParallelError(LteBaseException):
    """thread error"""
    def __init__(self, threadname, threaderror):
        self._threadname = threadname
        self._threaderror = threaderror
        self._message = "%s: %s" % (self._threadname, self._threaderror)
        super(ParallelError, self).__init__(self._message)

class FuncCall(object):
    """ Class FunCall defines a function call object that is used to handle
        a certain function calls on a thread.

        FuncCall contains the attributes thread name, function object and
        function arguments.

        FuncCall class initialization parameters:

        @param str threadname: thread name
        @param function func: function object
        @param tuple args: argument values tuple (default is ())
        @param dict kwargs: named arguments dictionary (default is {})
    """
    def __init__(self, threadname, func, args=(), kwargs={}):
        self.__threadname = threadname
        self.__func = func
        self.__args = args
        self.__kwargs = kwargs

    threadname = property(lambda s: s.__threadname)
    func = property(lambda s: s.__func)
    args = property(lambda s: s.__args)
    kwargs = property(lambda s: s.__kwargs)

    def __str__(self):
        funcstr = ""
        if isfunction(self.__func):
            funcstr = "%s" % self.__func.func_name
        elif ismethod(self.__func):
            funcname = self.__func.im_func.func_name
            funcclass = self.__func.im_self.__class__.__name__
            funcstr = "%s.%s" % (funcclass, funcname)
        return "threadName=%s, func=%s, args=%s, kwargs=%s" % (
            self.__threadname,
            funcstr,
            self.__args,
            self.__kwargs)

class FuncResult(object):
    """ Class FuncResult is a base class that defines the result of a function
        call object.

        FuncResult class initialization parameters:

        @param str threadname: thread name
    """
    def __init__(self, threadname):
        self.__threadname = threadname
    threadname = property(lambda s: s.__threadname)


class FuncResultReturnValue(FuncResult):
    """ Class FuncResultReturnValue inherits from FuncResult and defines the
        returned value result of a function call object.

        FuncCall contains the attribute return value.

        FuncResultReturnValue class initialization parameters:

        @param str threadName: thread name
        @param str returnValue: return value
    """
    def __init__(self, threadname, returnvalue):
        FuncResult.__init__(self, threadname)
        self.__returnvalue = returnvalue
    returnvalue = property(lambda s: s.__returnvalue)


class FuncResultException(FuncResult):
    """ Class FuncResultException inherits from FuncResult and defines the a
        exception result of a function call object.

        FuncCall contains the attributes exception and traceback.

        FuncResultReturnValue class initialization parameters:

        @param str threadName: thread name
        @param exception exception: exception object
        @param str traceback: exception traceback string
    """
    def __init__(self, threadname, exception, traceback):
        FuncResult.__init__(self, threadname)
        self.__exception = exception
        self.__traceback = traceback
    exception = property(lambda s: s.__exception)
    traceback = property(lambda s: s.__traceback)

