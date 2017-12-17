# -*- coding: UTF-8 -*-
import re


def recognizeType(text):
    # 类型分类：
    # text-sentence  —— 普通文本-句子
    # text-phrase  —— 普通文本-句子
    # time  —— 时间
    # quantity —— 数量单位
    # currency —— 货币单位
    # digit  —— 数字  暂时货币单位 数量单位 都先归类到digit类型
    # digit-quantity  —— 数字加数量单位
    # digit-currency  —— 数字加货币单位
    # placeholder  ——  占位符

    aim = re.sub('[\(\)\,]', '', text)
    aim = aim.strip()

    digit_re = re.compile(r'(^[1-9]+[\.]?[0-9]+$)|(^[1-9]+[\.]?[0-9]?[a-z]?$)|(^0.[0-9]+[a-z]?$)')

    if aim.isdigit() or digit_re.match(aim): # digit 开头的都先标记成digit
        return 'digit'
    elif aim == '—' or aim == '-':  # 占位符
        return 'placeholder'
    else:
        if len(aim) > 100:
            return 'text-sentence'
        else:
            return 'text-phrase'


class TextChunk:
    def __init__(self, text, x0, y0, x1, y1):
        self.text = re.sub('[\n]', '', text)
        self.x0 = x0
        self.y0 = y0
        self.x1 = x1
        self.y1 = y1
        self.type = recognizeType(text)