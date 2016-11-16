"""functions basic property
"""


def get_func_co_name(kw):
    if kw.func_code.co_name != '<lambda>':
        return kw.func_code.co_name
    else:
        #return kw._co_name
        return kw.func_code.co_name

def get_func_co_filename(kw):
    if kw.func_code.co_filename != '<string>':
        return kw.func_code.co_filename
    else:
        return kw._co_filename

def get_func_detail_info(func):
    return dict(name=func.__name__, doc=func.__doc__, module=func.__module__,
                dict=func.__dict__, func_code=func.func_code,
                globals=func.func_globals, closure=func.func_closure)

def set_func_detail_info(func, infodict):
    func.__name__ = infodict['name']
    func.__doc__ = infodict['doc']
    func.__module__ = infodict['module']
    func.__dict__.update(infodict['dict'])
    func._co_filename = infodict['func_code'].co_filename
    func._co_name = infodict['func_code'].co_name
    #func.func_globals = infodict['globals']
    #func.func_closure = infodict['closure']
