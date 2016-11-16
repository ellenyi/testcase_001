# -*- coding:utf-8 -*-
"""
This module contains one class, SocketClientCommon.
Class SocketClientCommon realizes data sending and receiving on
SOCK_STREAM type socket.socket() which connecting to a remote host.
@author: Qijun Chen
@contact: qijun.chen@nsn.com
@version: 2014-06-25
"""


import select
import socket
import time
import timeit
#from Userdefined.connection_lib import global_logger as log


class SocketClientCommon(object):
    """This a class realizes:
       Data sending and receiving through a socket.socket() connection 
       which is SOCK_STREAM type. 
       You can consider it as a TCP-like connection.
       This class connects to only one remote host at a time.
    """
    
    # length of data to recv on each socket.socket.recv() call
    RECV_SIZE = 8192
    TIMEOUT_DIV = 5.0
    
    def __init__(self, host, port, data_op_timeout=3):
        """@param host: string of host's name or IP.
           @param port: integer number.
           @param data_op_timeout: 
            this timeout influence self.recv_data() and self.send_data().
            1. if expected length of data is not received during a whole 
               'data_op_timeout', then, recv_data() will return what 
               it already received.
            2. if socket is not writable during a whole 'data_op_timeout', 
               then, send_data() will fail.
            3. socket.socket()'s timeout will be 
               1/TIMEOUT_DIV of 'data_op_timeout'
        """
        super(SocketClientCommon, self).__init__()
        self._socket_instance = None
        self._host = host
        self._port = port
        self._is_open = False
        self._data_op_timeout = data_op_timeout
        # use name 'timeout' rather than '_timeout', is for keeping unity with 
        # -> serial_common.SerialCommon()'s property 'timeout'
        self.timeout = data_op_timeout / self.TIMEOUT_DIV
    
    def set_data_op_timeout(self, data_op_timeout):
        """re-set data_op_timeout.
           See __init__'s doc string for more info about this property.
           This method will NOT close socket connection if it is open.
           @return: previous data_op_timeout value.
        """
        previous_timeout = self._data_op_timeout
        self._data_op_timeout = data_op_timeout
        self.timeout = data_op_timeout / self.TIMEOUT_DIV
        if self._socket_instance:
            self._socket_instance.settimeout(self.timeout)
        return previous_timeout
    
    def is_open(self):
        """@return: True/False, indicates whether socket is connected to a
            remote host or not.
        """
        return self._is_open
    
    def open_connection(self, host=None, port=-1, data_op_timeout=-1):
        """Instantiate a new socket.socket() instance, try to connect it to
           host:port, and set its timeout.
           IPv6 host supported.
           If instantiating or connecting failed, raise Exception.
           @param host, port, data_op_timeout: see __init__'s doc string.
        """
        if self._is_open:
            return True
        
        # If host, port and data_op_timeout are default values, that means to 
        # use self._host, self._port, self._data_op_timeout instead.
        if host == None:
            host = self._host
        if port == -1:
            port = self._port
        if data_op_timeout == -1:
            data_op_timeout = self._data_op_timeout
        timeout = data_op_timeout / self.TIMEOUT_DIV
        
        # parameter validation check
        if not host:
            raise Exception('Cannot establish socket connection, ' + 
                            '"host" is empty or invalid: %s' %repr(host))
        if not port:
            raise Exception('Cannot establish socket connection, ' + 
                            '"port" is invalid: %s' %repr(port))
        if data_op_timeout < 0:
            raise Exception('Cannot establish socket connection, ' + 
                            '"data_op_timeout" is invalid(< 0): %s' 
                            %repr(data_op_timeout))
        
        # instantiate a socket.socket() with first address family available 
        for ret in socket.getaddrinfo(host, port, socket.AF_UNSPEC, 
                                      socket.SOCK_STREAM):
            family, sock_type, proto, canon_name, sock_addr = ret
            try:
                self._socket_instance = socket.socket(family, sock_type, proto)
            except socket.error, err_info:
                log.debug('Failed to instantiate socket(): %s' %err_info)
                self._socket_instance = None
                continue
            # set timeout before connecting
            self._socket_instance.settimeout(timeout)
            self.timeout = timeout
            try:
                self._socket_instance.connect(sock_addr)
                self._host = host
                self._port = port
                self._is_open = True
            except socket.error, err_info:
                log.debug('Failed to connect socket() to "%s:%d": %s' 
                          %(sock_addr[0], sock_addr[1], err_info))
                self._socket_instance.close()
                self._socket_instance = None
                self._is_open = False
                continue
            # instantiate and connect succeeded, break
            break
        if self._socket_instance == None:
            raise Exception('Failed to establish socket connection to ' + 
                            '"%s:%d": %s' %(host, port, err_info))
        else:
            return True
    
    def close_connection(self):
        """Close internal socket instance's established connection.
        """
        if not self._is_open:
            return True
        try:
            self._socket_instance.shutdown(socket.SHUT_RDWR)
            self._socket_instance.close()
        except Exception, err_info:
            log.info('Close socket "%s:%d" failed with exception: "%s"\n'
                     %(self._host, self._port, err_info) +
                     'This error is ignored.')
        del self._socket_instance
        self._socket_instance = None
        self._is_open = False
        return True
    
    def is_ready_to_recv(self):
        ready_to_read, _, _ = select.select([self._socket_instance], [], [], 
                                            self.timeout)
        return True if ready_to_read else False
    
    def recv_all_avail_data(self, timeout=None):
        """recv all available data from socket until socket is unreadble, or timeout 
        is reached.
        @note: added by Sam at 2015/01/19 when debug tm500 multi ue socket recv problem.
        """
        ret = ""
        starttime = time.time()
        while self.is_ready_to_recv():
            buf = self._socket_instance.recv(self.RECV_SIZE)
            if buf == "":
                break
            ret += buf
            if timeout is not None:
                if time.time() - starttime >= timeout:
                    break
        return ret
        
    def recv_data(self, expect_recv_len=1, use_timeout=True, temp_timeout=None):
        """Receive data from the connected internal socket instance.
           @param expect_recv_len:
            *if len(data_already_recv) >= expect_recv_len,
             return ALL received data immediately.
            *otherwise, recv and return as much data as possible until
             a self._data_op_timeout(which is set/changed by __init__
             and/or self.set_data_op_timeout(), or param temp_timeout).
           @param use_timeout: 
            *True  -> to use timeout mechanism.
            *False -> NOT to use timeout mechanism;
             will return immediately after first trial of data recv,
             this is NOT recommended unless,
             you are very clear about your requirement.
           @param temp_timeout:
            change self._data_op_timeout temporarily during this method call.
           @return: 'string of data' or ''.
        """
        def _get_data_from_buffer():
            if not self.is_ready_to_recv():
                return ''
            else:
                return self._socket_instance.recv(self.RECV_SIZE)
        
        # re-set self._data_op_timeout if needed
        if use_timeout and temp_timeout != None:
            previous_op_timeout = self.set_data_op_timeout(temp_timeout)
        if use_timeout:
            start_time = timeit.default_timer()
        
        ret_str = _get_data_from_buffer()
        if use_timeout and expect_recv_len <= 0:
            if temp_timeout != None:
                self.set_data_op_timeout(previous_op_timeout)
            return ret_str
        elif not use_timeout:
            return ret_str
        
        while use_timeout and (len(ret_str) < expect_recv_len) and \
           (timeit.default_timer() - start_time + self.timeout <= 
            self._data_op_timeout):
            time.sleep(self.timeout)
            ret_str += _get_data_from_buffer()
            if len(ret_str) >= expect_recv_len:
                break
        if temp_timeout != None:
            self.set_data_op_timeout(previous_op_timeout)
        return ret_str
    
    def send_data(self, data_to_send, use_timeout=True):
        """Send data to remote host by internal socket instance.
           This method does not guarantee successful data sending even when
           return value is True.
           Please use some method in upper level to guarantee it if needed.
           @param data_to_send: string type
            *No ctrl-char will be added before sending, i.e. \r \n;
            *Thus, please input all characters needed through this parameter.
           @param use_timeout:
            *True  -> to use timeout mechanism.
            *False -> NOT to use timeout mechanism;
             will return False immediately if socket is not writable at first
             trial, this is NOT recommended unless,
             you are very clear about your requirement.
           @return: True/False, but please do NOT treat return value as
            guarantee of successful data sending.
        """
        type_of_data = type(data_to_send)
        if type_of_data not in (str, unicode):
            raise Exception('Socket "%s:%d", "data_to_send" is NOT ' 
                            %(self._host, self._port) + 
                            'string, it is %s' %type_of_data)
        if not len(data_to_send):
            raise Exception('Socket "%s:%d", "data_to_send" is empty!'
                            %(self._host, self._port))
        
        if use_timeout:
            start_time = timeit.default_timer()
        
        _, ready_to_write, _ = \
            select.select([], [self._socket_instance], [], self.timeout)
        while use_timeout and (not ready_to_write) and \
           (timeit.default_timer() - start_time + self.timeout <= 
            self._data_op_timeout):
            time.sleep(self.timeout)
            _, ready_to_write, _ = \
                select.select([], [self._socket_instance], [], self.timeout)
        if not ready_to_write:
            log.info('Socket "%s:%d" is not ready for data sending! '
                     %(self._host, self._port) + 'No data sent.')
            return False
        else:
            self._socket_instance.sendall(data_to_send)
            return True


if __name__ == "__main__":
    sock = SocketClientCommon('10.69.81.29', 8081)
    sock.send_data("testing\r\n")
    print sock.recv_data()
    sock.close_connection()
