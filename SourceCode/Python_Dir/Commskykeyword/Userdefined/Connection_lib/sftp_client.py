import os
import re
import logging
import paramiko
from optparse import OptionParser

log = logging.getLogger("csrd.sftp")

class Sftp(object):
    def __init__(self, host, port, username, password):
        self.host = host
        self.port = port
        self.username = username
        self.password = password

        try:
            self.transport = paramiko.Transport((host, int(port)))
            log.debug("transport is ok, host:'%s', port:'%s'" % (host, port))
        except Exception, error:
            raise Exception("sftp failed, host:'%s', port:'%s', reason:'%s'" % \
                            (host, port, error))
        try:
            self.transport.connect(username=username, password=password)
            #'str' object has no attribute 'get_name' if use username, password directly
            self.sftp = paramiko.SFTPClient.from_transport(self.transport)
            log.info("sftp connect to '%s', username:'%s', password:'%s' is ok" \
                  % (host, username, password))
        except Exception, error:
            raise Exception("sftp connect to '%s' as'%s'/'%s' failed for '%s'." \
                            % (host, username, password, error))

    def get_size(self, host_file_path):
        if self.is_file(host_file_path):
            size = self.sftp.lstat(host_file_path).st_size/1000
            log.debug("sftp get file size '%s' is %sKB" % (host_file_path, size))
            return size
        else:
            log.debug("sftp get file size '%s' is wrong: not a file or not exist" % (host_file_path))
            return None

    def upload_file(self, local_file, target_file):
        try:
            self.sftp.put(local_file, target_file)
            log.info("sftp upload from '%s' to '%s' is ok." % \
                  (local_file, target_file))
            self.get_size(target_file)

        except Exception, error:
            raise Exception("sftp upload from '%s' to '%s' is failed, reason:'%s'." % \
                  (local_file, target_file, error))

    def download_file_once(self, local_file, target_file):
        self.get_size(target_file)
        self.sftp.get(target_file, local_file)
        local_file_size = os.path.getsize(local_file)
        if int(local_file_size) == 0:
            self.sftp.get(target_file, local_file)
            log.debug("local file size is zero, try again")

        log.info("sftp download from '%s' to '%s' is ok. local file size is %sk" % \
                  (target_file, local_file, int(local_file_size)/1000))
        return local_file
                  
    def download_file(self, local_file, target_file):
        try:
            self.download_file_once(local_file, target_file)
        except Exception, error:
            log.info("download failed for: '%s'" % error)
            ret = os.popen("ping %s" % self.host).read()
            log.info(ret)
            try:
                self.download_file_once(local_file, target_file)
            except Exception, error:
                raise Exception("sftp download from '%s' to '%s' is failed for '%s'." % \
                                 (target_file, local_file, error))
                
    def download_latest_file(self, local_file, target_dir, filefilter):
        try:
            self.sftp.chdir(target_dir)
            log.debug('sftp walking to %s' % (target_dir))
        except Exception, error:
            raise Exception("sftp cd to dir '%s' failed, details: '%s'" % (target_dir, error))
        sftp_curr_dir = self.sftp.getcwd()
        
        _mtime = lambda filename: self.sftp.stat("%s/%s" % (sftp_curr_dir, filename)).st_mtime
        statfiles = list(sorted([filename for filename in self.listdir(sftp_curr_dir) if 
                                 re.search(filefilter, filename)], key=_mtime, reverse=False))        
        target_file = "%s/%s" % (sftp_curr_dir, statfiles[-1])
        try:
            return self.download_file_once(local_file, target_file)
        except Exception, error:
            log.info("download failed for: '%s'" % error)
            ret = os.popen("ping %s" % self.host).read()
            log.info(ret)
            try:
                return self.download_file_once(local_file, target_file)
            except Exception, error:
                raise Exception("sftp download from '%s' to '%s' is failed for '%s'." % \
                                 (target_file, local_file, error))                          

    def download_files_in_time_period(self, 
                                      starttime, 
                                      endtime, 
                                      local_dir,
                                      target_dir, 
                                      filefilter):
        try:
            self.sftp.chdir(target_dir)
            log.debug('sftp walking to %s' % (target_dir))
        except Exception, error:
            raise Exception("sftp cd to dir '%s' failed, details: '%s'" % (target_dir, error))
        sftp_curr_dir = self.sftp.getcwd()
        _mtime = lambda filename: self.sftp.stat("%s/%s" % (sftp_curr_dir, filename)).st_mtime
        files = []
        from RobotWS.CommonLib.misc_lib import date_to_second
        starttime = date_to_second(starttime)
        endtime = date_to_second(endtime)
        for filename in self.listdir(sftp_curr_dir):
            if re.search(filefilter, filename):
                if starttime <= _mtime(filename) <= endtime:
                    files.append(filename)
        download_error = False
        local_files = []
        for filename in files:
            target_file = "%s/%s" % (sftp_curr_dir, filename)
            local_file = os.path.join(local_dir, filename)
            local_files.append(local_file)
            try:
                self.download_file(local_file, target_file)
            except Exception, error:
                print error
                download_error = True
        if download_error:
            raise Exception("download failed !")
        return local_files
                        
    def close(self):
        try:
            self.sftp.close()
            self.transport.close()
            log.debug("sftp close is ok")
        except Exception, error:
            raise Exception("sftp close is failed for '%s'" % error)

    def listdir(self, path='.'):
        return self.sftp.listdir(path)

    def is_file(self, path='.'):
        log.info(path)
        ret = self.sftp.lstat(path)
        if str(ret.__str__()).startswith('-'):
            return True
        else:
            return False

    def is_dir(self, path='.'):
        log.info(path)
        ret = self.sftp.lstat(path)
        if str(ret.__str__()).startswith('d'):
            return True
        else:
            return False

    def rename(self, old_path, new_path):
        return self.sftp.rename(old_path, new_path)

    def remove(self, path):
        return self.sftp.remove(path)

    def __search_advanced(self, target_dir, local_dir, file_filter="", if_deep_walk=True):
        """
        search all files with filter into local dir, no dir tree will keep
        Input Parameters:
        [1] target_dir: dir on ssh server
        [2] local_dir: local dir where will store searched files
        [3] file_filter: regular expression about file name, such as ".*.xml", "\\d+_\\d+.log"
        [4] if_deep_walk: if search in sub directory

        Output Parameters:
        [1] result
        """
        # change to target dir
        try:
            self.sftp.chdir(target_dir)
            log.debug('sftp walking to %s' % (target_dir))
        except Exception, error:
            raise Exception("sftp cd to dir '%s' failed for '%s'." % (target_dir, error))
        sftp_curr_dir = self.sftp.getcwd()

        # make local dir
        if not os.path.isdir(local_dir):
            DirCommon.create_dir(local_dir)

        # walk process
        list_folder = self.listdir(sftp_curr_dir)

        for item in list_folder:
            item_path = '%s/%s' % (sftp_curr_dir, item)
            if self.is_file(item_path):
                log.debug("%s is a flie" % item_path)
                local_path = os.path.join(local_dir, item)
                if file_filter != "":
                    if re.search(file_filter, item):
                        self.download_file(local_path, item_path)
                else:
                    self.download_file(local_path, item_path)

            elif self.is_dir(item_path):
                log.debug("%s is a dir" % item_path)
                if if_deep_walk:
                    self.__search_advanced(item_path, local_dir, file_filter, if_deep_walk)
                else:
                    log.debug("No deep mode, jump sub dir %s" % item_path)

            else:
                log.info("Error happens when check %s!" % item_path)

        return True

    def __download_advanced(self, target_dir, local_dir, if_deep_walk=True, file_filter=""):
        # change to target dir
        try:
            self.sftp.chdir(target_dir)
            log.debug('sftp walking to %s' % (target_dir))
        except Exception, error:
            raise Exception("sftp cd to dir '%s' failed for '%s'" % (target_dir, error))
        sftp_curr_dir = self.sftp.getcwd()

        # make local dir
        if not os.path.isdir(local_dir):
            DirCommon.create_dir(local_dir)
            

        # walk process
        list_folder = self.listdir(sftp_curr_dir)

        for item in list_folder:
            item_path = '%s/%s' % (sftp_curr_dir, item)
            if self.is_file(item_path):
                log.info("%s is a flie" % item_path)
                local_path = os.path.join(local_dir, item)
                if file_filter != "":
                    if re.search(file_filter, item):
                        self.download_file(local_path, item_path)
                else:
                    self.download_file(local_path, item_path)

            elif self.is_dir(item_path):
                log.info("%s is a dir" % item_path)
                if if_deep_walk:
                    local_sub_dir = os.path.join(local_dir, item)
                    self.__download_advanced(item_path, local_sub_dir, if_deep_walk, file_filter)
                else:
                    log.debug("No deep mode, jump sub dir %s" % item_path)
            else:
                log.info("Error happens when check %s!" % item_path)

        return True


    def download_dir(self, target_dir, local_dir, file_filter = ""):
        return self.__download_advanced(target_dir, local_dir, False, file_filter)

    def download_dir_deep(self, target_dir, local_dir, file_filter = ""):
        return self.__download_advanced(target_dir, local_dir, True, file_filter)

    def search_dir(self, target_dir, local_dir, file_filter):
        return self.__search_advanced(target_dir, local_dir, file_filter, False)

    def search_dir_deep(self, target_dir, local_dir, file_filter):
        return self.__search_advanced(target_dir, local_dir, file_filter, True)

