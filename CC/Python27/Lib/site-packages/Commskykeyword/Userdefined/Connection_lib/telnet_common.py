"""Provides enhancements of Python's BuiltIn's telnet Library
Common class, any of these methods should be contribute to all of our library.
Domain specficed, and tools specfied operation should not placed here !!!
"""

import re
import os
import time
import telnetlib
import types
import socket


from robot_api import timestr_to_secs
from robot_api import secs_to_timestr
from robot_api import seq2str
from robot_api import get_time

     
import logging
logger = logging.getLogger("ssh_common")

if os.name == 'java':
    from select import cpython_compatible_select as select
else:
    from select import select

REGEXP = re.compile('|'.join([
    r'\x1b\[\d{1,3}[lhinc]',
    r'\x1b\[\d{1,3};\d{1,3}[lhy]',
    r'\x1b\[\d+[ABCDmgKJPLMincq]',
    r'\x1b\[\d+;\d+[HfmrR]',
    r'\x1b\[[HfmKJic]',
    r'\x1b[DME78=>NOHgZc<ABCDIFGKJ\^_WXV\]]',
    r'\x1b[()][AB012]',
    r'\x1b#\d',
    r'\x1bY\d+',
    r'\x1b\/Z'
]))

class TelnetCommon(telnetlib.Telnet):

    def __init__(self, host, port, prompt, timeout="10sec", newline='CRLF'):
        self.host = host
        self.port = port == '' and 23 or int(port)
        self._timeout = float(timestr_to_secs(timeout))
        telnetlib.Telnet.__init__(self, self.host, self.port)
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
        self.conn_type = "TELNET"
        self.device_type = None

        #dump_telnet = os.getenv("DUMP_TELNET", "NO") == 'YES'
        #TO DO: dump every connection seesion's baklog to case's log file.
        #self._dumper = dump_telnet and FileDumper(flag="telnet-%s" %(self.host)) or DummyDumper()
        if os.getenv("TDLTE_DUMP_TELNET", "NO") == 'YES':
            self._logger = FileLogger()

    def __str__(self):
        return str(self.host) + ":" + str(self.port) + " DeviceType:" + str(self.device_type) + " Timeout:"\
            + secs_to_timestr(self._timeout) + " " + repr(self)

    def __del__(self):
        """Override Telnet.__del__ because it sometimes causes problems"""
        pass
    
    @property
    def connected(self):
        try:
            self.sock.recv(0)
        except socket.error:
            return False
        except Exception, _:
            return False
        else:
            return True 
    
    def open(self, host, port=0, *args):
        """Override Telnet.open set timeout of create connection!"""
        self.eof = 0
        if not port:
            port = telnetlib.TELNET_PORT
        self.host = host
        self.port = port
        msg = "getaddrinfo returns an empty list"
        for res in socket.getaddrinfo(host, port, 0, socket.SOCK_STREAM):
            af, socktype, proto, canonname, sa = res
            try:
                self.sock = socket.socket(af, socktype, proto)
                self.sock.settimeout(self._timeout)
                #^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
                self.sock.connect(sa)
            except socket.error, msg:
                if self.sock:
                    self.sock.close()
                self.sock = None
                continue
            break
        if not self.sock:
            raise socket.error, msg
        self.connected = True

    def read_all_avail_data(self, loglevel=None):
        """read all the avail data from socket, don't use self.sock.recv, it may cause problems"""
        time.sleep(self._pausetime)
        loglevel = loglevel == None and self._loglevel or loglevel        
        ret = ""
        try:
            self.process_rawq()
            while not self.eof and select([self.fileno()], [], [], 1) != ([], [], []):
                self.fill_rawq()
                self.process_rawq()
            ret = self.read_very_lazy()                                
        except Exception, e:
            self._log(str(e), "WARN")
        self._log("Get Response: " + ret, loglevel)
        return ret

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
        self._timeout = self.timeout = float(timestr_to_secs(timeout))
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
        """Closes current Telnet connection.

        Logs and returns possible output.
        """
        loglevel = loglevel == None and self._loglevel or loglevel
        telnetlib.Telnet.close(self)
        ret = self.read_all()
        self._log(ret, loglevel)
        self._log("Disconnect from %s" % str(self), self._loglevel)
        #self._dumper.close()
        self.connected = False
        return ret

    def login(self, username='', password='', login_prompt='ogin: ',
              password_prompt='assword: '):
        """Logs in to Telnet server with given user information.

        The login keyword reads from the connection until login_prompt is
        encountered and then types the username. Then it reads until
        password_prompt is encountered and types the password. The rest of the
        output (if any) is also read and all text that has been read is
        returned as a single string.

        Prompt used in this connection can also be given as optional arguments.
        """
        self.username = username
        self.password = password
        origprompt = self.get_prompt()
        ret = ''
        if username != '':
            self.set_prompt(login_prompt)
            ret += self.read_until_prompt(None) + username+'\n'
            self.write(username)
        if password != '':
            self.set_prompt(password_prompt)
            ret += self.read_until_prompt(None) + '*'*len(password)+'\n'
            self.write(password)
        self.set_prompt(origprompt)
        if self._prompt is None:
            time.sleep(1)
            ret += self.read(None)
        else:
            if ret.find("openSUSE") == -1:
                self._log("not SUSE system")
                #ret += self.read_until_prompt()
            else:
                self._log("SUSE system")
                ret += self.read(None)
                self._log(ret.find("Terminal type?"))
                self.write("vt100")    # add default Terminal type
                #ret += self.read_until_prompt()
            time.sleep(self._pausetime)    
            ret = self.expect(self._prompt, self._timeout)
            if ret[0] == -1 :
                self._log("Get Response: " + ret[2],'WARN')
                raise AssertionError('No match found for prompt "%s" in %ssec, detail info: "%s"'
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
            msg = 'Only ascii characters are allowed in telnet. Got: %s' % text
            raise ValueError(msg)
        if text not in (self._newline, ""):
            sDict = {chr(3):"Ctrl-C", chr(13) : "Ctrl-M", chr(24): "Ctrl-X", chr(25): "Ctrl-Y"}
            self._log("Execute command: " + sDict.get(text, text), self._loglevel)
        telnetlib.Telnet.write(self, text)
        #self._dumper.write("\n<--%s-->\n" % text)

    def read(self, loglevel=None):
        """Reads and returns/logs everything currently available on the output.

        Read message is always returned and logged but log level can be altered
        using optional argument. Available levels are TRACE, DEBUG, INFO and
        WARN.
        """

        ret = self.read_all_avail_data(loglevel)
        return ret  

    def read_until_prompt(self, loglevel=None, timeout_add=True):
        """Reads from the current output until prompt is found.

        Expected is a list of regular expressions, and keyword returns the text
        up until and including the first match to any of the regular
        expressions.
        """
        time.sleep(self._pausetime)
        loglevel = loglevel == None and self._loglevel or loglevel
        ret = self.expect(self._prompt, self._timeout, timeout_add)
        if ret[0] == -1 :
            self._log("Get Response: " + ret[2],'WARN')
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
            self._logger.log(self._log_buffer, loglevel)
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

    def expect(self, li, timeout=None, timeout_add=True):
        self._log("Telnet: >>expect %s" % get_time(), "TRACE")
        re = None
        indices = range(len(li))
        if timeout is not None:
            _old_timeout = timeout
            time_start = time.time()
        while 1:
            self.process_rawq()
            #pos = max(0, len(self.cookedq) - 50)
            # change '50' to '256' as sometimes the length of prompt could be more than 50 characters
            self.cookedq = REGEXP.sub('', self.cookedq)
            pos = max(0, len(self.cookedq) - 256)
            for i in indices:
                m = li[i].search(self.cookedq, pos)
                if m:
                    text = self.cookedq[:m.end()]
                    self.cookedq = self.cookedq[m.end():]
                    #print "*DEBUG* |%s| %d %d" % (m.string[m.start():m.end()], m.end(), m.endpos)
                    self._log("Telnet: <<expect %s found % s" % (get_time(), li[i].pattern), "TRACE")
                    return (i, m, text)
            if self.eof:
                self._log("Telnet: Eof detected", "WARN")
                break
            if timeout is not None:
                elapsed = time.time() - time_start
                if elapsed >= timeout:
                    self._log("Telnet: Elapsed time exceeds timeout -> No further check", "WARN")
                    break
                s_args = ([self.fileno()], [], [], 5) # timeout-elapsed)
                #self._log("Telnet: waiting select...", "Trace")
                r, w, x = select(*s_args)
                #self._log("Telnet: select end  r:%s w:%s x:%s" % (r, w, x), "Trace")
                #self._log("Telnet: timeout:%s   elapsed:%s __timeout:%s" % (timeout, elapsed, self._timeout), "Trace")

                if not r:
                    continue
                else:
                    if timeout_add is True:
                        time_start = time.time()
                        timeout = _old_timeout
                        
            self.fill_rawq()
        text = self.read_very_lazy()
        if not text and self.eof:
            self._log("Telnet: <<expect %s raise eof error" % get_time(), "WARN")
            raise EOFError
        self._log("Telnet: <<expect %s no any pattern matched" % get_time(), "WARN")
        return (-1, None, text)


    def process_rawq(self):
        """Transfer from raw queue to cooked queue.

        Set self.eof when connection is closed.  Don't block unless in
        the midst of an IAC sequence.

        """
        buf = ['', '']
        try:
            while self.rawq:
                c = self.rawq_getchar()
                #self._dumper.write(c)
                if not self.iacseq:
                    if c == telnetlib.theNULL:
                        continue
                    if c == "\021":
                        continue
                    if c != telnetlib.IAC:
                        buf[self.sb] = buf[self.sb] + c
                        continue
                    else:
                        self.iacseq += c
                elif len(self.iacseq) == 1:
                    # 'IAC: IAC CMD [OPTION only for WILL/WONT/DO/DONT]'
                    if c in (telnetlib.DO, telnetlib.DONT, telnetlib.WILL, telnetlib.WONT):
                        self.iacseq += c
                        continue

                    self.iacseq = ''
                    if c == telnetlib.IAC:
                        buf[self.sb] = buf[self.sb] + c
                    else:
                        if c == telnetlib.SB: # SB ... SE start.
                            self.sb = 1
                            self.sbdataq = ''
                        elif c == telnetlib.SE:
                            self.sb = 0
                            self.sbdataq = self.sbdataq + buf[1]
                            buf[1] = ''
                        if self.option_callback:
                            # Callback is supposed to look into
                            # the sbdataq
                            self.option_callback(self.sock, c, telnetlib.NOOPT)
                        else:
                            # We can't offer automatic processing of
                            # suboptions. Alas, we should not get any
                            # unless we did a WILL/DO before.
                            self.msg('IAC %d not recognized' % ord(c))
                elif len(self.iacseq) == 2:
                    cmd = self.iacseq[1]
                    self.iacseq = ''
                    opt = c
                    if opt in [telnetlib.SGA, telnetlib.ECHO]:
                        if cmd == telnetlib.DO:
                            self.sock.sendall(telnetlib.IAC + telnetlib.WILL + opt)
                        elif cmd == telnetlib.WILL:
                            self.sock.sendall(telnetlib.IAC + telnetlib.DO + opt)
                        else:
                            pass
                    elif cmd in (telnetlib.DO, telnetlib.DONT):
                        self.msg('IAC %s %d',
                            cmd == telnetlib.DO and 'DO' or 'DONT', ord(opt))
                        if self.option_callback:
                            self.option_callback(self.sock, cmd, opt)
                        else:
                            self.sock.sendall(telnetlib.IAC + telnetlib.WONT + opt)
                    elif cmd in (telnetlib.WILL, telnetlib.WONT):
                        self.msg('IAC %s %d',
                            cmd == telnetlib.WILL and 'WILL' or 'WONT', ord(opt))
                        if self.option_callback:
                            self.option_callback(self.sock, cmd, opt)
                        else:
                            self.sock.sendall(telnetlib.IAC + telnetlib.DONT + opt)
        except EOFError: # raised by self.rawq_getchar()
            self.iacseq = '' # Reset on EOF
            self.sb = 0
            pass
        i = 0;
        while i < len(buf[0]):
            if buf[0][i] == chr(8):
                if i == 0:                        # BS is first element
                    buf[0] = buf[0][1:]              # remove it form buffer and the last from the queue if not LF or CR
                    if len(self.cookedq) != 0 and (self.cookedq[-1] != chr(10) and self.cookedq[-1] != chr(13)):
                        self.cookedq = self.cookedq[:-1]
                else:
                    if buf[0][i-1] == chr(10) or buf[0][i-1] == chr(13):
                        buf[0] = buf[0][:i] + buf[0][i + 1:]        # remove only BS from buffer
                    else:
                        buf[0] = buf[0][:i-1] + buf[0][i + 1:]      # remove BS and previous char from buffer
                        i = i - 1
            elif buf[0][i] > chr(127):
                buf[0] = buf[0][:i] + buf[0][i + 1:]        # remove only this invalid char from buffer
            else:
                i = i + 1

        self.cookedq = self.cookedq + buf[0]
        self.sbdataq = self.sbdataq + buf[1]


if __name__ == "__main__":
#     import StringIO
#     RDB_TELNET_HOOKER = StringIO.StringIO()

    #telnetlib.DEBUGLEVEL = 9
    host = "10.69.67.67"
    user = "airtester"
    passwd = "airtest"
    telconn = TelnetCommon(host, 23, "\w:.*>", "2")
    telconn.set_timeout(1)
    telconn.set_loglevel("DEBUG")
    telconn.login(user, passwd)
    telconn.write("ls -al")
    telconn.read_until_prompt()
    telconn.write("pwd")
    telconn.read_until_prompt()
    telconn.write("cd ..")
    telconn.read_until_prompt()
    telconn.write("pwd")
    telconn.read_until_prompt()
    telconn.write("ping 127.0.0.1 -n 5")
    time.sleep(1)
    old_newline = telconn.set_newline(None)
    telconn.write(chr(3))
    telconn.set_newline(old_newline)
    #telconn.write("ping 127.0.0.1 -n 20")
    telconn.read_until_prompt()
    telconn.write("pwd")
    telconn.read_until_prompt()
    telconn.write("ping 127.0.0.1 -n 5")
    time.sleep(1)
    telconn.set_newline(None)
    telconn.write(chr(3))
    #telconn.set_newline(old_newline)
    #telconn.write("ping 127.0.0.1 -n 20")
    telconn.read_until_prompt()
    telconn.read_all_avail_data()
    print telconn.connected
    telconn.close_connection()  
    print telconn.connected
#     print "+++++++++++++++++++++++++++++++"
#     print RDB_TELNET_HOOKER.getvalue()  

