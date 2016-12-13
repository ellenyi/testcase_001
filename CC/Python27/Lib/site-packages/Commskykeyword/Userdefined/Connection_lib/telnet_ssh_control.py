from .connection_mgr import ConnectionMgr

global_connection_mgr = ConnectionMgr()


def switch_host_connection(conn):
    """Switch to the connection identified by 'conn'.
       The value of the parameter 'conn' was obtained from keyword 'Connect to Host'
    """
    return global_connection_mgr.switch_host_connection(conn)

def execute_shell_command(command, **kwargs):
    """Execute a command on the remote system.

    | Input Parameters  | Man. | Description |
    | command           | Yes  | command to be executed on the remote system |
    | username          | No   | username for execute command on the remote system (Linux only) |
    |                   |      | default is "root". |
    | password          | No   | password for user on the remote system (Linux only) |
    |                   |        | default is "", execute command as current user. |
    | timeout_add       | No   | default is True, if not, it will not check exist data |
    |                   |      | in the socket, when timeout is reach or one of prompt is reach. |
    | newline            | No  | the newline symbol for command |
    | loglevel          | No  | the loglevel of current command execution | 
    | expected_errorcode | No  | the errorcode expected |

    | Return value | command output (String) |

    Example
    | Execute shell command | ${command} |                      | # execute command as current user. |
    | Execute shell command | ${command} | timeout_add=${false} | # execute until command timeout, neither the socket have data or not |
    | Execute shell command | ${command} | password=${password} | # execute command as root. |
    | Execute shell command | ${command} | expected_errorcode=0 | #execute command and check the errorcode | 
    """
    return global_connection_mgr.current_mgr.execute_shell_command(command, **kwargs)

def execute_shell_command_bare(command, **kwargs):
    """Execute a command on the remote system without write newline.

    | Input Parameters  | Man. | Description |
    | command           | Yes  | command to be executed on the remote system |
    | loglevel          | No  | the loglevel of current command execution |
    | Return value      | command output (String) |

    Example
    | Execute shell command bare | ${command} |      
    """
    return global_connection_mgr.current_mgr.execute_shell_command_bare(command, **kwargs)


def disconnect_all_hosts(**kwargs):
    """Closes all existing telnet connections to remote hosts.
    | Input Parameters  | Man. | Description |
    | **args            | No   | conn_type |

    Example
    Disconnect all connections, both with telnet and ssh.
    | disconnect_all_hosts |   
    Disconnect all telnet connections
    | disconnect_all_hosts | conn_type=TELNET |
    Disconnect all ssh connections
    | disconnect_all_hosts | conn_type=SSH |
    
    """
    return global_connection_mgr.disconnect_all_hosts(**kwargs)

def disconnect_from_host(conn=None):
    """Closes the telnet connections to the currently active remote host.
    | Input Parameters  | Man. | Description |
    | **args            | No   |conn obj |

    Example
    Disconnect current active connection.
    | disconnect_from_host |  
    Disconnect given connection obj: connobj.
    | disconnect_from_host | connobj | 
    """
    return global_connection_mgr.disconnect_from_host(conn)

def get_current_connection(conn_type=None):
    """This keyword get the current connection

    | Input Parameters        | Man. | Description |
    | get_current_connection  | Yes  | length for receive |

    Example
    | get_current_connection |
    | get_current_connection | conn_type= SSH | 
    """
    return global_connection_mgr.get_current_connection(conn_type)
    
def get_shell_content():
    """This keyword get the current content of .

    Example
    | get_shell_content |
    """
    return global_connection_mgr.current_mgr.read()


def set_shell_prompt(*new_prompt):
    """This keyword sets the connection prompt to new prompt other than default one.

    | Input Parameters  | Man. | Description |
    | new_prompt        | Yes  | New prompt for connection |

    | Return value | original connection prompt |

    Example
    | ${old_prompt} = | set_shell_prompt | # |  $ |
    | ${old_prompt} = | set_shell_prompt | [.*$, \w:.*>] |
    """
    return global_connection_mgr.current_mgr.set_shell_prompt(*new_prompt)

def set_shell_timeout(new_timeout):
    """This keyword sets the new connection timeout.

    | Input Parameters  | Man. | Description |
    | new_timeout       | Yes  | New timeout for connection |

    | Return value | original connection timeout |

    Example
    | ${old_timeout} = | set_shell_timeout | 100 |
    """
    return global_connection_mgr.current_mgr.set_shell_timeout(new_timeout)


def set_shell_pausetime(pausetime):
    """This keyword sets the new connection pausetime.

    | Input Parameters  | Man. | Description |
    | pausetime       | Yes  | New timeout for connection |

    | Return value | original connection pausetime |

    Example
    | ${old_timeout} = | set_shell_pausetime | 100 |
    """
    return global_connection_mgr.current_mgr.set_shell_pausetime(pausetime)

def set_shell_loglevel(loglevel):
    """This keyword sets the new connection loglevel.

    | Input Parameters  | Man. | Description |
    | loglevel       | Yes  | New timeout for connection |

    | Return value | original connection loglevel |

    Example
    | ${old_loglevel} = | set_shell_loglevel | DEBUG |
    """
    return global_connection_mgr.current_mgr.set_shell_loglevel(loglevel)

def connect_to_host(host, port=23, username="", password="", **kwargs):
    """Used to connect to host, either TELNET or SSH
    | Input Parameters  | Man. | Description |
    | host              | Yes  | the address of the host you want connect |
    | port              | No   | the port you want connect |
    | username          | No   | the username    |
    | password          | No   | the password    |
    | username_prompt    | No   | the username prompt |
    | password_prompt    | No   | the password prompt |
    | conn_type         | No   | the connection type, TELNET or SSH, default is TELNET |
    | prompt            | No   | the command prompt of target host |
    | newline           | No   | the newline of target host , can be CRLF or LF for windows or linux |
    | timeout           | No   | the timeout of target host |
    | pausetime         | No   | the pause time before read something from connection |
    | device_type       | No   | the device_type of your target host |
    
    | Return value | connection object |

    Example
    | ${connection} = | connect_to_host | 127.0.0.1 | port=23 | username=tdlte-tester | password=btstest |
    | ${connection} = | connect_to_host | 192.168.1.100 | port=5003 | prompt=> |
    """
    return global_connection_mgr.connect_to_host(host, port=port, username=username, 
                                                 password=password, **kwargs)

if __name__ == '__main__':
    pass
