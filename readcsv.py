#!/usr/bin/env python
# -*- coding:utf-8 -*-

import csv
with open('egg.csv','rb') as f:
 reader = csv.reader(f)
 for row in reader:
  print row
