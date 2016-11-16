import os   
import inspect 

def get_Commskykeyword_path():    
    this_file = inspect.getfile(inspect.currentframe())  
    path = os.path.dirname(os.path.dirname(this_file))
    return path

def get_Commskykeyword_path_with_command():
    seper = "*SEP*"
    cmd = '''python -c "import Commskykeyword, os;print '%s',os.path.dirname(Commskykeyword.__file__)"''' % seper
    ret = Connection_lib.execute_shell_command_without_check(cmd)
    if seper not in ret:
        raise Exception, "Can't get Commskykeyword path with python command"
    else:
        for ln in ret.splitlines()[::-1]:
            if seper in ln:
                return ln.split(seper, 3)[-1].strip()
            
def get_tools_path_with_command():     
    path = get_Commskykeyword_path_with_command()
    tools_path = os.path.join(path, "resources", "tools")
    return tools_path
            
def get_tools_path():     
    path = get_Commskykeyword_path()
    tools_path = os.path.join(path, "resources", "tools")
    return tools_path

if __name__ == "__main__":
    Connection_lib.connect_to_host("172.20.20.39", 23, "Administrator", "sunwentao")
    print "<<"
    path = get_tools_path_with_command()
    print ">>", "%s" %path
    print "<<"
    connections.disconnect_all_hosts()
