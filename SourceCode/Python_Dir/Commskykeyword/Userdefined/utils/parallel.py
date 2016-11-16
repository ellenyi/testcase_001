from inspect import ismethod, isfunction
import Queue
from sys import exc_info
from threading import Thread
from funccall import *
from RobotWS.CommonLib.logging import global_logger as log


def run_sequential(funccalls):
    """ Run list of function calls in sequence.

    @param FuncCall funccalls: function calls list
    """
    results = []
    for funccall in funccalls:
        try:
            res = funccall.func(*funccall.args, **funccall.kwargs)
            result = FuncResultReturnValue(
                threadame=funccall.threadame,
                returnvalue=res)
        except Exception, e:
            result = FuncResultException(
                threadame=funccall.threadame,
                exception=e, traceback=exc_info()[2])
        results.append(result)
    return results

def run_parallel(funccalls, stoponfirstexception=True):
    """ Run list of function calls in parallel.

    @param FuncCall funccalls: function calls list
    @param bool stoponfirstexception: flag to stop execution on the first
                                      exception (default is True)
    """
    queue = Queue.Queue()
    threads = []

    threadmap = {}
    for funccall in funccalls:
        if funccall.threadname not in threadmap:
            threadmap[funccall.threadname] = [funccall]
        else:
            threadmap[funccall.threadname].append(funccall)

    newfunccalls = []
    for threadname in threadmap:
        if len(threadmap[threadname]) == 1:
            newfunccalls.append(threadmap[threadname][0])
        else:
            newfunccalls.append(
                FuncCall(
                    threadname=threadname,
                    func=run_sequential,
                    args=(threadmap[threadname],)))

    for (i, funccall) in enumerate(newfunccalls):
        def makewrapper(funccall, j):
            def threadwrapper(*args, **kwargs):
                try:
                    res = funccall.func(*args, **kwargs)
                    queue.put((j, FuncResultReturnValue(
                        threadname=funccall.threadname,
                        returnvalue=res)))
                    return res
                except Exception, e:
                    queue.put((j, FuncResultException(
                        threadname=funccall.threadname,
                        exception=e, traceback=exc_info()[2])))
            return threadwrapper
        thread = Thread(
            target=makewrapper(funccall, i),
            name=funccall.threadname,
            args=funccall.args,
            kwargs=funccall.kwargs)
        threads.append(thread)
        thread.daemon = True
        thread.start()

    n = len(newfunccalls)
    results = [None] * n
    outstandingresults = set()
    for i in xrange(n):
        outstandingresults.add(i)
    for i in xrange(n):
        while True:
            try:
                (j, funcresult) = queue.get(block=True, timeout=10)
                queue.task_done()
                outstandingresults.remove(j)
                if isinstance(funcresult, FuncResultException) and stoponfirstexception:
                    raise ParallelError(funcresult.threadname, funcresult.exception), None, funcresult.traceback
                else:
                    results[j] = funcresult
                break
            except Queue.Empty:
                log.debug("waiting for function calls: %s" % ", ".join(["(%s)" % newfunccalls[i] for i in outstandingresults]))
    return results




if __name__ == "__main__":
    
    import time
    def _test_2(*a, **b):
        print "test 2", a, b
        raise RuntimeError("Error2")
        
    def _test_1(a, b=1):
        time.sleep(30)
        print "test 1", a, b
        return a, b    
    test_1 = FuncCall(threadname="test_1", func=_test_1, args=(0,))
    test_3 = FuncCall(threadname="test_1", func=_test_1, args=(0, 2))
    test_2 = FuncCall(threadname="test_2", func=_test_2, args=(1,2,3, 4), kwargs={'c':1,'d':2})
    
    result = run_parallel([test_1, test_2], False)
    print "all result: ", result
    
    print result[0].exception
    print result[1].returnvalue
    raise result[0].exception
    

    