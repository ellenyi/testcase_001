"""Basic python ssh connection base on python paramiko module, define basic operation for ssh
Usage is same as telnet_connection
"""

import re
import time
import types
import logging
import sys

import paramiko

logger = logging.getLogger("csrd.ssh_client")
#===============================================================================
# logger.setLevel(logging.DEBUG)
# if not logger.handlers:
#     ch = logging.StreamHandler(stream=sys.stdout)
#     ch.setLevel(logging.DEBUG)
#     logger.addHandler(ch)
#===============================================================================

class SshClient:
    def __init__(self, host, port, prompt, timeout="10", newline='CRLF'):
        self.host = host    
        self.port = port == '' and 22 or int(port)
        
        self._timeout = str(timeout)
        self._newline = newline.upper().replace('LF','\n').replace('CR','\r')
        self._prompt = None
        self.set_prompt(prompt)
        
        """
        self._logger = logging.getLogger("main.ssh")
        self._logger.setLevel(logging.DEBUG)
        ch = logging.StreamHandler(stream=sys.stdout)
        ch.setLevel(logging.DEBUG)
        self._logger.addHandler(ch)
        """
        self._logger = logger
        self.username = None
        self.password = None

        self._channel = None
        self.client = paramiko.SSHClient()
        self.client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

    @property
    def channel(self):
        if not self._channel:
            self._channel = self.client.invoke_shell()
            #combine stderr to stdout
            self._channel.set_combine_stderr(True)
        return self._channel
            
    def __str__(self):
        return str(self.host) + ":" + str(self.port) + repr(self)

    
    def set_timeout(self, timeout):
        old = self._timeout
        self._timeout = str(timeout)
        #self.channel.settimeout(self._timeout)
        return old
    
    def close_connection(self, loglevel=None):
        """Closes current Ssh connection.

        Logs and returns possible output.
        """
        self.client.close()
        self.client = None
        self._channel = None       
        self._logger.info("Disconnect from %s" % str(self))

    def login(self, username, password, login_prompt='ogin: ',
              password_prompt='assword: '):
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
        
        ret = self.expect(self._prompt, self._timeout)
        if ret[0] == -1 :
            self._logger.warn(ret[2])
            raise AssertionError('No match found for prompt "%s", detail info: "%s" '
                                 % (" or ".join([x.pattern for x in self._prompt ]), ret[2]))
        missbuf = self.read()
        self._logger.info(ret[2] + missbuf)
        return ret[2] + missbuf
    
    def __sftp_callback(self, size, filesize):
        self._logger.debug("transmit size: %s filesize is: %s" % (size, filesize))
        
    def put_file(self, localpath, remotepath):
        sftp = self.client.open_sftp()
        #sftp.put(localpath, remotepath, callback=self.__sftp_callback, confirm=True)
        sftp.put(localpath, remotepath, confirm=True)
        
    def get_file(self, remotepath, localpath):
        sftp = self.client.open_sftp()
        #sftp.get(remotepath, localpath, callback=self.__sftp_callback)
        sftp.get(remotepath, localpath)

    def execute_command(self, cmd):
        prev_ret = self.read_very_eager()
        self._logger.info(prev_ret)
        self.write(cmd)
        time.sleep(0.05)
        ret = self.read_until_prompt()
        return ret #+ self.read_very_eager()
    
    def execute_command_internal(self, cmd):
        _in, _out, _error = self.client.exec_command(cmd)
        return _out.read()
    
    def write(self, text):
        """Writes given text over the connection and appends newline"""
        self.write_bare(text + self._newline)

    def write_bare(self, text):
        """Writes given text over the connection without appending newline"""
        try:
            text = str(text)
        except UnicodeError:
            msg = 'Only ascii characters are allowed in ssh. Got: %s' % text
            raise ValueError(msg)
        
        if text != self._newline:
            sDict = {chr(3):"Ctrl-C", "\x18": "Ctrl-X", "\x19": "Ctrl-Y"}
            self._logger.info("Execute command: " + sDict.get(text, text))
        self.channel.sendall(text)
        
    def read_until(self, expected, timeout):
        """read until expected string appeared in socket buffer."""
        data = ''
        time.sleep(self._pausetime)
        start_time = time.time()
        while time.time() < float(timeout) + start_time :
            if self.channel.recv_ready():
                data += self.channel.recv(1)
            if data.count(expected) > 0:
                return data
        return data
        
    def read(self):
        """Reads and returns/logs everything currently available on the output.
        """
        ret = self.read_very_eager()
        self._logger.info(ret)
        return ret
    
    def read_very_eager(self):
        if self.channel is None:
            return ""
        data = ''
        #stime = time.time()
        while self.channel.recv_ready():
            data += self.channel.recv(128)
            time.sleep(0.005)
        return data
    
    def read_until_prompt(self):
        """Reads from the current output until prompt is found.

        Expected is a list of regular expressions, and keyword returns the text
        up until and including the first match to any of the regular
        expressions.
        """
        ret = self.expect(self._prompt, self._timeout)
        if ret[0] == -1 :
            self._logger.warn(ret[2])
            raise AssertionError('No match found for prompt "%s" in %ssec, detail info: "%s"'
                                 % (" or ".join([x.pattern for x in self._prompt ]), \
                                    self._timeout, ret[2]))
        self._logger.info("Get Response: " + ret[2])
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
        return _temp_prompt
    
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
    
    _colorpattern = re.compile("\033\[[0-9;]*m") 
    def expect(self, regexps, timeout=None):
        start_time = time.time()
        data = ''
        regexps = [ re.compile(expr) for expr in regexps ]
        while time.time() < start_time + int(timeout):
            if self.channel.recv_ready():                
                data += self.channel.recv(512)
                #print "recvdata=", data, "."
            matching_pattern = [ pattern for pattern in regexps 
                                 if pattern.search(data) ]
            if len(matching_pattern) > 0:
                pattern = matching_pattern[0]
                data = SshClient._colorpattern.sub("", data)
#                 while self.channel.recv_ready():
#                     data += self.channel.recv(128)
#                     time.sleep(0.005)
                #commented by sam, seems like not used by LTETest
                #data = self._remove_unused_char(data)
                return (regexps.index(pattern), pattern.search(data), data)
        return (-1, None, data)
    
if __name__ == "__main__":  
    host = "10.69.71.98"
    user = "toor4nsn"
    passwd = "oZPS0POrRieRtu"
    sshconn = SshClient(host, 22, "^[a-zA-Z]+[@:~\s\w]+[>#$]$", timeout=5, newline="LF")
    sshconn.login(user, passwd)
    ret = sshconn.execute_command("ls -al /")
    print "xx@!@"
    print ret