def sftp_download(host, port, username, password, local_file_dir, host_file_name, host_dir):
    """This keyword use sftp download file from BTS to BTS control PC. 
       Telnet connection is not needed.

    | Input Parameters | Man. | Description |
    | host             | Yes  | host ip address |
    | port             | Yes  | sftp port |
    | username         | Yes  | sftp login username |
    | password         | Yes  | sftp login password |
    | local_file_dir   | Yes  | local file full path |
    | host_file_name   | Yes  | download file name | dir download, set it as  "ALL" |
    | host_dir         | Yes  | sftp host file dir |

    Example
    | SFTP Download | 192.168.255.1 | 22 | test | test | d:\\temp | .* | /tmp | download whole tmp dir |
    | SFTP Download | 192.168.255.1 | 22 | test | test | d:\\temp | .*.txt | /tmp | download all .txt file |
    | SFTP Download | 192.168.255.1 | 22 | test | test | d:\\test.bat | test.bat | /tmp | download test.bat file |
    | SFTP Download | 192.168.255.1 | 22 | test | test | d:\\new.bat | test.bat | /tmp | download test.bat file and change name |


    """
    try:
        _sftp_download_once(host, 
                            port, 
                            username, 
                            password, 
                            local_file_dir, 
                            host_file_name, 
                            host_dir)
    except Exception, error:        
        log.info("sftp download failed for '%s'\nTry to sftp download again!" % error)
        _sftp_download_once(host, 
                            port, 
                            username, 
                            password, 
                            local_file_dir, 
                            host_file_name, 
                            host_dir)
        
    
    
