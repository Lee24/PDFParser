# -*- coding:utf-8 -*-
from PDF import PDF
import sys
import os
import time
# from resolver.Resolver import printTest

if __name__ == '__main__':
    reload(sys)
    sys.setdefaultencoding('utf-8')

    # path = u'C:\\work\\pdfparse\\pdfs\\india'
    path = u'C:\\work\\pdfparse\\pdfs\\test'  # test file
    # path = u'C:\\work\\pdfparse\\pdfs\\typical'

    beginTime = int(time.time())
    # print str(beginTime)
    files = os.listdir(path)
    for fileName in files:
        PDF(path, fileName)
    cost = (int(time.time()) - beginTime) / 60
    # print str(time.time())
    # print 'total cost: ' + str(cost)

