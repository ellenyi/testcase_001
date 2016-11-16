import os
import inspect

#from RobotWS.CommonLib.errors import LteBaseException

#__all__ = ["get_lib_root_path", "get_tools_path"]

def get_lib_root_path(with_cmd=False):
    if with_cmd:
        return _get_lib_path_with_cmd()
    else:
        return _get_lib_path()
            
def get_tools_path(with_cmd=False):     
    path = get_lib_root_path(with_cmd)
    tools_path = os.path.join(path, "tools")
    return tools_path

def get_lib_version_with_cmd(): 
    from RobotWS.CommonLib.connections import execute_shell_command   
    seper = "*SEP*"
    cmd = '''python -c "import RobotWS, os;print '%s',RobotWS.__version__"''' % seper
    ret = execute_shell_command(cmd)
    if seper not in ret:
        raise LteBaseException("Can't get RobotWS path with python command")
    else:
        for ln in ret.splitlines()[::-1]:
            if seper in ln:
                return ln.split(seper, 3)[-1].strip()            

def _get_lib_path_with_cmd():  
    from RobotWS.CommonLib.connections import execute_shell_command  
    seper = "*SEP*"
    cmd = '''python -c "import RobotWS, os;print '%s',os.path.dirname(RobotWS.__file__)"''' % seper
    ret = execute_shell_command(cmd)
    if seper not in ret:
        #raise LteBaseException("Can't get RobotWS path with python command")
        return ""
    else:
        for ln in ret.splitlines()[::-1]:
            if seper in ln:
                return ln.split(seper, 3)[-1].strip()
            
def _get_lib_path():    
    this_file = inspect.getfile(inspect.currentframe())  
    path = os.path.dirname(os.path.dirname(os.path.dirname(this_file)))
    #import platform
    #if platform.system() == "Linux":
    #    os.system("chmod -R 777 %s" % path)
    return path
