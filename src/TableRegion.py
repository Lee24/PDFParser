# -*- coding: UTF-8 -*-


class TableRegion:
    def __init__(self, content, page, beginLine, endLine):
        self.content = content  # line aggregate
        self.page = page
        self.beginLine = beginLine  # begin line in the page
        self.endLine = endLine  # end line in the page

        # 特征
        self.isHaveDigit = isHaveDigit(self.content)
        #正文范围
        self.tableBodyRange = genTableBodyRange(self.content)

        #降噪，去掉表正文最后一行后的所有行
        self.content = self.content[0: self.tableBodyRange['endLine'] + 1]

        # 纵向分割（旧方法）
        # self.splitLineBox = genDevideLine(self.content, self.tableBodyRange)
        # self.structure = genStructureBox(self.content, self.splitLineBox)

        # 列划分（新方法） 划分出表title，header，body，
        self.title = []
        self.header = []
        self.body = []
        self.referLine = []
        if len(self.content) > 0:
            result = devide(self.content, self.tableBodyRange, self.page.lineBox, self.beginLine)
            self.title = result['title']
            self.header = result['header']
            self.body = result['body']
            self.referLine = result['referLine']


        # 结构化到array —— 寻找数字列 —— 合并数字列左边所有列，并更新referLine




def devide(content, tableBodyRange, originLineBox, TRbeginLineOnPage):
    bodyDevideBox = [[]]
    referLine = []
    headerReferLine = [] #表头的参考线和body的不一样，表头的参考线只参考body中从上到下的第一个元素

    #表正文划分
    for index in range(0, len(content[tableBodyRange['beginLine']])):
        textChunk = content[tableBodyRange['beginLine']][index]
        bodyDevideBox[0].append({
            'textChunk': textChunk,
            'index': 100 * (index + 1)
        })
        referLine.append({
            'x0': textChunk.x0,
            'x1': textChunk.x1,
            'index': 100 * (index + 1)
        })
        headerReferLine.append({
            'x0': textChunk.x0,
            'x1': textChunk.x1,
            'index': 100 * (index + 1)
        })

    for line in content[tableBodyRange['beginLine'] + 1 : tableBodyRange['endLine'] + 1]:
        result = genLineIndex(referLine, line, headerReferLine)
        referLine = result['referLine']
        headerReferLine = result['headerReferLine']
        bodyDevideBox.append(result['lineAndIndex'])

    #表头划分及表头区域识别。有可能在tableRegion范围内都没有找全header区域，如果这样的话，表区域需要在下一步继续找
    headerDevideBox = []
    extendBodyBox = []

    headerBeginLine = 0
    headerEndLine = 0
    initRange = range(0, TRbeginLineOnPage + tableBodyRange['beginLine'])
    initRange.reverse()
    for index in initRange:
        line = originLineBox[index]

        result = genLineIndex(headerReferLine, line, headerReferLine)
        referLine = result['referLine']
        lineAndIndex = result['lineAndIndex']

        if not (len(line) == 1 and lineAndIndex[0]['index'] == referLine[0]['index']):  # 正常表头范围
            if headerEndLine == 0:
                headerEndLine = index
            headerBeginLine = index
            headerDevideBox.append(lineAndIndex)
        else:
            if headerEndLine == 0:      #意味着还没有开始识别到表头，这一部分内容属于扩展的正文内容
                extendBodyBox.append(lineAndIndex)
            else:  #意味着表头范围结束了。 接下来可以确定表title
                break

    #表正文合并
    extendBodyBox.reverse()
    body = extendBodyBox + bodyDevideBox

    #表title识别
    tileRegionBeginLine = max(0, headerBeginLine - 5)  #在表头往上五行内找title
    titleRegion = originLineBox[tileRegionBeginLine: headerBeginLine]
    titleRegion.reverse()
    titleLineNumThr = 2  # 取两行合格的line作为title
    title = []
    for line in titleRegion:
        isSentence = False
        for textChunk in line:
            if textChunk.type == 'text-sentence':
                isSentence = True
                break
        if not isSentence:
            title.append(line)
        if len(title) >= titleLineNumThr:  # 找够了，结束
            break
    title.reverse()

    #表头
    headerDevideBox.reverse()

    # 合并“表正文”和"扩展正文"
    return {
        'referLine': referLine,
        'title': title,
        'header': headerDevideBox,
        'body': body

    }