def _sftp_download_once(host, port, username, password, local_file_dir, host_file_name, host_dir):    
    sftp = Sftp(host, port, username, password)
    try:
        if '.*' in host_file_name:
            sftp.download_dir(host_dir, local_file_dir, host_file_name)
        else:
            sftp.download_file(local_file_dir, '%s/%s' % (host_dir, host_file_name))
    finally:
        sftp.close()

def sftp_download_deep(host, port, username, password, local_file_dir, host_file_name, host_dir):
    """This keyword use sftp download file from BTS to BTS control PC. telnet connection is not needed.

    | Input Parameters | Man. | Description |
    | host             | Yes  | host ip address |
    | port             | Yes  | sftp port |
    | username         | Yes  | sftp login username |
    | password         | Yes  | sftp login password |
    | local_file_dir   | Yes  | local file full path |
    | host_file_name   | Yes  | download file name | if you want to download whole dir,set this parameter "ALL" |
    | host_dir         | Yes  | sftp host file dir |

    Example
    | SFTP Download | 192.168.255.1 | 22 | test | test | d:\\temp | .* | /tmp | download whole tmp dir |
    | SFTP Download | 192.168.255.1 | 22 | test | test | d:\\temp | .*.txt | /tmp | download all txt file |
    | SFTP Download | 192.168.255.1 | 22 | test | test | d:\\test.bat | test.bat | /tmp | download test.bat file |
    | SFTP Download | 192.168.255.1 | 22 | test | test | d:\\new.bat | test.bat | /tmp | download test.bat file and change name |


    """
    sftp = Sftp(host, port, username, password)
    try:
        sftp.download_dir_deep(host_dir, local_file_dir, host_file_name)
    finally:
        sftp.close()
        
