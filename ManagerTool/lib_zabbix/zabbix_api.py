#!/usr/bin/python 
#coding:utf-8 
 
import json 
import urllib2 
from urllib2 import URLError 
import ConfigParser
import sys,argparse
import os
from colorclass import Color
from terminaltables import SingleTable
import my_sort
import time
import my_compare
import XLSWriter
#{{{logging
import logging 
logging.basicConfig(level=logging.DEBUG,
		format='%(asctime)s%(filename)s[line:%(lineno)d] %(levelname)s%(message)s',
		datefmt='%a,%d %b %Y %H:%M:%S',
		filename='/tmp/zabbix.log',
		filemode='a')


#logging.debug('debug message')
#logging.info('info message')
#logging.warning('warning message')
#logging.error('error message')
#logging.critical('critical message')
#}}}
#{{{msg
def err_msg(msg):
    print "\033[41;37m[Error]: %s \033[0m"%msg
    exit()

  
def info_msg(msg):
    print "\033[42;37m[Info]: %s \033[0m"%msg

  
def warn_msg(msg):
    print "\033[43;37m[Warning]: %s \033[0m"%msg

#}}}
class zabbix_api: 
    def __init__(self,terminal_table): 
        if os.path.exists("zabbix_config.ini"):
            config = ConfigParser.ConfigParser()
            config.read("zabbix_config.ini")
            self.server = config.get("zabbixserver", "server")
            self.port = config.get("zabbixserver", "port")
            self.user = config.get("zabbixserver", "user")
            self.password = config.get("zabbixserver", "password")
        else:
            print "the config file is not exist"
            exit(1)

        self.url = 'http://%s:%s/api_jsonrpc.php' % (self.server,self.port) #修改URL
        self.header = {"Content-Type":"application/json"}
        self.terminal_table=terminal_table
        self.authID = self.user_login() 

    #{{{user_login
    def user_login(self): 
        data = json.dumps({
                           "jsonrpc": "2.0",
                           "method": "user.login",
                           "params": { 
                                      "user": self.user, #修改用户名
                                      "password": self.password #修改密码
                                      },
                           "id": 0 
                           })
         
        request = urllib2.Request(self.url, data) 
        for key in self.header: 
            request.add_header(key, self.header[key]) 
     
        try: 
            result = urllib2.urlopen(request) 
        except URLError as e: 
            print "\033[041m 用户认证失败，请检查 !\033[0m", e
            exit(1)
        else: 
            response = json.loads(result.read()) 
            result.close() 
            self.authID = response['result'] 
            return self.authID 
         
    #}}}
    # host
    #{{{host_get
    ##
    # @brief host_get 
    #
    # @param hostName
    #
    # @return 
    def host_get(self,hostName=''): 
        data=json.dumps({
                "jsonrpc": "2.0",
                "method": "host.get",
                "params": {
                          "output": "extend",
                          "filter":{"host":hostName} 
                          },
                "auth": self.user_login(),
                "id": 1
                })
        request = urllib2.Request(self.url,data) 
        for key in self.header: 
            request.add_header(key, self.header[key]) 
        try: 
            result = urllib2.urlopen(request) 
        except URLError as e: 
            if hasattr(e, 'reason'): 
                print 'We failed to reach a server.' 
                print 'Reason: ', e.reason 
            elif hasattr(e, 'code'): 
                print 'The server could not fulfill the request.' 
                print 'Error code: ', e.code 
        else: 
            response = json.loads(result.read()) 
            result.close() 
            print "主机数量: \033[31m%s\033[0m"%(len(response['result']))
            if self.terminal_table:
                table_show=[]
                table_show.append(["HostID","HostName","name","Status","Available"])
            else:
                print "HostID","HostName","name","Status","Available"

            if len(response['result']) == 0:
                return 0
            for host in response['result']:      
                status={"0":"OK","1":"Disabled"}
                available={"0":"Unknown","1":Color('{autobggreen}available{/autobggreen}'),"2":Color('{autobgred}Unavailable{/autobgred}')}
                if len(hostName)==0:
                    #print host
                    if self.terminal_table:
                        table_show.append([host['hostid'],host['host'],host['name'],status[host['status']],available[host['available']]])
                    else:
                        print host['hostid'],host['host'],host['name'],status[host['status']],available[host['available']]
                else:
                    print host['hostid'],host['host'],host['name'],status[host['status']],available[host['available']]
                    return host['hostid']
            if self.terminal_table:
                table=SingleTable(table_show)
                print(table.table)

    #}}}
    #{{{_host_get
    def _host_get(self): 
        host_list=[]
        data=json.dumps({
                "jsonrpc": "2.0",
                "method": "host.get",
                "params": {
                          "output": "extend",
                          },
                "auth": self.user_login(),
                "id": 1
                })
        request = urllib2.Request(self.url,data) 
        for key in self.header: 
            request.add_header(key, self.header[key]) 
        try: 
            result = urllib2.urlopen(request) 
        except URLError as e: 
            if hasattr(e, 'reason'): 
                print 'We failed to reach a server.' 
                print 'Reason: ', e.reason 
            elif hasattr(e, 'code'): 
                print 'The server could not fulfill the request.' 
                print 'Error code: ', e.code 
        else: 
            response = json.loads(result.read()) 
            result.close() 
            if len(response['result']) == 0:
                return 0
            for host in response['result']:      
                host_list.append([host['hostid'],host['host'],host['name']])
            return host_list

    #}}}
    #{{{host_create
    def host_create(self, hostip,hostname,hostgroupName, templateName): 
        if self.host_get(hostname):
            print "\033[041m该主机已经添加!\033[0m" 
            sys.exit(1)

        group_list=[]
        template_list=[]
        for i in hostgroupName.split(','):
            var = {}
            var['groupid'] = self.hostgroup_get(i)
            group_list.append(var)
        for i in templateName.split(','):
            var={}
            var['templateid']=self.template_get(i)
            template_list.append(var)   

        data = json.dumps({ 
                           "jsonrpc":"2.0", 
                           "method":"host.create", 
                           "params":{ 
                                     "host": hostname, 
                                     "interfaces": [ 
                                     { 
                                     "type": 1, 
                                     "main": 1, 
                                     "useip": 1, 
                                     "ip": hostip, 
                                     "dns": "", 
                                     "port": "10050" 
                                      } 
                                     ], 
                                   "groups": group_list,
                                   "templates": template_list,
                                     }, 
                           "auth": self.user_login(), 
                           "id":1                   
        }) 
        request = urllib2.Request(self.url, data) 
        for key in self.header: 
            request.add_header(key, self.header[key]) 
              
        try: 
            result = urllib2.urlopen(request) 
        except URLError as e: 
            print "Error as ", e 
        else: 
            #print result.read()
            response = json.loads(result.read()) 
            result.close() 
            print "添加主机 : \033[42m%s\033[0m \tid :\033[31m%s\033[0m" % (hostip, response['result']['hostids']) 


    #}}}
    #{{{host_disable
    def host_disable(self,hostip):
        data=json.dumps({
        "jsonrpc": "2.0",
        "method": "host.update",
        "params": {
        "hostid": self.host_get(hostip),
        "status": 1
        },
        "auth": self.user_login(),
        "id": 1
        })
        request = urllib2.Request(self.url,data)
        for key in self.header:
            request.add_header(key, self.header[key])       
        try: 
            result = urllib2.urlopen(request)
        except URLError as e: 
            print "Error as ", e 
        else: 
            response = json.loads(result.read()) 
            result.close()
            print '----主机现在状态------------'
        print self.host_get(hostip)
                 
    #}}}
    #{{{host_delete
    def host_delete(self,hostid):
        hostid_list=[]
        #print type(hostid)
        for i in hostid.split(','):
            var = {}
            var['hostid'] = self.host_get(i)
            hostid_list.append(var)      
        print hostid_list
        data=json.dumps({
                "jsonrpc": "2.0",
                "method": "host.delete",
                "params": hostid_list,
                "auth": self.user_login(),
                "id": 1
                })
        print data
        request = urllib2.Request(self.url,data) 
        for key in self.header: 
            request.add_header(key, self.header[key]) 
             
        try: 
            result = urllib2.urlopen(request) 
        except Exception,e: 
            print  e
        else: 
            response = json.loads(result.read()) 
            #print response['result']
            print response

            result.close() 
            print "主机 \033[041m %s\033[0m  已经删除 !"%hostid 
    #}}}
    # hostgroup
    #{{{hostgroup_get
    def hostgroup_get(self, hostgroupName=''): 
        data = json.dumps({ 
                           "jsonrpc":"2.0", 
                           "method":"hostgroup.get", 
                           "params":{ 
                                     "output": "extend", 
                                     "filter": { 
                                                "name": hostgroupName 
                                                } 
                                     }, 
                           "auth":self.user_login(), 
                           "id":1, 
                           }) 
         
        request = urllib2.Request(self.url,data) 
        for key in self.header: 
            request.add_header(key, self.header[key]) 
              
        try: 
            result = urllib2.urlopen(request) 
        except URLError as e: 
            print "Error as ", e 
        else: 
            #print result.read()
            response = json.loads(result.read()) 
            result.close() 
            if len(response['result']) == 0:
                return 0
            for group in response['result']:
                if  len(hostgroupName)==0:
                    print "hostgroup:  \033[31m%s\033[0m \tgroupid : %s" %(group['name'],group['groupid'])
            else:
                print "hostgroup:  \033[31m%s\033[0m\tgroupid : %s" %(group['name'],group['groupid'])
                self.hostgroupID = group['groupid'] 
                return group['groupid'] 

    #}}}
    # item
    #{{{item_get
    ##
    # @brief item_get 
    #
    # @param host_ID
    # @param itemName
    #
    # @return list
    # list_format [item['itemid'],item['name'],item['key_']]

    def item_get(self, host_ID='',itemName=''): 
        if  len(host_ID)==0:
            print "ERR- host_ID is null"
            return 0

        table_show=[]
        data = json.dumps({ 
                           "jsonrpc":"2.0", 
                           "method":"item.get", 
                           "params":{ 
                                     "output":"extend",
                                     "hostids":host_ID,
                                     }, 
                           "auth":self.user_login(), 
                           "id":1, 
                           }) 
         
        #dd"filter":{"name":itemName} 
        request = urllib2.Request(self.url,data) 
        for key in self.header: 
            request.add_header(key, self.header[key]) 
              
        try: 
            result = urllib2.urlopen(request) 
        except URLError as e: 
            print "Error as ", e 
        else: 
            response = json.loads(result.read()) 
            result.close() 
            table_show.append(["itemid","name","key_"])
            if len(response['result']) == 0:
                return 0
            item_list=[]
            item_list[:]=[]
            for item in response['result']:
                #########################################
                # alt the $1 and $2 
                #########################################
                position = item['key_'].find('[')+1
                if position:
                    list_para = item['key_'][position:-1].split(",")
                    # 将$1,$2等置换为真正name
                    for para_a in range(len(list_para)):
                        para='$'+str(para_a+1)
                        item['name']=item['name'].replace(para,list_para[para_a])

                if  len(itemName)==0:
                    table_show.append([item['itemid'],item['name'],item['key_']])
                else:
                    if item['name']==itemName:
                        item_list.append([item['itemid'],item['name'],item['key_']])
                    else:
                        if my_compare.my_compare(item['name'],itemName):
                            item_list.append([item['itemid'],item['name'],item['key_']])
            
            if len(itemName) == 0:
                table=SingleTable(table_show)
                print(table.table)
            if len(item_list):
                return item_list
            else:
                return 0

    #}}}
    # history
    #{{{history_get
    def history_get(self,history='',item_ID='',time_from='',time_till=''): 
        history_data=[]
        history_data[:]=[]
              
        #print history,item_ID,time_from,time_till     
        data = json.dumps({ 
                           "jsonrpc":"2.0", 
                           "method":"history.get", 
                           "params":{ 
                                     "time_from":time_from,
                                     "time_till":time_till,
                                     "output": "extend",
                                     "history": history,
                                     "itemids": item_ID,
                                     "limit": 50000
                                     }, 
                           "auth":self.user_login(), 
                           "id":1, 
                           }) 
        request = urllib2.Request(self.url,data) 
        for key in self.header: 
            request.add_header(key, self.header[key]) 
        try: 
            result = urllib2.urlopen(request) 
        except URLError as e: 
            print "Error as ", e 
        else: 
            response = json.loads(result.read()) 
            result.close() 
            if len(response['result']) == 0:
                debug_info=str([history,item_ID,time_from,time_till,"####not have history_data"])
                logging.debug(debug_info)
                return 0.0,0.0,0.0
            for history_info in response['result']:
                history_data.append(history_info['value'])
            history_value=my_sort.Stats(history_data)
            history_min=history_value.min()
            #print history_min,type(history_min)
            history_max=history_value.max()
            #print history_max,type(history_max)
            history_avg=float('%0.4f'% history_value.avg())
            #print history_avg,type(history_avg)
            
            if history == '3':
                history_min = int(history_min)
                history_max = int(history_max)
                history_avg = int(history_avg)
            debug_info=str([history,item_ID,time_from,time_till,history_min,history_max,history_avg])
            logging.debug(debug_info)
            return (history_min,history_max,history_avg)

    #}}}
    #{{{history_report
    ##
    # @brief history_report 
    #
    # @param history
    # @param itemName
    # @param date_from
    # @param date_till
    # @param export_xls ["OFF","ceshi.xls"]
    #
    # @return 
    def history_report(self,history,itemName,date_from,date_till,export_xls): 
        #dateFormat = "%Y-%m-%d %H:%M:%S"
        dateFormat = "%Y-%m-%d"
        try:
            startTime =  time.strptime(date_from,dateFormat)
            endTime =  time.strptime(date_till,dateFormat)
            sheetName =  time.strftime('%Y%m%d',startTime) + "_TO_" +time.strftime('%Y%m%d',endTime)
            info_msg=str(sheetName)
            logging.info(info_msg)
        except:
            err_msg("时间格式 ['2016-05-01'] ['2016-06-01']")

        if export_xls[0] == 'ON':
            xlswriter = XLSWriter.XLSWriter(export_xls[2])
            xlswriter.add_image("python.bmg",0,0,sheet_name=sheetName)
            xlswriter.add_header(u"报告周期:"+sheetName,8,sheet_name=sheetName)
            xlswriter.setcol_width([10, 20, 20,10,20,10,10,10],sheet_name=sheetName)
            xlswriter.writerow(["hostid","hostname","name","itemid","itemName","min","max","avg"],sheet_name=sheetName,border=True,pattern=True)
        time_from = int(time.mktime(startTime))
        time_till = int(time.mktime(endTime))
        if time_from > time_till:
            err_msg("date_till must after the date_from time")

        if self.terminal_table:
            table_show=[]
            table_show.append(["hostid","hostname","name","itemid","itemName","min","max","avg"])
        else:
            print "hostid",'\t',"hostname",'\t',"name",'\t',"itemid",'\t',"itemName",'\t',"min",'\t',"max","avg"
        host_list = self._host_get()
        for host_info in host_list: 
            itemid_all_list = self.item_get(host_info[0],itemName)
            if itemid_all_list == 0:
                continue
            for itemid_sub_list in itemid_all_list:
                itemid=itemid_sub_list[0]
                item_name=itemid_sub_list[1]
                item_key=itemid_sub_list[2]
                debug_msg="itemid:%s"%itemid
                logging.debug(debug_msg)
                
                history_min,history_max,history_avg = self.history_get(history,itemid,time_from,time_till)
                history_min=str(history_min)
                history_max=str(history_max)
                history_avg=str(history_avg)
                itemid=str(itemid)
                if self.terminal_table:
                    table_show.append([host_info[0],host_info[1],host_info[2],itemid,item_name,history_min,history_max,history_avg])
                else:
                    print host_info[0],'\t',host_info[1],'\t',host_info[2],'\t',itemid,item_name,'\t',history_min,'\t',history_max,'\t',history_avg
                if export_xls[0] == "ON":
                    xlswriter.writerow([host_info[0],host_info[1],host_info[2],itemid,item_name,history_min,history_max,history_avg],sheet_name=sheetName,border=True)
        print
        if self.terminal_table:
            table=SingleTable(table_show)
            table.title = itemName
            print(table.table)
        if export_xls[0] == 'ON':
            xlswriter.save()
        return 0
 #}}}
    #{{{template_get
    def template_get(self,templateName=''): 
        data = json.dumps({ 
                           "jsonrpc":"2.0", 
                           "method": "template.get", 
                           "params": { 
                                      "output": "extend", 
                                      "filter": { 
                                                 "name":templateName                                                        
                                                 } 
                                      }, 
                           "auth":self.user_login(), 
                           "id":1, 
                           })
         
        request = urllib2.Request(self.url, data) 
        for key in self.header: 
            request.add_header(key, self.header[key]) 
              
        try: 
            result = urllib2.urlopen(request) 
        except URLError as e: 
            print "Error as ", e 
        else: 
            response = json.loads(result.read()) 
            if self.terminal_table:
                table_show=[]
                table_show.append(["template","id"])
            else:
                print "template","id"
            result.close() 
            #print response
            for template in response['result']:                
                if len(templateName)==0:
                    if self.terminal_table:
                        table_show.append([template['name'],template['templateid']])
                    else:
                        print "template : \033[31m%s\033[0m\t  id : %s" % (template['name'], template['templateid'])
                else:
                    self.templateID = response['result'][0]['templateid'] 
                    print "Template Name :  \033[31m%s\033[0m "%templateName
                    return response['result'][0]['templateid']
            if self.terminal_table:
                table=SingleTable(table_show)
                print(table.table)
    #}}}
    #{{{hostgroup_create
    def hostgroup_create(self,hostgroupName):

        if self.hostgroup_get(hostgroupName):
            print "hostgroup  \033[42m%s\033[0m is exist !"%hostgroupName
            sys.exit(1)
        data = json.dumps({
                          "jsonrpc": "2.0",
                          "method": "hostgroup.create",
                          "params": {
                          "name": hostgroupName
                          },
                          "auth": self.user_login(),
                          "id": 1
                          })
        request=urllib2.Request(self.url,data)

        for key in self.header: 
            request.add_header(key, self.header[key]) 
              
        try: 
            result = urllib2.urlopen(request)
        except URLError as e: 
            print "Error as ", e 
        else: 
            response = json.loads(result.read()) 
            result.close()
            print "\033[042m 添加主机组:%s\033[0m  hostgroupID : %s"%(hostgroupName,response['result']['groupids'])


    #}}}
    #{{{alert_get
    def alert_get(self):
        data=json.dumps({
                "jsonrpc": "2.0",
                "method": "alert.get",
                "params": {
                    "output":"extend",
                    "actionids":"3"
                },
                "auth": self.user_login(),
                "id": 1
                })
        print data
        request = urllib2.Request(self.url,data) 
        for key in self.header: 
            request.add_header(key, self.header[key]) 
             
        try: 
            result = urllib2.urlopen(request) 
        except Exception,e: 
            print  e
        else: 
            response = json.loads(result.read()) 
            #print response['result']
            print response
            result.close() 
    #}}}
    #{{{trend_get
    ##
    # @brief trend_get 
    #
    # @param itemID
    #
    # @return itemid
    def trend_get(self,itemID=''): 
        data = json.dumps({ 
                           "jsonrpc":"2.0", 
                           "method":"trend.get", 
                           "params":{ 
                               "output":[
                                   "itemid",
                                   "clock",
                                   "num",
                                   "value_min",
                                   "value_avg",
                                   "value_max"
                                        ],
                               "itemids":itemID,
                               "limit":"20"
                                     }, 

                           "auth":self.user_login(), 
                           "id":1, 
                           }) 
         
        request = urllib2.Request(self.url,data) 
        for key in self.header: 
            request.add_header(key, self.header[key]) 
              
        try: 
            result = urllib2.urlopen(request) 
        except URLError as e: 
            print "Error as ", e 
        else: 
            response = json.loads(result.read()) 
            result.close() 
            if len(response['result']) == 0:
                return 0
            for trend in response['result']:
                print trend 
    #}}}
    # user
    #{{{user_get
    ##
    # @brief user_get 
    #
    # @param userName
    #
    # @return 
    def user_get(self,userName=''): 
        data=json.dumps({
                "jsonrpc": "2.0",
                "method": "user.get",
                "params": {
                          "output": "extend",
                          },
                "auth": self.user_login(),
                "id": 1
                })
        request = urllib2.Request(self.url,data) 
        for key in self.header: 
            request.add_header(key, self.header[key]) 
        try: 
            result = urllib2.urlopen(request) 
        except URLError as e: 
            if hasattr(e, 'reason'): 
                print 'We failed to reach a server.' 
                print 'Reason: ', e.reason 
            elif hasattr(e, 'code'): 
                print 'The server could not fulfill the request.' 
                print 'Error code: ', e.code 
        else: 
            response = json.loads(result.read()) 
            result.close() 
            print "user sum: \033[31m%s\033[0m"%(len(response['result']))
            if self.terminal_table:
                table_show=[]
                table_show.append(["userid","alias","name","url"])
            else:
                print "userid","alias","name","url"

            if len(response['result']) == 0:
                return 0
            for user in response['result']:      
                if len(userName)==0:
                    if self.terminal_table:
                        table_show.append([user['userid'],user['name'],user['name'],user['url']])
                    else:
                        print user['userid'],user['name'],user['name'],user['url']
                else:
                    #print user_group['usrgrpid'],user_group['name'],user_group['gui_access'],user_group['users_status']
                    return user['userid']
            if self.terminal_table:
                table=SingleTable(table_show)
                print(table.table)
    #}}}
    # usergroup
    #{{{usergroup_get
    ##
    # @brief host_get 
    #
    # @param hostName
    #
    # @return 
    def usergroup_get(self,usergroupName=''): 
        data=json.dumps({
                "jsonrpc": "2.0",
                "method": "usergroup.get",
                "params": {
                          "output": "extend",
                          "filter":{"name":usergroupName} 
                          },
                "auth": self.user_login(),
                "id": 1
                })
        request = urllib2.Request(self.url,data) 
        for key in self.header: 
            request.add_header(key, self.header[key]) 
        try: 
            result = urllib2.urlopen(request) 
        except URLError as e: 
            if hasattr(e, 'reason'): 
                print 'We failed to reach a server.' 
                print 'Reason: ', e.reason 
            elif hasattr(e, 'code'): 
                print 'The server could not fulfill the request.' 
                print 'Error code: ', e.code 
        else: 
            response = json.loads(result.read()) 
            result.close() 
            print "usergroup sum: \033[31m%s\033[0m"%(len(response['result']))

            if not len(usergroupName):
                if self.terminal_table:
                    table_show=[]
                    table_show.append(["usrgrpid","name","gui_access","users_status"])
                else:
                    print "usrgrpid","name","gui_access","users_status"

            if len(response['result']) == 0:
                return 0
            for user_group in response['result']:      
                if len(usergroupName)==0:
                    if self.terminal_table:
                        table_show.append([user_group['usrgrpid'],user_group['name'],user_group['gui_access'],user_group['users_status']])
                    else:
                        print user_group['usrgrpid'],user_group['name'],user_group['gui_access'],user_group['users_status']
                else:
                    #print user_group['usrgrpid'],user_group['name'],user_group['gui_access'],user_group['users_status']
                    return user_group['usrgrpid']
            if self.terminal_table:
                table=SingleTable(table_show)
                print(table.table)
    #}}}
    #{{{usergroup_create
    def usergroup_create(self, usergroupName,hostgroupName): 
        if self.usergroup_get(usergroupName):
            print "\033[041mthis usergroupName is exists\033[0m" 
            sys.exit(1)

        hostgroupID=self.hostgroup_get(hostgroupName)
        data = json.dumps({ 
                           "jsonrpc":"2.0", 
                           "method":"usergroup.create", 
                           "params":{ 
                                     "name":usergroupName,
                                     "rights":{ 
                                         "permission": 3,
                                         "id":hostgroupID
                                      }, 
                                     }, 
                           "auth": self.user_login(), 
                           "id":1                   
        }) 
        request = urllib2.Request(self.url, data) 
        for key in self.header: 
            request.add_header(key, self.header[key]) 
              
        try: 
            result = urllib2.urlopen(request) 
        except URLError as e: 
            print "Error as ", e 
        else: 
            #print result.read()
            response = json.loads(result.read()) 
            result.close() 
            print "add usergroup : \033[42m%s\033[0m \tid :\033[31m%s\033[0m" % (usergroupName, response['result']['usrgrpids'][0]) 
    #}}}
    #{{{usergroup_del
    def usergroup_del(self,usergroupName):
        usergroup_list=[]
        for i in usergroupName.split(','):
            usergroupID=self.usergroup_get(i)
            if usergroupID:
                usergroup_list.append(self.usergroup_get(i))      
        if not len(usergroup_list):
            print "usergroup \033[041m %s\033[0m  is not exists !"% usergroupName 
            exit(1)
        data=json.dumps({
                "jsonrpc": "2.0",
                "method": "usergroup.delete",
                "params": usergroup_list,
                "auth": self.user_login(),
                "id": 1
                })
        request = urllib2.Request(self.url,data) 
        for key in self.header: 
            request.add_header(key, self.header[key]) 
             
        try: 
            result = urllib2.urlopen(request) 
        except Exception,e: 
            print  e
        else: 
            response = json.loads(result.read()) 
            result.close() 
            print "usergroup \033[042m %s\033[0m  delete OK !"% usergroupName 
    #}}}


