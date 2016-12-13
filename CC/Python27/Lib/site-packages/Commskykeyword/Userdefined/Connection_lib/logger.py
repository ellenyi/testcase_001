"""Common logging module 
Usage:
    in main thread first run config_logging method
    then use logging.getLogger("counter.xxx") to get a logger"""

import logging
import os
import sys

class Logger:
    LOGGINGLEVELS = {"NOTSET" : logging.NOTSET,
                     "DEBUG" : logging.DEBUG, 
                     "INFO" : logging.INFO, 
                     "WARN" : logging.WARN, 
                     "ERROR" : logging.ERROR, 
                     "FATAL" : logging.FATAL,
                     "CRITICAL" : logging.CRITICAL}    
    def __init__(self):
        self.streamformat = '%(name)s/%(module)s/%(levelname)s: %(message)s'
        self.fileformat = "%(asctime)s %(name)s/%(module)s(%(lineno)d), %(levelname)s: %(message)s"
        self.logtag = None
        self.stream_loglevel = None
        self.file_loglevel = None
        self.filemode = None
        self.max_filesize = None
        self.max_filenum = None
        
    def config_logging(self, 
                       logtag="log", 
                       stream_loglevel=None,
                       file_loglevel=None, 
                       filename="log.log", 
                       filemode="w",
                       max_filesize=1024*1024*30,
                       max_filenum=100):
        
        self.logtag = logtag
        self.stream_loglevel = self._check_level(stream_loglevel)
        self.file_loglevel = self._check_level(file_loglevel)
        self.filename = filename
        log_path = os.path.dirname(self.filename)
        if log_path:
            if not os.path.exists(log_path):
                os.mkdir(log_path)
        self.filemode = filemode
        self.max_filesize = max_filesize
        self.max_filenum = max_filenum
                
        self.logger = logging.getLogger(self.logtag)
        self.logger.setLevel(logging.DEBUG)  #???

        if self.file_loglevel is None and self.stream_loglevel is None:
            return True
        if self.file_loglevel and self.stream_loglevel:
            #===================================================================
            # logging.basicConfig(format=self.streamformat,
            #                     level=self.stream_loglevel,
            #                     )          
            #===================================================================
            self._config_streamhandler()
            self._config_filehandler()
            return True
        if self.file_loglevel is None and self.stream_loglevel is not None:
            #===================================================================
            # logging.basicConfig(format=self.streamformat,
            #                     level=self.stream_loglevel,
            #                     )                               
            #===================================================================
            self._config_streamhandler()
            return True
        if file_loglevel is not None and stream_loglevel is None:           
            self._config_filehandler()
            return True
        return False

    def _config_filehandler(self):
        from logging.handlers import RotatingFileHandler
        filehandler = RotatingFileHandler(filename=self.filename,
                                          mode=self.filemode,
                                          maxBytes=self.max_filesize,
                                          backupCount=self.max_filenum)
        filehandler.setLevel(self.file_loglevel)
        filehandler_formatter = logging.Formatter(self.fileformat)
        filehandler.setFormatter(filehandler_formatter)        
        self.logger.addHandler(filehandler)
        
    def _config_streamhandler(self):
        streamhandler = logging.StreamHandler(sys.stdout)
        streamhandler.setLevel(self.stream_loglevel)
        streamhandler_formatter = logging.Formatter(self.streamformat)
        streamhandler.setFormatter(streamhandler_formatter)
        self.logger.addHandler(streamhandler)        
        
    def get_logger(self, logtag=""):
        return logging.getLogger(logtag)
    
    def _check_level(self, level):
        if level is None:
            return level
        try:
            level = str(level)
            if level not in Logger.LOGGINGLEVELS:
                raise ValueError("Unknown level: %r" % level)
            tlevel = Logger.LOGGINGLEVELS[level]
        except Exception, e:
            print "ERROR: ", repr(e)
            raise TypeError("Please input a valid log level: %r" % level)
        return tlevel

    
if __name__ == "__main__":
    log = Logger()
    log.config_logging(logtag="counter", 
                       stream_loglevel="INFO", 
                       file_loglevel="DEBUG", 
                       filename="counter.log", 
                       filemode="w", 
                       max_filesize=1024*1024*10, 
                       max_filenum=10
                       )
    logger = logging.getLogger("counter.main")
     
    #for i in range(1024):
     #   logger.info("test...")
    logger.info("test")

    logger.debug('This is debug message')
    logger.info('This is info message')
    logger.warning('This is warning message')

    

