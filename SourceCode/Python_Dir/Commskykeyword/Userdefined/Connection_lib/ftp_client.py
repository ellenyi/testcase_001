"""ftp client"""
import os 
import re
import logging
from ftplib import FTP

log = logging.getLogger("csrd.ftp")


class FtpClient(object):
    def __init__(self, host, port, username, password):

        self.ftp = FTP()
 
        try:
            self.ftp.connect(host, int(port))
            log.debug("ftp connect to ip='%s' port='%s' OK." % (host, port))
        except Exception, error:            
            raise Exception("ftp connect to ip='%s' port='%s' failed for '%s'." % \
                            (host, port, error))

        try:
            self.ftp.login(username, password)
            log.info("ftp login as username='%s' password='%s' OK."  % (username, password))
        except Exception, error:
            raise Exception("ftp login as username='%s' password='%s' failed for '%s'." \
                            % (username, password, error))

        log.info(self.ftp.getwelcome())

    def ftp_upload_single_file(self, local_file_dir, host_file_name, host_dir):
        try:
            self.ftp.cwd(host_dir)
            log.debug("ftp cd to dir '%s' OK." % host_dir)
        except Exception, error:
            raise Exception("ftp cd to dir '%s' dir failed for '%s'. " % (host_dir, error))

        bufsize = 10240

        try:
            file_handler = open(local_file_dir,'rb')
            log.debug("ftp open local file '%s' OK." % host_dir)
        except Exception, error:
            raise Exception("ftp open file '%s' failed for '%s.'" % (local_file_dir, error))

        ftp_cmd ='STOR ' + host_file_name
        try:
            self.ftp.storbinary(ftp_cmd, file_handler, bufsize)
            log.info("ftp upload '%s' to '%s/%s' OK." % \
                  (local_file_dir, host_dir, host_file_name))
        except Exception, error:
            raise Exception("ftp upload '%s' to '%s/%s' failed for '%s'." % \
                  (local_file_dir, host_dir, host_file_name, error))

        file_handler.close()

    def ftp_download_single_file(self, local_file_dir, host_file_name, host_dir):
        try:
            self.ftp.cwd(host_dir)
            log.debug("ftp cd to dir '%s' OK." % host_dir)
        except Exception, error:
            raise Exception("ftp cd to dir '%s' failed for '%s'." % (host_dir, error))

        bufsize = 10240

        try:
            file_handler = open(local_file_dir, 'wb').write
            log.debug("ftp open local file '%s' OK." % local_file_dir)
        except Exception, error:
            raise Exception("ftp open local file '%s' failed for '%s'." % (local_file_dir, error))

        ftp_cmd ='RETR ' + host_file_name
        try:
            self.ftp.retrbinary(ftp_cmd, file_handler, bufsize)
            log.info("ftp download '%s/%s' as '%s' OK." % \
                  (host_dir, host_file_name, local_file_dir))
        except Exception, error:
            raise Exception("ftp download '%s/%s' as '%s' failed for '%s'." % \
                  (host_dir, host_file_name, local_file_dir, error))


    def get_dirs_files(self):
        dir_res = []
        self.ftp.dir('.' , dir_res.append)
        files = [f.split(None, 8)[-1] for f in dir_res if f.startswith('-')]
        dirs = [f.split(None, 8)[-1] for f in dir_res if f.startswith('d')]
        dirs = [x for x in dirs if x not in ['.', '..']]
        return files, dirs

    def walk(self, next_dir, filter_flag, walk_flag):
        try:
            self.ftp.cwd(next_dir)
            log.debug('ftp walking to ' + next_dir)
        except Exception, error: 
            raise Exception("ftp cd to dir '%s' failed for '%s'." % (next_dir, error))
        ftp_curr_dir = self.ftp.pwd()

        files, dirs = self.get_dirs_files()
        if (0 < len(files)) and (0 < walk_flag):
            try:
                os.mkdir(next_dir.strip('/'))
            except OSError:
                pass
            os.chdir(next_dir.strip('/'))
        local_curr_dir = os.getcwd()

        new_files = []
        if "ALL" == filter_flag:
            pass
        else:
            for one_file in files:
                if re.search(filter_flag, one_file):
                    new_files.append(one_file)
            files = new_files

        for one_file in files:
            log.debug("next dir is '%s:%s'" % (next_dir, one_file))
            outf = open(one_file, 'wb')
            try:
                self.ftp.retrbinary('RETR %s' % one_file, outf.write)
            finally:
                outf.close()
        walk_flag += 1
        for one_dir in dirs:
            os.chdir(local_curr_dir)
            self.ftp.cwd(ftp_curr_dir)
            self.walk(one_dir, filter_flag, walk_flag)

    def ftp_download_all_file(self, local_file_dir, host_file_name, host_dir):

        if os.path.isdir(local_file_dir):
            log.debug("Dir %s has existed" % (local_file_dir))
        else:
            try:
                os.makedirs(local_file_dir)
            except Exception, error:
                raise Exception("Create directory '%s' failed for '%s'!" % (local_file_dir, error))

        os.chdir(local_file_dir) #set current folder as local_file_dir
        walk_flag  = 0
        self.walk(host_dir, host_file_name, walk_flag)


    def ftp_quit(self):
        self.ftp.quit()


def ftp_upload(host, port, username, password, local_file_dir, host_file_name, host_dir):
    """This keyword use ftp upload file to ftp server.

    | Input Parameters | Man. | Description |
    | host             | Yes  | host ip address |
    | port             | Yes  | ftp port |
    | username         | Yes  | ftp login username |
    | password         | Yes  | ftp login password |
    | local_file_dir   | Yes  | upload source file full path |
    | host_file_name   | Yes  | host file name  |
    | host_dir         | Yes  | ftp host file dir |

    Example
    | FTP Upload | 192.168.255.1 | 21 | test | test | d:\\test.dat | test.dat | temp |
    """
    cftp = FtpClient(host, port, username, password)
    try:
        cftp.ftp_upload_single_file(local_file_dir, host_file_name, host_dir)
    finally:
        cftp.ftp_quit()


def ftp_download(host, port, username, password, local_file_dir, host_file_name, host_dir):
    """This keyword use ftp download file to host PC.

    | Input Parameters | Man. | Description |
    | host             | Yes  | host ip address |
    | port             | Yes  | ftp port |
    | username         | Yes  | ftp login username |
    | password         | Yes  | ftp login password |
    | local_file_dir   | Yes  | local file or folder full path |
    | host_file_name   | Yes  | download file name or "ALL"  |
    | host_dir         | Yes  | ftp host file dir |

    Example
    | FTP Download | 192.168.255.1 | 21 | test | test | d:\\test.dat | test.dat | temp |
    | FTP Download | 192.168.255.1 | 21 | test | test | d:\\test | "ALL" | temp |
    | FTP Download | 192.168.254.129 | 21 | root | None | d:\\test | "F01.*" | /ram |

    """
    cftp = FtpClient(host, port, username, password)
    try:
        if ("ALL" == host_file_name) or (0 <= host_file_name.find('*')):
            cftp.ftp_download_all_file(local_file_dir, host_file_name, host_dir)
        else:
            cftp.ftp_download_single_file(local_file_dir, host_file_name, host_dir)
    finally: 
        cftp.ftp_quit()

