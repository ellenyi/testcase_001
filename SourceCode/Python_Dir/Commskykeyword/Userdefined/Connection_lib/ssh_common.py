"""Basic python ssh connection base on python paramiko module, define basic operation for ssh
Usage is same as telnet_connection
"""

import re
import time
import types
import socket

from robot_api import timestr_to_secs
from robot_api import secs_to_timestr
from robot_api import seq2str
from robot_api import get_time


import logging
logger = logging.getLogger("ssh_common")

class SshCommon:

    def __init__(self, host, port, prompt, timeout="10sec", newline='CRLF'):
        try:
            import paramiko
        except:
            raise RuntimeError("Can't import paramiko library, can't use ssh function.")
        
        self.host = host    
        self.port = port == '' and 22 or int(port)
        
        self._timeout = float(timestr_to_secs(timeout))
        self._newline = None    
        self.set_newline(newline.upper().replace('LF','\n').replace('CR','\r'))
        self._prompt = None
        self.set_prompt(prompt)
        self._loglevel = "INFO"
        self._log_buffering = False
        self._log_buffer = ""
        self._logger = logger
        
        self.username = None
        self.password = None

        #self.connected = False
        self._pausetime = 0.05
        self.conn_type = "SSH"
        self.device_type = None

        self._channel = None
        self.client = paramiko.SSHClient()
        self.client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

    @property
    def connected(self):
        try:
            #print dir(self.channel)
            if not self.channel.active or self.channel.closed:
                return False
            else:
                return True
            #return False if self.channel.closed else True
        except socket.error:
            return False
        except Exception, _:
            return False
        else:
            return True
            
    @property
    def channel(self):
        if not self._channel:
            self._channel = self.client.invoke_shell()
            #combine stderr to stdout
            self._channel.set_combine_stderr(True)
        #self.connected = True
        return self._channel
            
    def __str__(self):
        return str(self.host) + ":" + str(self.port) + " DeviceType:" + str(self.device_type) + " Timeout:"\
            + secs_to_timestr(self._timeout) + " " + repr(self)

    def __del__(self):
        """Override ssh.__del__ because it sometimes causes problems"""
        pass
    
    def set_pausetime(self, pause):
        """Sets the timeout used in read socket response, e.g. "120 sec".

        The read operations will for this time before starting to read from
        the output. To run operations that take a long time to generate their
        complete output, this timeout must be set accordingly.
        """
        old = secs_to_timestr(self._pausetime)
        self._pausetime = float(timestr_to_secs(pause))
        return old
    
    def set_timeout(self, timeout):
        """Sets the timeout used in read operations to given value represented as timestr, e.g. "120 sec".

        The read operations will for this time before starting to read from
        the output. To run operations that take a long time to generate their
        complete output, this timeout must be set accordingly.
        """
        old = secs_to_timestr(self._timeout)
        self._timeout = float(timestr_to_secs(timeout))
        #self.channel.settimeout(self._timeout)
        return old

    def set_loglevel(self, loglevel):
        old = self._loglevel
        self._loglevel = loglevel
        return old

    def set_newline(self, newline):
        old = self._newline
        self._newline = newline
        return old
    
    def close_connection(self, loglevel=None):
        """Closes current Ssh connection.

        Logs and returns possible output.
        """
        loglevel = loglevel == None and self._loglevel or loglevel
        self.client.close()
        self.client = None
        self._channel = None       
        self._log("Disconnect from %s" % str(self), self._loglevel)
        #self.connected = False
        return 

    def login(self, username, password, login_prompt='login: ',
              password_prompt='Password: '):
        """Logs in to SSH server with given user information.

        The login keyword reads from the connection until login_prompt is
        encountered and then types the username. Then it reads until
        password_prompt is encountered and types the password. The rest of the
        output (if any) is also read and all text that has been read is
        returned as a single string.

        Prompt used in this connection can also be given as optional arguments.
        """
        self.username = username
        self.password = password

        self.client.connect(self.host, self.port, username, password, timeout=self._timeout)
        # made ssh to use lastline to search.
        time.sleep(self._pausetime)
        start_time = time.time()
        login_ret = ''    
        while time.time() - start_time < int(self._timeout):
            if self.channel.recv_ready():
                c = self.channel.recv(128)
                if c == "":
                    self._log('please send this log to sam.c.zhang@nsn.com, thanks!', "WARN")
                    break
                login_ret += c
                continue
            else:
                time.sleep(0.00005) #wait for CPU.
                #break
        time.sleep(self._pausetime)
        if self.channel.recv_ready():
            login_ret += self.channel.recv(1024)
        matched = False
        matching_pattern = [pattern for pattern in self._prompt 
                             if pattern.search(login_ret[-80:])]
        if len(matching_pattern) > 0:
            pattern = matching_pattern[0].pattern
            login_ret = SshCommon._colorpattern.sub("", login_ret)
            matched = True
        self._log(login_ret, self._loglevel)
        if not matched:
            raise AssertionError('No match found for prompt "%s" in %ssec, detail info: "%s"' \
                                 % (seq2str([x.pattern for x in self._prompt ], lastsep=' or '), \
                                    timestr_to_secs(self._timeout), login_ret))
        self._log("Select pattern '%s' as default pattern" % pattern)
        self.set_prompt(pattern)       
        return login_ret
        
        """            
        ret = self.expect(self._prompt, self._timeout)
        if ret[0] == -1 :
            self._log(ret[2], self._loglevel)
            raise AssertionError('No match found for prompt "%s" in %ssec, detail info: "%s"' \
                                 % (seq2str([x.pattern for x in self._prompt ], lastsep=' or '), \
                                    timestr_to_secs(self._timeout), ret[2]))
        else:
            if len(self.get_prompt()) > 1:
                selected_prompt = self._prompt[ret[0]].pattern
                self.set_prompt(selected_prompt)
                self._log("maybe this guy use default prompts, select the most \
similarly to set as default: '%s'" % selected_prompt, "TRACE")
        missbuf = self.read("Trace")
        self._log(ret[2] + missbuf, self._loglevel)
        #self.connected = True
        return ret[2] + missbuf
        """

    def write(self, text):
        """Writes given text over the connection and appends newline"""
        #self.write_bare(text + r"%s" % ('' if self._newline is None else self._newline))
        self.write_bare(text)
        self.write_bare(r"%s" % ("" if self._newline is None else self._newline))

    def write_bare(self, text):
        """Writes given text over the connection without appending newline"""
        try:
            text = str(text)
        except UnicodeError:
            msg = 'Only ascii characters are allowed in ssh. Got: %s' % text
            raise ValueError(msg)
        
        if text not in (self._newline, ""):
            sDict = {chr(3):"Ctrl-C", chr(13) : "Ctrl-M", chr(24): "Ctrl-X", chr(25): "Ctrl-Y"}
            self._log("Execute command: " + sDict.get(text, text), self._loglevel)
        self.channel.sendall(text)
        
    def read_until(self, expected, timeout):
        data = ''
        time.sleep(self._pausetime)
        start_time = time.time()
        while time.time() < float(timeout) + start_time :
            if self.channel.recv_ready():
                data += self.channel.recv(1)
            else:
                time.sleep(0.00005)
            if data.count(expected) > 0:
                return data
        return data
        
    def read(self, loglevel=None):
        """Reads and returns/logs everything currently available on the output.

        Read message is always returned and logged but log level can be altered
        using optional argument. Available levels are TRACE, DEBUG, INFO and
        WARN.
        """
        loglevel = loglevel == None and self._loglevel or loglevel
        ret = self.read_very_eager()
        self._log(ret, loglevel)
        return ret
    
    def read_very_eager(self):
        time.sleep(self._pausetime)
        if self.channel is None:
            return ""
        data = ''
        #stime = time.time()
        while self.channel.recv_ready():
            data += self.channel.recv(100000)
        return data
    
    def read_until_prompt(self, loglevel=None, timeout_add=True):
        """Reads from the current output until prompt is found.

        Expected is a list of regular expressions, and keyword returns the text
        up until and including the first match to any of the regular
        expressions.
        """
        time.sleep(self._pausetime)
        loglevel = loglevel == None and self._loglevel or loglevel 
        ret = self.expect(self._prompt, self._timeout)
        if ret[0] == -1 :
            self._log(ret[2],'WARN')
            raise AssertionError('No match found for prompt "%s" in %ssec, detail info: "%s"'
                                 % (seq2str([x.pattern for x in self._prompt ], lastsep=' or '), \
                                    timestr_to_secs(self._timeout), ret[2]))
        self._log("Get Response: " + ret[2], loglevel)
        return ret[2]

    def set_prompt(self, *prompt):
        """Sets the prompt used in this connection to 'prompt'.
        'prompt' can also be a list of regular expressions
        """
        old_prompt = self._prompt
        if len(prompt) == 1:
            if isinstance(prompt[0], basestring):
                self._prompt = list(prompt)
            else:
                self._prompt = prompt[0]
        else:
            self._prompt = list(prompt)
        indices = range(len(self._prompt))    
        for i in indices:
            if isinstance(self._prompt[i], basestring):
                self._prompt[i] = re.compile(self._prompt[i], re.MULTILINE)
        return old_prompt

    def get_prompt(self):
        _temp_prompt = []
        if isinstance(self._prompt, basestring):
            return self._prompt
        elif type(self._prompt) in (types.TupleType, types.ListType):
            _temp_prompt = list(self._prompt)
        else:
            raise TypeError(self.__str__() + \
                            " _prompt should be String or List !")
        _temp_prompt_str = []
        for prompt in _temp_prompt:
            if isinstance(prompt, basestring):
                _temp_prompt_str.append(prompt)
            else:
                _temp_prompt_str.append(getattr(prompt, "pattern"))
        return _temp_prompt_str
    
    def start_log_buffer(self):
        """ start copying the print outputs of _log into the log buffer """
        self._log_buffer = ""
        self._log_buffering = True

    def write_log_buffer(self, loglevel):
        """ print the log buffer with the specified loglevel and clear the buffer """
        if self._log_buffer:
            self._log_buffering = False
            self._log(self._log_buffer, loglevel)
            self._log_buffer = ""
            self._log_buffering = True

    def stop_log_buffer(self):
        """ stop copying the print output of _log into the log buffer and clear the buffer """
        self._log_buffering = False
        self._log_buffer = ""

    def _log(self, msg, loglevel=None):
        self._logger.log(msg, loglevel)
        if self._log_buffering:
            self._log_buffer += msg
            
    def _remove_unused_char(self, data):
        return data
        i = 0;
        while i < len(data):
            if data[i] == chr(8):
                if i == 0:                        # BS is first element
                    data = data[1:]              # remove it form buffer and the last from the queue if not LF or CR           
                else:
                    if data[i-1] == chr(10) or data[i-1] == chr(13):
                        data = data[:i] + data[i + 1:]        # remove only BS from buffer
                    else:
                        data = data[:i-1] + data[i + 1:]      # remove BS and previous char from buffer
                        i = i - 1
            else:
                i = i + 1
        return data
    #[32mtdlte-tester@LAB09041-BTS-DNHFH2X [33m~[0m
    #tdlte-tester@LAB09041-BTS-DNHFH2X ~
    #_colorpattern = re.compile("\033\[[0-9;]*m") 
    _colorpattern = re.compile('|'.join([
        r'\x1b\[\d{1,3}[lhinc]',
        r'\x1b\[\d{1,3};\d{1,3}[lhy]',
        r'\x1b\[\d+[ABCDmgKJPLMincq]',
        r'\x1b\[\d+;\d+[HfmrR]',
        r'\x1b\[[HfmKJic]',
        r'\x1b[DME78=>NOHgZc<ABCDIFGKJ\^_WXV\]]',
        r'\x1b[()][AB012]',
        r'\x1b#\d',
        r'\x1bY\d+',
        r'\x1b\/Z',
        r"\033\[[0-9;]*m"
    ]))    
    #_colorpattern = re.compile("\[[0-9;]*m") # modify by cygwim, maybe need add more system color type
    def expect(self, regexps, timeout=None):
        start_time = time.time()
        data = ''
        regexps = [ re.compile(expr) for expr in regexps ]
        while time.time() < start_time + int(timeout):
            if self.channel.recv_ready():                
                data += self.channel.recv(1)
                #print "recvdata=", data, "."
            matching_pattern = [ pattern for pattern in regexps 
                                 if pattern.search(data) ]
            if len(matching_pattern) > 0:
                pattern = matching_pattern[0]
                data = SshCommon._colorpattern.sub("", data)
                #commented by sam, seems like not used by LTETest
                #data = self._remove_unused_char(data)
                return (regexps.index(pattern), pattern.search(data), data)
        return (-1, None, data)
    
    
if __name__ == "__main__":
    host = "10.140.90.12"
    user = "root"
    passwd = "tact"
    sshconn = SshCommon(host, 22, ".*#", newline="LF")
    sshconn.set_timeout(2)
    sshconn.set_loglevel("DEBUG")
    sshconn.login(user, passwd)
    
    
    sshconn.write("ping 127.0.0.1 -c 4")
    
    print sshconn.connected
    sshconn.close_connection()
    print sshconn.connected
