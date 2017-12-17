# -*- coding: UTF-8 -*-
from TextChunk import TextChunk


class Page:
    def __init__(self, content, pageNum):
        self.originContent = content
        self.pageNum = pageNum

        # content box
        self.contentBox = absorb(self.originContent)
        self.lineBox = []

        if len(self.contentBox) > 0:  # 防止整页都没有文本的时越界异常
            # 排序
            self.contentBox.sort(cmp=textLineSortFunc)

            # 降噪 (这一步暂时不做)

            # 行汇聚

            self.lineBox = lineAggregate(self.contentBox)



def lineAggregate(contentBox):
    lineBox = [[contentBox[0]]]

    for textIndex in range(0, len(contentBox) - 1):  # 临时代码，硬编码的先去掉每一页的最后一行
        first = contentBox[textIndex]
        second = contentBox[textIndex + 1]

        xRange = [float(first.x0), float(first.x1), float(second.x0), float(second.x1)]
        xJudge = (xRange[0] > xRange[3] or xRange[2] > xRange[1])

        yJudge = overlapRate([float(first.y0), float(first.y1)], [float(second.y0), float(second.y1)]) == 1

        if xJudge and yJudge:
            lineBox[-1].append(second)
        else:
            lineBox.append([second])

    return lineBox

def textLineSortFunc(first, second):
    #-1调位 1不调位
    firstYRange = [float(first.y0), float(first.y1)]
    secondYRange = [float(second.y0), float(second.y1)]
    if overlapRate(firstYRange, secondYRange) >= 0.9:
        if first.x0 <= second.x0:
            return -1
        else:
            return 1
    elif first.y0 > second.y0:
        return -1
    elif first.y0 < second.y0:
        return 1

def overlapRate(firstYRange, secondYRange):
    # 计算重叠度，如果重叠度等于

    if firstYRange[0] > secondYRange[1] or secondYRange[0] > firstYRange[1]:
        return 0
    else:
        borderList = (firstYRange + secondYRange)
        borderList.sort()
        firstGap = abs(firstYRange[1] - firstYRange[0])
        secondGap = abs(secondYRange[1] - secondYRange[0])
        overlapGap = abs(borderList[2] - borderList[1])
        return overlapGap / min(firstGap,secondGap)


def absorb(pageContent):
    LTTextBoxHorizontalBox = []
    LTFigurelBox = []
    LTRectBox = []
    LTCurveBox = []
    LTLineBox = []

    contentBox = []

    splitter = {
        'LTTextBoxHorizontal': LTTextBoxHorizontalBox,
        'LTFigure': LTFigurelBox,
        'LTRect': LTRectBox,
        'LTCurve': LTCurveBox,
        'LTLine': LTLineBox
    }
    # 第一层次对象分类保存
    for element in pageContent:
        elementName = str(type(element)).split('.')[-1].split("'")[0]
        targetBox = splitter[elementName]
        targetBox.append(element)

    # 获取目标对象，封装成自定义对象，作为分析的基础。现阶段先从LTTextLineHorizontal入手，获取文本段封装到OriginPTextLine中
    for textBox in LTTextBoxHorizontalBox:
        for textLine in textBox:
            text = textLine.get_text()
            x0 = textLine.x0
            y0 = textLine.y0
            x1 = textLine.x1
            y1 = textLine.y1
            contentBox.append(TextChunk(text, x0, y0, x1, y1))

    return contentBox
