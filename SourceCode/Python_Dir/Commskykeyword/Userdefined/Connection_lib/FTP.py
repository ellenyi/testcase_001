'''
Created on 2015.4.16
This modue is in order to supply FTP connection 

@author: Administrator
'''

import ftplib  
import os  
import socket
import time



def Get_Local_IP():
    
    localIP = socket.gethostbyname(socket.gethostname())
    print "local ip:%s "%localIP

    ipList = socket.gethostbyname_ex(socket.gethostname())
    for i in ipList:
        if i != localIP:
            print "external IP:%s"%i 
    return localIP


def Get_File_From_Ftpserver(HOST,FILE,FTPPATH,LOCALPATH):
    
    try:  
        f = ftplib.FTP(HOST)  
    except (socket.error, socket.gaierror):  
        print 'ERROR:cannot reach " %s"' % HOST  
        return  
    print '***Connected to host "%s"' % HOST  
  
    try:  
        f.login()  
    except ftplib.error_perm:  
        print 'ERROR: cannot login anonymously'  
        f.quit()  
        return  
    print '*** Logged in as "anonymously"'  
    try:
        DIRN=FTPPATH
        print DIRN
        f.cwd(DIRN)  
    except ftplib.error_perm:  
        print 'ERRORL cannot CD to "%s"' % DIRN  
        f.quit()  
        return  
    print '*** Changed to "%s" folder' % DIRN  
    try:  
   
        PATH=LOCALPATH+'/'+FILE    
        t=open(PATH, 'wb')
             
        f.retrbinary('RETR %s' % FILE,t.write)

        
    except ftplib.error_perm:  
        print 'ERROR: cannot read file "%s"' % FILE  
        os.unlink(PATH)  
    else:  
        print '*** Downloaded "%s" to lOCAL' % FILE  
    f.quit() 
    t.close() 
    return  

def ftpconnect(host):
    username = 'admin'  
    password = 'commsky' 
    ftp=ftplib.FTP()  
    ftp.set_debuglevel(2)
    ftp.connect(host,21) 
    ftp.login(username,password) 
    return ftp         
       

def Download_File_By_FTP(host,remotepath,localpath):  
    start=time.time()
    ftp = ftpconnect(host)  
    print ftp.getwelcome()
    bufsize = 1024
    fp = open(localpath,'wb')
    ftp.retrbinary('RETR ' + remotepath,fp.write,bufsize)
    ftp.set_debuglevel(0)
    fp.close()  
    ftp.quit() 
    end=time.time()
    gap=abs(start-end)
    filezie=os.path.getsize(localpath)/1024
    print gap
    speed=float(filezie)/gap  
    return speed
       
def Upload_File_By_FTP(host,remotepath,localpath,filezie):  
    start=time.time()
    ftp = ftpconnect(host)  
    print ftp.getwelcome()
    bufsize = 1024
    fp = open(localpath,'rb')
    cmd='STOR '+remotepath
    ftp.storbinary(cmd, fp, bufsize)
    ftp.set_debuglevel(0)
    fp.close()  
    ftp.quit()
    end=time.time()
    gap=abs(start-end)
    print gap
    speed=float(filezie)/gap  
    return speed
    
if __name__ == '__main__':
    Get_Local_IP()
    
    print "ok"
    pass