def sftp_download_latest_file(host, port, username, password, local_file, host_dir, filefilter):
    """This keyword use sftp download file from BTS to BTS control PC. telnet connection is not needed.

    | Input Parameters | Man. | Description |
    | host             | Yes  | host ip address |
    | port             | Yes  | sftp port |
    | username         | Yes  | sftp login username |
    | password         | Yes  | sftp login password |
    | local_file   | Yes  | local file full path |    
    | host_dir         | Yes  | sftp host file dir |
    | filefilter       | Yes  | the filefilter regexp pattern |

    Example
    | SFTP Download | 10.69.71.98 | 22 | toor4nsn | oZPS0POrRieRtu | D:\\counter.gz | "PM.*gz" | /tmp |
    """
    sftp = Sftp(host, port, username, password)
    try:
        return sftp.download_latest_file(local_file, host_dir, filefilter)
    finally:
        sftp.close()

def sftp_download_files_in_time_period(host, 
                                       port, 
                                       username, 
                                       password, 
                                       starttime, 
                                       endtime, 
                                       local_dir, 
                                       host_dir, 
                                       filefilter):
    """This keyword use sftp download file from BTS to BTS control PC. telnet connection is not needed.

    | Input Parameters | Man. | Description |
    | host             | Yes  | host ip address |
    | port             | Yes  | sftp port |
    | username         | Yes  | sftp login username |
    | password         | Yes  | sftp login password |
    | starttime       | Yes  | the period of start time |
    | endtime        | Yes  | the period of end time |
    | local_dir         | Yes  | the path will download to |
    | host_dir         | Yes  | sftp host file dir |
    | filefilter       | Yes  | the filefilter regexp pattern |

    Example
    | SFTP Download | 10.69.71.98 | 22 | toor4nsn | oZPS0POrRieRtu | D:\\counter.gz | "PM.*gz" | /tmp |
    """
    sftp = Sftp(host, port, username, password)
    try:
        return sftp.download_files_in_time_period(starttime, 
                                                  endtime,
                                                  local_dir, 
                                                  host_dir, 
                                                  filefilter)
    finally:
        sftp.close()

def sftp_upload(host,
                port,
                username,
                password,
                local_file, 
                host_file_name, 
                host_dir):
    """This keyword use sftp upload file from BTS control PC to BTS. telnet connection is not needed.

    | Input Parameters | Man. | Description |
    | host             | Yes  | host ip address |
    | port             | Yes  | sftp port |
    | username         | Yes  | sftp login username |
    | password         | Yes  | sftp login password |
    | local_file_dir   | Yes  | upload source file full path |
    | host_file_name   | Yes  | host file name  |
    | host_dir         | Yes  | sftp host file dir |

    Example
    | SFTP Upload | 192.168.255.1 | 22 | test | test | d:\\test.dat | test.dat | temp |
    """
    sftp = Sftp(host, port, username, password)
    try:
        sftp.upload_file(local_file, host_dir+'/'+host_file_name)
    finally:
        sftp.close()

if __name__ == '__main__': 
    pass