if __name__ == "__main__":
    parser=argparse.ArgumentParser(description='zabbix  api ',usage='%(prog)s [options]')
    parser.add_argument('-G','--group',nargs='?',metavar=('GroupName'),dest='listgroup',default='group',help='查询主机组')
    parser.add_argument('--hostgroup_add',nargs=1,dest='hostgroup_add',help='添加主机组')
    parser.add_argument('-H','--host',nargs='?',metavar=('HostName'),dest='listhost',default='host',help='查询主机')
    parser.add_argument('-T','--template',nargs='?',metavar=('TemplateName'),dest='listtemp',default='template',help='查询模板信息')
    parser.add_argument('--item',nargs='+',metavar=('HostID','item_name'),dest='listitem',help='查询item')
    parser.add_argument('--history_get',nargs=4,metavar=('history','item_ID','time_from','time_till'),dest='history_get',help='查询history')
    parser.add_argument('--history_report',nargs=4,metavar=('history_type','item_name','date_from','date_till'),dest='history_report',help='zabbix_api.py \
                        --history_report 0 "CPU idle time" "2016-06-03" "2016-06-10"')
    parser.add_argument('--table',nargs='?',metavar=('ON'),dest='terminal_table',default="OFF",help='show the terminaltables')
    parser.add_argument('--xls',nargs=1,metavar=('xls_name.xls'),dest='xls',\
                        help='export data to xls')
    parser.add_argument('--trend_get',nargs=1,metavar=('item_ID'),dest='trend_get',help='查询item trend')
    # user
    parser.add_argument('--usergroup',nargs='?',metavar=('name'),default='usergroup',dest='usergroup',help='Inquire usergroup ID')
    parser.add_argument('--usergroup_add',dest='usergroup_add',nargs=2,metavar=('usergroupName','hostgroupName'),help='add usergroup')
    parser.add_argument('--usergroup_del',dest='usergroup_del',nargs=1,metavar=('usergroupID'),help='delete usergroup')
    parser.add_argument('--user',nargs='?',metavar=('name'),default='user',dest='user',help='Inquire user ID')
    parser.add_argument('-C','--add-host',dest='addhost',nargs=4,metavar=('192.168.2.1','hostname_ceshi1', 'test01,test02', 'Template01,Template02'),help='添加主机,多个主机组或模板使用分号')
    parser.add_argument('-d','--disable',dest='disablehost',nargs=1,metavar=('192.168.2.1'),help='禁用主机')
    parser.add_argument('-D','--delete',dest='deletehost',nargs='+',metavar=('192.168.2.1'),help='删除主机,多个主机之间用分号')
    parser.add_argument('-v','--version', action='version', version='%(prog)s 1.0.4')
    if len(sys.argv)==1:
        print parser.print_help()
    else:
        args=parser.parse_args()
        terminal_table = False
        if args.terminal_table != "OFF":
            terminal_table = True
        zabbix=zabbix_api(terminal_table)
        export_xls = ["OFF","ceshi.xls"]
        if args.xls:
            export_xls[0] = 'ON'
            export_xls[1]=args.xls[0]
        if args.listhost != 'host' :
            if args.listhost:
                zabbix.host_get(args.listhost)
            else:
                zabbix.host_get()
        if args.listgroup !='group':
            if args.listgroup:
                zabbix.hostgroup_get(args.listgroup)
            else:
                zabbix.hostgroup_get()
        if args.listtemp != 'template':
            if args.listtemp:
                zabbix.template_get(args.listtemp)
            else:
                zabbix.template_get()
        if args.usergroup != 'usergroup':
            if args.usergroup:
                zabbix.usergroup_get(args.usergroup)
            else:
                zabbix.usergroup_get()
        if args.user != 'user':
            if args.user:
                zabbix.user_get(args.user)
            else:
                zabbix.user_get()
        if args.listitem:
            if len(args.listitem) == 1:
                zabbix.item_get(args.listitem[0])
            else:
                zabbix.item_get(args.listitem[0],args.listitem[1])
        if args.history_get:
            zabbix.history_get(args.history_get[0],args.history_get[1],args.history_get[2],args.history_get[3])
        if args.trend_get:
            zabbix.trend_get(args.trend_get[0])
        if args.history_report:
            zabbix.history_report(args.history_report[0],args.history_report[1],args.history_report[2],args.history_report[3],export_xls)
        if args.hostgroup_add:
            zabbix.hostgroup_create(args.hostgroup_add[0])
        if args.addhost:
            zabbix.host_create(args.addhost[0], args.addhost[1], args.addhost[2])
        if args.usergroup_add:
            zabbix.usergroup_create(args.usergroup_add[0], args.usergroup_add[1])
        if args.usergroup_del:
            zabbix.usergroup_del(args.usergroup_del[0])
        if args.disablehost:
            zabbix.host_disable(args.disablehost)
        if args.deletehost:
            zabbix.host_delete(args.deletehost[0])