def genLineIndex(referLine, line, headerReferLine):
    lineAndIndex = []
    newRefer = referLine

    for textChunk in line:
        referLine = sorted(referLine, key=lambda refer: refer['index'])
        for index in range(0, len(referLine)):
            refer = referLine[index]
            referIndex = referLine[index]['index']
            if textChunk.x1 < refer['x0']:  # 在参考物前面
                if index == 0:  # 第一个
                    lineAndIndex.append({
                        'textChunk': textChunk,
                        'index': (0 + referIndex) / 2  # 因为index不是沿用原来的index，所以是一个新的参考物
                    })
                    referLine.append({
                        'x0': textChunk.x0,
                        'x1': textChunk.x1,
                        'index': (0 + referIndex) / 2
                    })
                    headerReferLine.append(
                        {
                            'x0': textChunk.x0,
                            'x1': textChunk.x1,
                            'index': (0 + referIndex) / 2
                    })
                    break
                else:  # 非第一个
                    lastReferIndex = referLine[index-1]['index']
                    lineAndIndex.append({
                        'textChunk': textChunk,
                        'index': (lastReferIndex + referIndex) / 2  # 因为index不是沿用原来的index，所以是一个新的参考物
                    })
                    referLine.append({
                        'x0': textChunk.x0,
                        'x1': textChunk.x1,
                        'index': (lastReferIndex + referIndex) / 2
                    })
                    headerReferLine.append({
                        'x0': textChunk.x0,
                        'x1': textChunk.x1,
                        'index': (lastReferIndex + referIndex) / 2
                    })
                    break
            elif (not textChunk.x0 > refer['x1']) and not (textChunk.x1 < refer['x0']): #与参考物相交
                # 判断和后一个是否相交。如果相交
                lineAndIndex.append({
                    'textChunk': textChunk,
                    'index': referIndex
                })
                x0 = refer['x0']
                x1 = refer['x1']
                if len(line) > 1:  # 该行列数大于1且该列只与一个refer重叠的情况下， 该列所占的位置才可作为参考值
                    x0 = min(float(textChunk.x0), float(refer['x0']))
                    x1 = max(float(textChunk.x1), float(refer['x1']))
                referLine[index]['x0'] = x0
                referLine[index]['x1'] = x1
                referLine[index]['index'] = referIndex
                break
            elif textChunk.x0 > refer['x1'] and index + 1 == len(referLine): #在参考物后面且是本行的最后一个
                lineAndIndex.append({
                    'textChunk': textChunk,
                    'index': referIndex + 100
                })
                referLine.append({
                    'x0': textChunk.x0,
                    'x1': textChunk.x1,
                    'index': referIndex + 100
                })
                headerReferLine.append({
                    'x0': textChunk.x0,
                    'x1': textChunk.x1,
                    'index': referIndex + 100
                })
                break

    return {
        'referLine': referLine,
        'lineAndIndex': lineAndIndex,
        'headerReferLine': headerReferLine
    }


def genStructureBox(content, splitLineBox):
    arrayBox = []
    for i in range(0, len(content)):
        line = []
        for k in range(0, len(splitLineBox)):
            line.append('')
        arrayBox.append(line)

    for index in range(0, len(content)):
        lineData = content[index]
        for text in lineData:
            for splitLineIndex in range(0, len(splitLineBox)):
                if text.x1 < splitLineBox[splitLineIndex] or (text.x0 < splitLineBox[splitLineIndex] and text.x1 > splitLineBox[splitLineIndex]):
                    if arrayBox[index][splitLineIndex] != '':
                        exist = arrayBox[index][splitLineIndex]
                        exist.text = exist.text + ' ' + text.text
                        exist.x0 = min(text.x0, exist.x0)
                        exist.x1 = max(text.x1, exist.x1)
                        exist.y0 = min(text.y0, exist.y0)
                        exist.y1 = max(text.y1, exist.y1)
                        arrayBox[index][splitLineIndex] = exist
                    else:
                        arrayBox[index][splitLineIndex] = text
                    break
    return arrayBox



def genDevideLine(content, tableBodyRange):
    gaps = [[0, 100000000]]  #设置一个极大值表示pdf页面最右边边界
    for lineIndex in range(tableBodyRange['beginLine'], tableBodyRange['endLine']):
        gaps = genGaps(gaps, content[lineIndex])
    splitLineBox = identifyHeader(content, gaps, tableBodyRange)
    return splitLineBox

