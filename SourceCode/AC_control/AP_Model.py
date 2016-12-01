"""AC,AP variable file, this file is used in TA run."""
#************************ AC,AP ***********************
#SW_RELEASE = "RL65"
# --> AC Information by telent logon<--
AC_INFO = {"IP" : "172.20.75.51",
            "NAME" : "AC1000",
            "USERNAME" : "root",
            "PASSWORD" : "fitap^_^",
            "AC_VERSION" : ""}
					
# --> AP Information by telnet logon<--
AP_INFO = { "IP" : "172.20.99.64",
            "NAME" : "AP3902",
            "USERNAME" : "admin",
            "PASSWORD" : "admin",
            "AC_VERSION" : ""}
# --> Client control PC <--
Client_PC_INFO = {"IP" : "172.20.30.149",  
               "GATEWAY" : "172.20.30.1",
               "USERNAME" : "Administrator", 
               "PASSWORD" : "sunwentao"}


#************************ AC logon by web  ***********************
ConsoleServer_IP = "172.20.99.100"
ConsoleServer_Port = "10017"
WEB_IP = "172.20.99.64"





 
   

def get_variables(target=""):
    """get variables that will be used in robot, in TA also will validate these
    variable to make every team have a uniform environment.
    @param target: is target or not, can be TGT1,TGT2,TGT3 or leave it empty
    @raise ValidationError: if not match template"""
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

    vars = dict(((k, globals()[k]) for k in globals() if not k.startswith("_")))
    return RobotObjectDict(vars)



