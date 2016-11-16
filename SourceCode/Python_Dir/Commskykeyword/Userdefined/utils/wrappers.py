from .func_property import get_func_detail_info, set_func_detail_info

def deprecated_keyword(kw):
    """This decorator is used to add DEPRECATED info before keyword's document.
    Usage:
    @deprecated_keyword
    def test():
        '''This is test for deprecated.'''
        print "test ok !"
    or can do like this:
    test = DEPRECATED(test)
    """
    kw_info = get_func_detail_info(kw)
    def _wrapper(*args, **kwargs):
        return kw(*args, **kwargs)
    kw_info["doc"] = "*DEPRECATED* " + kw_info["doc"]
    set_func_detail_info(_wrapper, kw_info)
    return _wrapper