def genGaps(gaps, line):
    for text in line:
        textRange = [text.x0, text.x1]
        tempBox = []
        for gapIndex in range(0, len(gaps)):
            result = processRanges(gaps[gapIndex], textRange)
            tempBox = tempBox + result['newGap']
            if len(result['residue']) != 0:
                textRange = result['residue']
            else:
                if gapIndex == len(gaps) - 1 :
                    gaps = tempBox
                else:
                    gaps = tempBox + gaps[gapIndex + 1: len(gaps)]
                break
    return gaps
def processRanges(gap, textRange):
    # 以下是非常不好，非常垃圾的代码，极度容易有bug，不过除了这样，不知道怎么写，顶
    # print ''
    if gap[1] <= textRange[0] or gap[0] >= textRange[1]:
        return {
            'newGap': [gap],
            'residue': textRange
        }
    elif textRange[0] <= gap[0]:
        if textRange[1] < gap[1]:
            return {
                'newGap': [[textRange[1], gap[1]]],
                'residue': []
            }
        elif textRange[1] == gap[1]:
            return {
                'newGap': [],
                'residue': []
            }
        else:
            return {
                'newGap': [],
                'residue': [gap[1], textRange[1]]
            }
    elif gap[0] < textRange[0] and gap[1] > textRange[1]:
        return {
            'newGap': [[gap[0], textRange[0]], [textRange[1], gap[1]]],
            'residue': []
        }
    elif gap[0] < textRange[0] and gap[1] < textRange[1]:
        return {
            'newGap': [[gap[0], textRange[0]]],
            'residue': [gap[1], textRange[1]]
        }
    else:
        raise Exception('vertical devide error')
def identifyHeader(content, gaps, tableBodyRange):
    splitLineBox = []

    # 下面这个代码也是醉了
    lineIndex = tableBodyRange['beginLine']
    findedHeaderLineFlag = False


    headerRegion = content[0: tableBodyRange['beginLine']]
    headerRegion.reverse()

    for line in headerRegion:
        if not findedHeaderLineFlag:
            lineIndex = lineIndex - 1
            for text in line:
                if not findedHeaderLineFlag:
                    textRange = [text.x0, text.x1]
                    tempBox = []
                    for gap in gaps:
                        result = processRanges(gap, textRange)
                        if len(result['newGap']) != 1:
                            findedHeaderLineFlag = True
                            break
                        else:
                            tempBox = tempBox + result['newGap']
                            if len(result['residue']) > 0:
                                textRange = result['residue']
                            else:
                                break
                    if len(tempBox) == len(gaps):
                        gaps = tempBox
                    else:
                        gaps = tempBox + gaps[len(tempBox): len(gaps)]
                else:
                    break
        else:
            break
    for gap in gaps:
        if gap[0] != 0 :
            splitLineBox.append((gap[0] + gap[1])/2)
    return splitLineBox


def isAllDigit(line):
    flag = True
    for textChunk in line:
        if textChunk.type != 'digit':
            flag = False
            break
    return flag


def genTableBodyRange(content):
    # 第一行列数大于等于3，并且除第一列外出现数字的行 最后一行列数大于等于3，并且出现数字的行
    multiColunmThr = 3
    beginLine = -1
    endLine = -1
    isFirst = True
    for lineIndex in range(0, len(content)):
        tempLINE = content[lineIndex]
        if len(content[lineIndex]) >= multiColunmThr:
            if isFirst:
                isFirst = False
            else:
                for colunmIndex in range(1, len(content[lineIndex])):
                    if content[lineIndex][colunmIndex].type == 'digit':
                        if beginLine == -1:
                            beginLine = lineIndex
                        else:
                            endLine = lineIndex
                        break
        elif len(content[lineIndex]) == 2 and isAllDigit(content[lineIndex]):
            if isFirst:
                isFirst = False
            else:
                if beginLine == -1:
                    beginLine = lineIndex
                else:
                    endLine = lineIndex

    return {
        'beginLine': beginLine,
        'endLine': endLine
    }

def isHaveDigit(content):
    for line in content:
        for textLine in line:
            if textLine.type == 'digit':
                return True
    return False
