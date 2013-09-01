======
Glance
======

Copyright © 2013 nuoqingyun xuqifeng <homheihdu@gmail.com>

August 2013

.. contents:: 目录

介绍
====

Glance是一个分布式、监控PaaS平台的监控程序。Glance能监视各种网络参数，保证服务器系统的安全运营，并为PaaS负载均衡以及迅速定位解决错误提供依据。
该工程是基于Glances，Psutil以及python-nmap开源程序，在此非常感谢开源世界。

Glance 主要功能：
 - CPU 负荷
 - 内存使用
 - 磁盘使用
 - 网络状况
 - 端口监视
 - 进程监视
 - 流量统计

数据格式文档
============

System
------
  * **Note**:获取服务器系统的相关信息，包括CPU,Memory,Disk,Loadavg,Network等等。

  * **数据格式:**
   ::

    {
      "_id" : ObjectId("51dbbb431f4c42191325831d"),
      "uptime" : "1 days 16 hours 16 minutes 29 seconds",
      "network" : {
        "eth1" : {
          "kb_received" : "0.00",
          "kb_transmitted" : "0.00"
        },
        "eth0" : {
          "kb_received" : "0.00",
          "kb_transmitted" : "0.00"
        }
      },
      "time" : 1373354819,
      "last_check" : 1377322180,
      "loadavg" : {
        "cores" : 4,
        "fifteen_minutes" : "0.00",
        "scheduled_processes" : "1/327",
        "minute" : "0.00",
        "five_minutes" : "0.01"
      },
      "memory" : {
        "swap:total:mb" : 0,
        "memory:total:mb" : 1994,
        "memory:free:mb" : 1448,
        "swap:free:mb" : 0,
        "memory:used:%" : 27,
        "swap:used:mb" : 0,
        "memory:used:mb" : 546,
        "swap:used:%" : 0
      },
      "disk" : [{
        "sda1" : {
          "used" : "19G",
          "percent" : "20",
          "free" : "74G",
          "volume" : "/dev/sda1",
          "path" : "/",
          "total" : "97G"
        }
      },
      ],
      "cpu" : {
        "iowait" : "0.00",
        "system" : "0.37",
        "idle" : "99.63",
        "user" : "0.00",
        "steal" : "0.00",
        "nice" : "0.00"
      }
    }

Server
------

  * **Note**:获取受监控服务器的相关信息。

  * **数据格式:**
   ::

    {
      "_id" : ObjectId("51dbbb431f4c4219132583abc"),
      "key" : "0.0.0.0",
      "linux_distro" : "CntOS 6.4",
      "platform" : "32bit",
      "os_name" : "Linux",
      "os_version" : "2.6.32-358.e16.i686",
      "uptime" : "1 days 16 hours 16 minutes 29 seconds",
      "last_check" : 1373358415,
      "hostname" : "appengine",
    }

Traffic
-------

  * **Note**:该功能是针对PaaS平台上的各个应用流量监控和统计。原理是收集Squid的日志文件进行统计。

  * **数据格式:**
   ::

    {
      "_id" : ObjectId("51da8a611f4c425553f97a52"),
      "domain" : "www.wbssfs.com",
      "code" : 0,
      "responsecode" : "200",
      "responsetime" : "48",
      "hit_code" : "TCP_MISS:FIRST_UP_PARENT",
      "log_time" : 1371664742.0,
      "bytes" : 27268,
      "clinet_ip" : "218.30.103.148"
    }

