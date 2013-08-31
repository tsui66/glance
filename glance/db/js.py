#!/usr/bin/env python
#encode=utf-8
#vim: tabstop=4 shiftwidth=4 softtabstop=4
#Created on 2013-6-24
#Copyright 2013 nuoqingyun xuqifeng

from bson.code import Code

traffic_map = Code("function () {"
        "emit(this.domain, this.bytes);"
                    "}")

traffic_reduce = Code("function (key, values) {"
                        " var sum = 0;"
                        " var count = 0;"
                        " values.forEach(function(byte){"
                        " sum += byte;"
                        " count ++;"
                        "});"
                        " return {'sum':sum, 'count':count};"
                        "}")

traffic_reduce1 = Code("function (keyDomain, valuesBytes) {"
                          " return Array.sum(valuesBytes);"
                          "}")
traffic_map_test = Code("function () {"
        "emit(this.domain, {bytes:this.bytes, visit:1, hits:this.code});"
        "}")

traffic_reduce_test = Code("function (key, values) {"
                        " var sum = 0;"
                        " var count = 0;"
                        " var visits = 0;"
                        " values.forEach(function(vals){"
                        " sum += vals.bytes;"
                        " count += vals.hits;"
                        " visits += vals.visit;"
                        "});"
                        " return {bytes:sum, visit:visits, hits:count};"
                        "}")


