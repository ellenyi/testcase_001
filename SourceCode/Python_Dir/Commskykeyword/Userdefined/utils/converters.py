# -*- coding: utf-8 -*-
"""Converter package.

@author: Zhang Yongchao
@contact: sam.c.zhang@nsn.com
"""
import types

def to_bool(value, skip_none=False):
    """Method to made conversion to boolean.
     
    @param value: Some value to convert.
    @param boolean skip_none: Skip conversion if value is None.

    @return: Converted value.
    @rtype: boolean
    
    """
    if value is None and skip_none is True:
        return value
    if isinstance(value, basestring):
        if value.lower().strip() == "false":
            value = False
        elif value.lower().strip() == "true":
            value = True
        else:
            raise ValueError('Value is from out of range. Available values \
are (not case sensitive): ${True}, ${False}, true, false')
        return value
    elif isinstance(value, bool):
        return value
    else:
        raise TypeError('Object (%s) with value (%s) cannot be converted \
to bool' % (str(value), type(value).__name__))


def to_float(value, skip_none=False):
    """Method to made conversion to float.

    @param value: Some value to convert.
    @param boolean skip_none: Skip conversion if value is None.

    @return: Converted value.
    @rtype: integer
    """
    if value is None and skip_none is True:
        return value
    if isinstance(value, basestring) or isinstance(value, int):
        try:
            return float(value)
        except ValueError:
            raise ValueError('Value (%s) is not a floating point number \
representation' % str(value))
    elif isinstance(value, float):
        return value
    else:
        raise TypeError('Object (%s) with value (%s) cannot be converted to \
float' % (str(value), type(value).__name__))

    

def to_int(value, skip_none=False):
    """Method to made conversion to integer.

    @param value: Some value to convert.
    @param boolean skip_none: Skip conversion if value is None.

    @return: Converted value.
    @rtype: integer
    """
    if value is None and skip_none is True:
        return value
    try:
        return int(value)
    except ValueError:
        raise ValueError('Value (%s) is not a number e.g. 1, ${1}' % str(value))

def to_list(value, expected_type=None, skip_none=False):
    """Method to made conversion to integer.

    @param value: Some value to convert.
    @param expected_type: types every value need to convert.
    @param boolean skip_none: Skip conversion if value is None.

    @return: Converted value.
    @rtype: list.
    """    
    if value is None and skip_none is True:
        return value
    if not callable(expected_type) and expected_type is not None:
        expected_type = eval(expected_type)
    result_list = []
    if isinstance(value, (basestring, int, float)):
        if expected_type is None:
            result_list.append(value)
        else:
            result_list.append(expected_type(value))
        return result_list
    
    for index, item in enumerate(value):
        if expected_type is None:
            result_list.append(item)
        else:
            try:
                result_list.append(expected_type(item))
            except ValueError:
                raise ValueError('Value (%s) with index (%d) cannot be \
converted to (%s)' % (str(item), index, expected_type.__name__))
    return result_list

