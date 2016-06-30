# report


<h2 name="1.4">1.4 report报表</h2>

<h3>1.4.1 简单了解内容</h3>

report 包括以下内容

服务器可用性报表
    
+ 服务器可用性报表使用Agent ping计算，Agent ping 成功时会入库1，如果失败时，则不入库。
+ trend会每个小时将history中的值计算出最大值，最小值，和平均值，这里我们需要的是trend小时的记录个数即可，有两点需要注意，(1)trend记录的是前一天之前的数据，比如今天是2016年06月29日10点，那tren中最新的数据也只是2016年06月29日00点00分的数据,即2016-06-28 23:00:00~2016-06-29 00:00:00的数据。(2)搜索trend数据时，假如搜索前一天的话，应该是搜索时间为2016-06-28 00:00:01到2016-06-29 00:00:00 ,因为如果输入2016-06-28 00:00:00的话，会将2016-06-27 23:59:01~2016-06-28 00:00:00的时间段的值加到其中

服务器日常使用报表

+ CPU在一段时间内的最高值、平均值、最小值等
+ item支持模糊搜索
+ 文件系统的使用情况等

<h3>1.4.2 服务器可用性报表</h3>

输出显示时加--table可以表框显示
![Screenshot](https://github.com/BillWang139967/zabbix_manager/raw/master/images/report_available_table.jpg)

输出显示时加--xls ceshi.xls可以导出excel文件，如下

![Screenshot](https://github.com/BillWang139967/zabbix_manager/raw/master/images/report_available_xls.jpg)

<h3>1.4.2 服务器日常使用报表</h3>