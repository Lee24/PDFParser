# -*- coding: UTF-8 -*-
import os

import time

import re
from pdfminer.converter import PDFPageAggregator
from pdfminer.layout import LAParams
from pdfminer.pdfdocument import PDFDocument, PDFTextExtractionNotAllowed, PDFEncryptionError
from pdfminer.pdfinterp import PDFResourceManager, PDFPageInterpreter
from pdfminer.pdfpage import PDFPage
from pdfminer.pdfparser import PDFParser

from Page import Page
from TableRegion import TableRegion
import tools


def outputRegionTable(path, fileName, tableRegionBox):
    outPath = path + '_output' + "\\" + fileName.split('.')[0]
    if not os.path.exists(outPath):
        os.makedirs(outPath)

    for index in range(0, len(tableRegionBox)):
        region = tableRegionBox[index]
        title = ''
        for line in region.title:
            for text in line:
                title_part = re.sub('[\/\\:\*\?\"\<\>\r\n]', '', text.text)
                # title_part = text.text.replace(r'\/\/ ', '_')
                title = title + re.sub('[\n]', '', title_part) + '_#_'

        title = title[0: -3]

        outPutName =outPath + "\\" + str(region.page.pageNum) + '_' + title
        if len(outPath + "\\" + str(region.page.pageNum + 1) + '_' + title + ".csv") > 200:
            outPutName = outPutName[0: 200]
        outPutName = outPutName + ".csv"
        outFile = file(outPutName, "w+")

        # for index in range(0, len(region.header) + len(region.body) + 2):


        for line in region.header:
            textIndex = 0
            for refer in region.referLine:
                referIndex = refer['index']
                textCloumnIndex = line[textIndex]['index']
                text = line[textIndex]['textChunk'].text

                if referIndex == textCloumnIndex:
                    aim = re.sub('[\,\n]', '', text)
                    outFile.write(aim + ',')
                    if textIndex < len(line) - 1:
                        textIndex = textIndex + 1
                else:
                    outFile.write(',')
            outFile.write('\n')
        outFile.write('\n')
        outFile.write('\n')

        for line in region.body:
            textIndex = 0
            for refer in region.referLine:
                referIndex = refer['index']
                textCloumnIndex = line[textIndex]['index']
                text = line[textIndex]['textChunk'].text

                if referIndex == textCloumnIndex:
                    aim = re.sub('[\,\n]', '', text)
                    outFile.write(aim + ',')
                    if textIndex < len(line) - 1:
                        textIndex = textIndex + 1
                else:
                    outFile.write(',')
            outFile.write('\n')
        outFile.close()


def printLineLenAndType(pageBox):
    for page in pageBox:
        print '==========' + str(page.pageNum)
        for line in page.lineBox:
            print str(len(line)),
            for textChunk in line:
                print textChunk.type + ' ',
            print '\n'


def isTitleLegal(title):
    flag = False
    for line in title:
        lineText = ''
        for textChunk in line:
            lineText = lineText + textChunk.text
        texts = lineText.split(' ')
        if tools.isHaveTitleKeyWord(texts):
            flag = True
            break
    return flag

class PDF:
    def __init__(self, path, fileName):
        beginTime = int(time.time())
        self.path = path
        self.fileName = fileName

        # 获取元信息： 1. 公司名称、id 2. 报表时间
        metaData = getMetaData(fileName)
        self.companyID = metaData['companyID']
        self.time = metaData['time']

        # 利用第三方接口提取pdf文本信息，封装到OriginPPage中
        filePath = os.path.join('%s\%s' % (path, fileName))
        self.pageBox = genPages(filePath)

        # 过滤掉无用page 规则 1. 识别不出text的page
        self.pageBox = [page for page in self.pageBox if len(page.contentBox) > 0]

        # printLineLenAndType(self.pageBox)

        # 识别TableRegion
        self.tableRegionBox = captureTableRegion(self.pageBox)

        #降噪，去掉无用TableRegion
        self.tableRegionBox = [tableRegion for tableRegion in self.tableRegionBox if tableRegion.isHaveDigit
                                   and len(tableRegion.body) > 0 and isTitleLegal(tableRegion.title)]

        # 以文件输出阶段结果
        outputRegionTable(self.path, self.fileName, self.tableRegionBox)

def captureTableRegion(pageBox):
    tableRegionBox = []
    for page in pageBox:
        lineBox = page.lineBox

        cloumnThr = 3
        serialMultiColumnThr = 2
        multiColumnBlockGap = 3

        beginIndex = -1  # 第一个列数大于cloumnTh的行的index
        serialNum = 0  # 连续列数大于cloumnTh的行数
        gapNum = 0  # 列数大于cloumnTh的行之间隔的行数

        for lineIndex in range(0, len(lineBox)):
            line = lineBox[lineIndex]
            if len(line) >= cloumnThr:
                if beginIndex == -1:
                    beginIndex = lineIndex
                serialNum = serialNum + 1  # 一旦这个加到上二之后，其它的加不加意义不大
                gapNum = 0
            else:
                if serialNum >= serialMultiColumnThr:
                    if len(line) <= 1:
                        gapNum = gapNum + 1
                    if gapNum > multiColumnBlockGap or (len(line) == 1 and line[0].type == 'text-sentence'):
                        begin = max(0, beginIndex - 5)
                        tableRegionBox.append(TableRegion(
                            lineBox[begin: lineIndex],
                            page,
                            begin,
                            lineIndex))
                        beginIndex = -1
                        serialNum = 0
                        gapNum = 0
                else:
                    beginIndex = -1
                    serialNum = 0
                    gapNum = 0

        if beginIndex > -1 and serialNum >= 2:
            begin = max(0, beginIndex - 5)
            tableRegionBox.append(TableRegion(
                lineBox[begin: len(lineBox)],
                page,
                begin,
                len(lineBox)))
    return tableRegionBox


def getMetaData(fileName):
    info = str(fileName).split('_')
    return {
        "companyID": info[0],
        "time": info[1]
    }


def genPages(filePath):
    pageBox = []
    document = ''
    try:
        document = PDFDocument(PDFParser(open(filePath, 'rb')))
    except PDFEncryptionError:
        print 'password require: ' + filePath
        return ''

    else:

    #处理加密pdf
        print '========process: ' + filePath
        if not document.is_extractable:
            raise PDFTextExtractionNotAllowed

        rsrcmgr = PDFResourceManager()
        laparams = LAParams()

        device = PDFPageAggregator(rsrcmgr, laparams=laparams)

        interpreter = PDFPageInterpreter(rsrcmgr, device)

        pageNum = 0

        for page in PDFPage.create_pages(document):
            print pageNum
            interpreter.process_page(page)

            content = device.get_result()
            # step 1 : 初步处理，把数据装入到自己定义的对象
            pageBox.append(Page(content, pageNum))

            pageNum = pageNum + 1

        return pageBox