PortScan
--------

  * **Note**:该功能是监控PaaS平台上各个应用的运行状态。

  * **数据格式:**
   ::
   
    {
      "_id" : ObjectId("51da8a611f4c425553f97ade"),
      "host" : "www.wbssfs.com",
      "key" : "0.0.0.0",
      "scan" : {
        "80" : {
            "state" : "up", 
            "reason" : "syn-ack",
            "name"': "http"
        },
        "22" : {
            "state" : "open",
            "reason" : "syn-ack",
            "name" : "ssh"
        },
        "5555" : {
            "state" : "closed",
            "reason" : "reset",
            "name" : "freeciv"
        }
    }
            
Process
-------

  * **Note**:该功能是监控指定进程运行状态。

  * **数据格式:**
   ::
    
    {
      "_id" : ObjectId("51dbbb431f4c42191325831e"),
      "1377324487" : [{
        "username" : "root",
        "status" : "S",
        "cpu_times" : [0.0, 0.0],
        "name" : "nginx.conf",
        "cpu_percent" : 0.0,
        "pid" : 5790,
        "io_counters" : [0, 4096, 0, 4096, 1],
        "cmdline" : "nginx: master process /usr/sbin/nginx -c /etc/nginx/nginx.conf",
        "memory_percent" : 0.099388068004504684,
        "memory_info" : [1200128, 15650816],
        "time_since_update" : 1,
        "nice" : 0
      },
      ...,
      ]
    }

Glance APIs
===========

System
------

-  get_system获取服务节点的系统信息，包括CPU，Memory，Disk，Load average，network等数据。
* **HTTP Verb:**
  ::
    POST 
* **URl:**
  ::
    test/glance/(:id)/action
* **Request JSON:**
  ::
    {
      "getsysteminfo":
        {
          "charts" : ["cpu", "memory", "disk", "network", "loadavg"],
          "date_to" : 1377322180,
          "date_from" : 1373358415,
          "server" : {"key" : "0.0.0.0"}
        }
    }
* **Response:**
  ::
   {
    'network': 
        [
            [
                {u'tx': 3192, u'cumulative_rx': 5709569, u'rx': 420, u'cumulative_cx': 21369507, u'time_since_update': 1, u'cx': 3612, u'cumulative_tx': 15659938, u'interface_name': u'eth0'}, 
                {u'tx': 5138, u'cumulative_rx': 5124401, u'rx': 5138, u'cumulative_cx': 10248802, u'time_since_update': 1, u'cx': 10276, u'cumulative_tx': 5124401, u'interface_name': u'lo'}
            ]
        ], 
    'loadavg': 
        [
            {u'min1': 0.53000000000000003, u'min5': 0.41999999999999998, u'min15': 0.20000000000000001}
        ], 
    'disk': 
        [
            [
                {u'mnt_point': u'/', u'used': 3084668928L, u'device_name': u'/dev/mapper/vg_centos-lv_root', u'avail': 6202675200L, u'fs_type': u'ext4', u'size': 9784369152L}, 
                {u'mnt_point': u'/boot', u'used': 32409600, u'device_name': u'/dev/sda1', u'avail': 449120256, u'fs_type': u'ext4', u'size': 507744256}, 
                {u'mnt_point': u'/var/lib/nfs/rpc_pipefs', u'used': 0, u'device_name': u'sunrpc', u'avail': 0, u'fs_type': u'rpc_pipefs', u'size': 0}
            ]
        ], 
    'cpu': 
        [
            {u'iowait': 0.0, u'system': 68.292682927163696, u'idle': 0.0, u'user': 26.829268292807875, u'irq': 1.2195121951275518, u'nice': 0.0}
        ], 
    'memory': 
        [
            {u'used': 145575936, u'cached': 370167808, u'percent': 12.1, u'free': 1061941248, u'inactive': 339963904, u'active': 193515520, u'total': 1207517184, u'buffers': 81489920}
        ]
    }

Server
------

-  get_server获取服务节点的信息。
* **HTTP Verb:**
  ::
    POST 
* **URl:**
  ::
    test/glance/(:id)/action
* **Request JSON:**
  ::
    {
      "getserverinfo":
        {
          "filter" : ["id1", "id2", "id3", "id4", "id5"],
        }
    }
    ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
    {
      "getserverinfo":
        {
          "key" : "0.0.0.0"
        }
    }
    ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
    {
      "getserverinfo":
        {
        }
    }

* **Response:**
  ::
    {
      "52184dc6d0e96f1bdf667a4b":
        {
          "uptime" : "0 days 7 hours 46 minutes 28 seconds",
          "os_name" : "Linux",
          "platform" : "32bit",
          "linux_distro" : "CentOS 6.4",
          "hostname" : "centos.mepoo",
          "last_check" : 1377330300,
          "os_version" : "2.6.32-358.el6.i686",
          "key" : "0.0.0.0"
        },
        ...
    }
    
Traffic
-------

-  Traffic获取CDN服务节access.log信息,计算各个网站的流量。
* **HTTP Verb:**
  ::
    POST 
* **URl:**
  ::
    test/glance/(:id)/action
* **Request JSON:**
  ::
    {
      "gettrafficinfo":
        {
         "date": "day",
         "domain": "www.sscnfs.com"
        }
    }

* **Response:**
  ::
    {"traffic":
      [
       {
        "domain": "www.sscnfs.com", 
        "value": 
            {
                "visit": 2.0, 
                "hits": 2.0, 
                "bytes": 223172.0
            }
       }
     ]
    }


PortScan
--------

-  PortScan获取服务节点程序的运行状态信息。
* **HTTP Verb:**
  ::
    POST 
* **URl:**
  ::
    test/glance/(:id)/action
* **Request JSON:**
  ::
    {
      "portscaninfo":
        [
         {"key": "0.0.0.0"}
        ]
    }

* **Response:**
  ::
    [
       {
        "key":"0.0.0.0",
        "host":""
        "scan": 
          {
            "21":{"state": 'closed', 'reason': 'reset', 'name': 'ftp'}, 
            "22":{"state": 'open', 'reason': 'syn-ack', 'name': 'ssh'},
            "5555":{"state": 'closed', 'reason': 'reset', 'name': 'freeciv'}, 
            "80": {"state": 'open', 'reason': 'syn-ack', 'name': 'http'}, 
            "81": {"state": 'closed', 'reason': 'reset', 'name': 'hosts2-ns'}, 
            "5500": {"state": 'closed', 'reason': 'reset', 'name': 'hotline'}
          }
        'time':1377324534
      }
     ]

Process
-------

-  Process获取服务节点程序的进程状态信息。
* **HTTP Verb:**
  ::
    POST 
* **URl:**
  ::
    test/glance/(:id)/action
* **Request JSON:**
  ::
    {
      "getprocessinfo":
        {
         "server":{"key": "0.0.0.0"},
         "date_to":1377666446
        }
    }

* **Response:**
  ::
     {
        'key':'0.0.0.0',
        'processes': 
          {
            'username': 'root', 
            'status': 'S', 
            'cpu_times': [0.0, 0.11], 
            'name': 'nginx.conf', 
            'cpu_percent': 0.0, 
            'pid': 1494, 
            'io_counters': [0, 4096, 0, 4096, 1], 
            'cmdline': 'nginx: master process /usr/sbin/nginx -c /etc/nginx/nginx.conf', 
            'memory_percent': 0.13025603451784915, 
            'memory_info': [1572864, 15650816], 
            'time_since_update': 1, 
            'nice': 0
          }, 
        'time':1377324534
    }
    
