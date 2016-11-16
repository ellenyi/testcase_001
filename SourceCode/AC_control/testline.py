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
AC_username = "icac"
AC_password = "icaclogin"
AC_url = "https://172.20.75.51/"
#************************ AC Configuration  ***********************
AP_CSV_File = "F:\\AC control\\ap_group_out.csv"
Update_path = "F:\\AP version\\AP4604V400R003D008.app"
Dstversion = "AP4604V400R003D008"

#************************ WLAN seurity  ***********************


WLAN_seurity = "https://172.20.75.51/wlan/wlan_security_cfg_list.php"

#************************ WLAN config by web  ***********************

WLAN_Groups = "https://172.20.75.51/wlan/wlan_group.php"
Time_Policy_Groups = "https://172.20.75.51/timepolicy/time_policy_group.php"
AP_Policy_Apply = "https://172.20.75.51/policy/policy.php"
WLAN_VLAN_Association = "https://172.20.75.51/wlanport/wlan_port.php"

AP_Configuration = "https://172.20.75.51/apgroup/apgroup_list.php" 
#************************ Basic Settings  by web  ***********************

AP_Version  = "https://172.20.75.51/VersionManager/APVerInfo_list.php"
AC_configlink = "https://172.20.75.51/baseconf/ac_config.php"
verion_download_server = "https://172.20.75.51/VersionManager/FtpServer_list.php"


#************************ Statistics  by web  ***********************
AP_Information = "https://172.20.75.51/ap/ap_list.php"
AP_Upgrade = "https://172.20.75.51/ap/ap_soft_upgrade.php"

#************************ setting ***********************
prompt_time = "30"
telnet_port = '23'
UPGRAD_VERSION ='V200R001D014 '
TFTP_SERVER = '172.20.99.42 '
IMAGE_FILE = 'AP2000-FATV200D014.app '
AP_Group = "TestAtHome_Gxx"
Add_WLANGROUP = "TestAtHomeProfile"
Device_Type = "AP4102"


#************************ Basic settings by AP Web ***********************
Network_setting = "network-setting"
IGMP_snooping = "IGMP snooping"
RF_setting = "RF-setting"
Radio_0 = "radio 0" 

 
#************************ Log Generating ***********************
SUITE_NAME ="CommSky G2 FatAP"
   

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



