'''
Created on 2015.4.16

@author: Administrator
'''



import sys
import codecs
import os
import string
import re
import csv
import subprocess
import time
import shutil

def Get_WeekDay():
    weekday=time.localtime().tm_wday
    return weekday

def Move_File_To_Target(filepath,targetpath):
    shutil.move(filepath, targetpath)
    print "move %s to %s successful" %(filepath,targetpath)
    
def Get_Line_And_Replace(file,substrline,newstr):
    
    _list_content = [];

    fh = codecs.open(file,encoding='utf-8', mode='r')
    print fh
    for i in fh.readlines():

        _list_content.append(i)
    
    fh.close()
    
    print _list_content
    
    length=len(_list_content)
    print length
    i=0
    while (i<length):

        if _list_content[i].find(substrline)!=-1:

            _list_content[i]=substrline + newstr + '\r\n'
            print _list_content[i] 
            i=i+1

        else:
            i=i+1

    print _list_content
        
    codecs.open(file, 'wb',encoding='utf-8').writelines(_list_content)
    
    
def Kill_Process(exename):
    
    command='taskkill /f /im '+exename
    print command
    os.system(command)
    
def Check_Exist_Process():
    command='tasklist'
    output=os.system(command)
    print output
    
def Excute_Windows_Cmd(cmd):
    print cmd 
    subprocess.Popen("cmd.exe /C "+cmd ,shell=True)
    print "start...."
    
def Compare_Version_And_Get_Latest(version0,version1):

    list_version0=list(version0)
    list_version1=list(version1)
    Vversion0=''.join(list_version0[1:4])
    Vversion1=''.join(list_version1[1:4])
    Rversion0=int(''.join(list_version0[5:8]))
    Rversion1=int(''.join(list_version1[5:8]))
    Dversion0=int(''.join(list_version0[9:12]))
    Dversion1=int(''.join(list_version1[9:12]))
    if list_version0[0]==list_version1[0] and list_version0[4]==list_version1[4] and list_version0[8]==list_version1[8]:
        print 'version format is correct'
        if Vversion0==Vversion1:
            print 'Vversion is same'           
            if Rversion0==Rversion1:
                print 'R version is same'
                if Dversion0==Dversion1:
                    print "your current version is newest, not need to upgrade"
                    upgrade='False'
                    return upgrade
                elif Dversion0>Dversion1:
                    print "your current version is newest, not need to upgrade"
                    upgrade='False'
                    return upgrade
                else:
                    print "you need upgrade to newer version %s" %version1
                    upgrade='True'
                    return upgrade    
                    
            elif Rversion0>Rversion1:
                print "your current version is newest, not need to upgrade"
                upgrade='False'
                return upgrade
            else:
                print "you need upgrade to newer version %s" %version1
                upgrade='True'
                return upgrade 

        else:
            erroinfo='check your V version '
            return erroinfo
        
    else:
        erroinfo= 'please check yaur input version...'
        return erroinfo
        


def Get_Infor_Start_End(input,start,end):

    index = input.find(start)
    if (index==-1):
        raise AssertionError("can't find start informaiton: '%s'. in output message" % start)
    
    input=input[index:]
    
    index_end = input.find(end)
    if (index_end==-1):
        raise AssertionError("can't find end informaiton: '%s'. in output message" % end)
    
    output = input[:index_end+1]
    
    return output
 
def Get_Infor_Start_To_End(input,start,end1,end2):

    index = input.find(start)
    if (index==-1):
        raise AssertionError("can't find start informaiton: '%s'. in output message" % start)
    
    input=input[index:]
    
    index_end = input.find(end1)
    if (index_end==-1):
        index_end2=input.find(end2)
        if (index_end2==-1):
            raise AssertionError("can't find end informaiton: '%s'. in output message" % end)
        else:
            index_end=index_end2
   
    output = input[:index_end+1]
    
    return output

def Get_Infor_Start(input,start):

    index = input.find(start)
    if (index==-1):
        raise AssertionError("can't find start informaiton: '%s'. in output message" % start)
    
    output=input[index:]        
    return output   
    
def Delete_Redundant_Space(str1):
    
    print isinstance(str1, unicode)
    str1=str1.encode('utf8')
    str1=re.sub(' +', ' ', str1)    
    return str1
 
def Delete_Str_End_Space(str1):
     
     str1=str1.rstrip(' ')
     return str1

def Delete_Zero_Head(str1):
    
    str1=str1.lstrip('0')
    return str1
    
def Delete_Prencent_Tail(str1):
    
    str1=str1.rstrip('%')
    return str1 

def Get_Info_CSV_File(file): 
    f=open(file, 'r')
    info=f.readlines()
    strinfo=''
    for c in info:
        strinfo=strinfo+c
        
    return strinfo
        
def Get_File_To_List(file):
    _list_content = [];

    fh = codecs.open(file,encoding='utf-8', mode='r')
    for i in fh.readlines():

        _list_content.append(i)
    
    fh.close()
    
    print _list_content
    newoutput=''.join(_list_content)
    return newoutput

def Delete_Repeat_String(str):
    
    print str
    patterns = ""
    for line in str.split("\n"):
        if line not in patterns:
            print "ooo"
            print line
            patterns=''.join(line + "\n")
 
    return patterns

def Delete_File(dir,filename,topdown=True):  
    for root, dirs, files in os.walk(dir, topdown):  

        for name in files:              
            pathname = os.path.splitext(os.path.join(root, name))  
            path=pathname[0]+pathname[1]
            print path
            filepath=dir+'\\'+filename
            if (path == filepath):  

                os.remove(os.path.join(root, name))  
                print(os.path.join(root,name)) 

                                           
if __name__ == '__main__':
    Kill_Process('3CDaemon.EXE')
 
    print "end"
    pass