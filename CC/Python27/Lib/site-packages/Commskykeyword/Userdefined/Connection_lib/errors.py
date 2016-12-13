import traceback


class LteBaseException(Exception):
    """TA library base exception"""
    def __init__(self, message):
        self._message = message
        Exception.__init__(self, self._message)
        traceback.print_exc()
    message = property(fget=lambda s:s._message)
            
    def __str__(self):
        return str(self.message)
    
class KeywordSyntaxError(LteBaseException):
    """Used for keyword input parameters is invalid.
    """
    def __init__(self, message = "Parameters you given is invalid ! Please check."):
        super(KeywordSyntaxError, self).__init__(message)
        
class CommandExecuteError(LteBaseException):
    """Used for commands execute error .
    """
    def __init__(self, message = "Command is executed failed !"):
        super(CommandExecuteError, self).__init__(message)    


class DataTypeConvertError(LteBaseException):
    """Exception raised when it is not possible to convert provided value."""
    def __init__(self, message = "Convert error"):
        super(DataTypeConvertError, self).__init__(message) 
