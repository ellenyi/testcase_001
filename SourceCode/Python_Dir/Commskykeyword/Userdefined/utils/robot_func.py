from robot.libraries.BuiltIn import BuiltIn

def robot_is_running():
    """check if robot is running or not."""
    try:        
        BuiltIn().get_library_instance("BuiltIn")
        return True
    except Exception, _:
        return False

def get_robot_runtime_variable(varname):
    """get robot runtime variable use Builtin libraries replace_variables"""
    try:
        if not varname.startswith("${"):
            varname = "${%s}" % varname
        return BuiltIn().replace_variables(varname)
    except Exception, error:
        from RobotWS.CommonLib.logging import global_logger as log
        log.info("Can't get variable '%s' ! details: '%s'" % (varname, error))