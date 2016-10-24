#/usr/bin/env python
#-*- encoding:utf-8 -*-

import telnetlib
import re
import time

HOST = '172.20.99.45'
user = 'admin'
password = 'admin'
finish = "CST-AP035150#"

tn = telnetlib.Telnet(HOST,23)
#tn.set_debuglevel(2) #开启调试模式

'''
tn.expect([re.compile(b"login:"),]) #用正则表达式匹配username
tn.write(user + "\n") #匹配成功，输入user
tn.expect([re.compile(b"Password:"),]) #同上
tn.write(password + "\n") #同上
time.sleep(.1)
'''

#输入用户名
tn.read_until("login:")
tn.write(user + "\n")
print "hi login"
#输入密码
tn.read_until("Password:")
tn.write(password + "\n")
print "hi password"

#进入鉴权模式
tn.read_until("CST-AP035150>") #如果读到CST-AP035150#提示符，执行下面命令
tn.write("enable\n") #输入命令
print "finish enable"
tn.read_until("Password:") #同上
tn.write(password + "\n")
time.sleep(5)
print "finish login"
#print tn.read_very_eager()
#tn.write("quit\n")
#print tn.read_all()

tn.read_until(finish)
tn.close() #关闭连接
