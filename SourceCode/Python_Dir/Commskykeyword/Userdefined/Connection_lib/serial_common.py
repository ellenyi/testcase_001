# -*- coding:utf-8 -*-
"""
This module contains one class, SerialCommon.
Class SerialCommon realizes data receiving and sending on serial port.
@author: Qijun Chen
@contact: qijun.chen@nsn.com
@version: 2014-06-06
"""


import copy
import time
import timeit
try:
    import threading as _threading
except ImportError:
    import dummy_threading as _threading
import serial
#from Commskykeyword.Userdefined.logging import global_logger as log


class SerialCommon(serial.Serial):
    """A base class realizes operations on serial port.
       Each instance of this class bind to one physical serial port.
    """
    
    PARITY_NONE, PARITY_ODD, PARITY_EVEN = 'N', 'O', 'E'
    READING_INTERVAL = 0.03
    TIMEOUT_DIV = 10.0
    
    def __init__(self, port='COM1', 
                 baudrate=9600, parity=PARITY_NONE, bytesize=8, stopbits=1, 
                 data_buffer_size=16384, data_op_timeout=3):
        """@param port, baudrate, parity, bytesize, stopbits:
            are parameters of serial.Serial(), serial port's properties.
           @param data_buffer_size: this class define an internal data buffer,
            this parameter define the size of that data buffer, unit is bytes.
           @param data_op_timeout:
            this timeout influence self.recv_data() and self.send_data().
            1. if expected length of data is not received during a whole 
               'data_op_timeout', then, recv_data() will return what 
               it already received.
            2. if serial port is not writable during a whole 'data_op_timeout', 
               then, send_data() will fail.
            3. serial.Serial().timeout will be 1/10 of this 'data_op_timeout'.
        """
        super(SerialCommon, self).__init__()
        # serial.Serial's property
        self.port = int(port[3:]) - 1
        self.baudrate = baudrate
        self.parity = parity
        self.timeout = data_op_timeout / self.TIMEOUT_DIV
        self.bytesize = bytesize
        self.stopbits = stopbits
        # self defined property
        self.port_name = port
        self._is_open = False # port open or not, to control reading thread
        self._is_sending_data = False
        self._is_reading_data = False
        self._reading_thread = None
        self._data_buffer = ''
        self._data_buffer_size = data_buffer_size
        self._data_op_timeout = data_op_timeout
    
    @staticmethod
    def get_os_serial_port_info():
        """Get all available serial ports' info from OS, format as COMx.
           @return: ["COM1", "COM2", ...] or []
        """
        import os
        if os.name == 'nt':  # Windows OS
            import win32api, win32con
            key = win32api.RegOpenKey(win32con.HKEY_LOCAL_MACHINE, 
                                      r'HARDWARE\DEVICEMAP\SERIALCOMM')
            num = win32api.RegQueryInfoKey(key)[1]  # get number of values
            values = []
            for idx in range(0, num):
                values.append(win32api.RegEnumValue(key, idx)[1])
            values.sort()
            return list(set(values))
        elif os.name == 'posix':  # Linux OS
            import glob
            value = glob.glob('/dev/ttyS*')
            values = ['COM%s' %( int(elem[elem.find('ttyS')+4:])+1 ) 
                      for elem in value ]
            values.sort()
            return list(set(values))
        else:
            log.info('Cannot get serial port info from your ' +
                     'operating system: %s' %os.name)
            return []
    
    def reconfigure_port(self, port='COM1', baudrate=9600, parity=PARITY_NONE, 
                         bytesize=8, stopbits=1):
        """Re-configure serial port's parameters.
           Use this method when port is closed.
           @return: True/False
        """
        if self._is_open:
            return False
        self.port_name = port
        self.port = int(port[3:]) - 1
        self.baudrate = baudrate
        self.parity = parity
        self.bytesize = bytesize
        self.stopbits = stopbits
        return True
    
    def set_data_op_timeout(self, data_op_timeout):
        """re-set data_op_timeout.
           See __init__'s doc string for more info about this property.
           This method will NOT close serial port if it is open.
           @return: previous data_op_timeout value.
        """
        previous_timeout = self._data_op_timeout
        self._data_op_timeout = data_op_timeout
        self.timeout = data_op_timeout / self.TIMEOUT_DIV
        self.setTimeout(self.timeout)
        return previous_timeout
    
    def is_open(self):
        """@return: True/False, indicates whether port is open or not.
        """
        return self._is_open
    
    def open_connection(self):
        """Open the binded serial port, and start a child thread to read data
           from it continuously, and store data to an internal data buffer.
           @return: True/False
        """
        if self._is_open:
            return True
        # wait to stop reading thread if any
        while True == self._is_reading_data:
            time.sleep(0.001)
        # open port
        try:
            self.open()
            self._is_open = True
        except Exception, err_info:
            raise Exception('Serial port %s open failed with exception: %s'
                            %(self.port_name, err_info))         
        # start thread of reading
        if self._reading_thread and self._reading_thread.isAlive():
            while self._reading_thread.isAlive():
                time.sleep(0.001)
        self._reading_thread = _threading.Thread(
                               target=self.__reading_thread_method)
        self._reading_thread.start()
        return True
    
    def __reading_thread_method(self):
        last_read_time = timeit.default_timer()
        # keep reading data while port is open
        while True == self._is_open:
            if timeit.default_timer() - last_read_time < self.READING_INTERVAL:
                time.sleep(0.005)
                continue
            if not self.readable():
                last_read_time = timeit.default_timer()
                continue
            # if serial instance is sending data, wait
            while True == self._is_sending_data:
                time.sleep(0.001)
            # read data
            self._is_reading_data = True
            last_read_time = timeit.default_timer()
            raw_data = self.readall()
            if raw_data:  # data received
                self._data_buffer += raw_data
                if len(self._data_buffer) > self._data_buffer_size:
                    self._data_buffer = \
                    self._data_buffer[-self._data_buffer_size:]
            self._is_reading_data = False
    
    def close_connection(self):
        """Close the binded serial port, and terminate child thread 
           which is for data reading.
           @return: True/False
        """
        if not self._is_open:
            return True
        else:
            self._is_open = False
            time.sleep(0.01)
            while self._is_reading_data:
                time.sleep(0.001)
            if self._reading_thread:
                while self._reading_thread.isAlive():
                    time.sleep(0.001)
                self._reading_thread = None
            self.close()
            return True
    
    def recv_data(self, expect_recv_len=1, use_timeout=True, temp_timeout=None):
        """Get data from internal data buffer.
           Data in internal data buffer is read form the binded
           serial port continuously by a child thread.
           @param expect_recv_len:
            *if len(data_in_buffer) >= expect_recv_len,
             return ALL data in buffer;
            *otherwise, read and return as much data as possible until
             a self._data_op_timeout(which is set/changed by __init__
             and/or self.set_data_op_timeout(), or param temp_timeout).
           @param use_timeout: 
            *True  -> to use timeout mechanism.
            *False -> NOT to use timeout mechanism;
             will return all data in internal data buffer immediately,
             this is NOT recommended unless,
             you are very clear about your requirement.
           @param temp_timeout:
            change self._data_op_timeout temporarily during this method call.
           @return: 'string of data' or ''.
        """
        def _get_data_from_buffer():
            self._is_sending_data = True
            while True == self._is_reading_data:
                time.sleep(0.001)
            ret_str = copy.deepcopy(self._data_buffer)
            self._data_buffer = ''
            self._is_sending_data = False
            return ret_str
        
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
        """Send data through the binded serial port.
           Port should be open at first.
           @param data_to_send: string type
            *No ctrl-char will be added before sending, i.e. \r \n;
            *Thus, please input all characters needed through this parameter.
           @param use_timeout:
            *True  -> to use timeout mechanism.
            *False -> NOT to use timeout mechanism;
             will return False immediately if serial port is not writable 
             at first trial, this is NOT recommended unless,
             you are very clear about your requirement.
           @return: True/False
        """
        if not self._is_open:
            raise Exception('Serial port %s is not open, cannot send data!'
                            %self.port_name)
        type_of_data = type(data_to_send)
        if type_of_data not in (str, unicode):
            raise Exception('Serial port %s, "data_to_send" is NOT ' + 
                            'string, it is %s' %type_of_data)
        if not len(data_to_send):
            raise Exception(('Serial port %s, "data_to_send" is empty!'
                             %self.port_name))
        
        if use_timeout:
            start_time = timeit.default_timer()
        
        while use_timeout and (not self.writable()) and \
           (timeit.default_timer() - start_time + self.timeout <= 
            self._data_op_timeout):
            time.sleep(self.timeout)
        if not self.writable():
            log.info('Serial port %s, is not ready for data sending! '
                     %self.port_name + 'No data sent.')
            return False
        else:
            self._is_sending_data = True
            while True == self._is_reading_data:
                time.sleep(0.001)
            self.write(data_to_send)
            self.flush()
            self._is_sending_data = False
            return True


if __name__ == "__main__":
    com_info_list = SerialCommon.get_os_serial_port_info()
    ser = SerialCommon(com_info_list[0])
    print ser.open_connection()
    print ser.send_data("GVER\r\n")
    print ser.recv_data(1)
    ser.close_connection()
