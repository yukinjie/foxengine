# -*- coding: utf-8 -*-

#与交易和评估相关的函数

import numpy as np
from wolfox.fengine.base.common import Trade,Evaluation
from wolfox.fengine.core.base import BaseObject
from wolfox.fengine.core.utils import fcustom

import logging
logger = logging.getLogger('wolfox.fengine.core.trade')

VOLUME_BASE = 1000

def buy_first(signal):  #确认是否前进一步以废除第一个卖出信号
    return 1 if signal < 0 else 0

def sell_first(signal):  #确认是否前进一步以废除第一个买入信号
    return 1 if signal > 0 else 0

def double_first(signal):  #双向
    return 0

def default_extra(trade,stock,index):   #不做任何事情
    return trade

def atr_extra(trade,stock,index):   #将atr值赋给trade
    trade.atr = stock.atr[index]
    return trade

def append_attribute_extra(trade,stock,index,attribute_name):
    if attribute_name in stock.__dict__:
        trade.__dict__[attribute_name] = stock.__dict__[attribute_name][index]
    else:
        logger.warn('append attribute error:%s do not have attribute %s',stock.code,attribute_name)
    return trade

atr_extra = fcustom(append_attribute_extra,attribute_name='atr')

def make_trades(stock,signal,tdate,tpositive,tnegative
        ,begin=0,taxrate=125,trade_strategy=buy_first,extra_func=default_extra):
    ''' stock为stock
        ssingal为买卖信号,对于次日买卖的信号，输入前需要将signal roll(1)
        tpositive,tnegative为信号值为正和负时的选择价格
        taxrate为税率，默认为千分之八
        begin为起始交易日
        trade_strategy为交易方式，先买后卖，先卖后买，还是均可
        以买入开始计算
    '''
    assert len(tpositive) == len(tnegative) == len(signal)
    sis = signal.nonzero()[0]  #非0信号的index    
    slen = len(sis)    
    if slen == 0:
        return []
    tbegin = tdate.searchsorted(begin)
    ibegin = sis.searchsorted(tbegin)   #tbegin在非0索引中的插入位置
    #print tbegin,ibegin
    if ibegin >= slen: #空信号
        return []
    should_skip = trade_strategy(signal[sis[ibegin]])
    ibegin += should_skip
    if ibegin >= slen: #仍然是空信号
        return []
    #print signal[tbegin:].tolist(),sis,ibegin,tbegin
    tbegin = sis[ibegin]
    trades = []
    for i in xrange(ibegin,slen):
        ci = sis[i]
        cs = signal[ci]
        price = tpositive[ci] if cs>0 else tnegative[ci]
        ctrade = Trade(stock.code,tdate[ci],price,cs*VOLUME_BASE,taxrate)
        trades.append(extra_func(ctrade,stock,ci))
    if sum(signal[tbegin:]) != 0: #最后一个未平仓,不计算
        #print sum(signal[tbegin:]),signal[tbegin:].tolist()
        trades.pop()
    return trades

def last_trade(stock,signal,tdate,tpositive,tnegative
        ,begin=0,taxrate=125,trade_strategy=buy_first,extra_func=default_extra): #trade_strategy虽然没用，也给写上
    ''' 返回值为[x]形式(无时为[])
    '''
    assert len(tpositive) == len(tnegative) == len(signal)
    sis = signal.nonzero()[0]  #非0信号的index
    tbegin = tdate.searchsorted(begin)
    ibegin = sis.searchsorted(tbegin)   #tbegin在非0索引中的插入位置
    slen = len(sis)
    if slen == 0 or sum(signal[tbegin:]) == 0 or tdate[sis[-1]] < begin: #空信号序列(实际上也是sum(signal)==0)或都已经匹配，无悬挂之买入/卖出
        return []
    last_index = sis[-1]
    cs = signal[last_index]
    price = tpositive[last_index] if cs > 0 else tnegative[last_index]
    ltrade = Trade(stock.code,tdate[last_index],price,cs*VOLUME_BASE,taxrate)
    trades= [extra_func(ltrade,stock,last_index)]
    return trades

def match_trades(trades):
    ''' 对交易进行匹配
        一次交易可以允许多次买卖，以单个股票存续数量为0为交易完成标志
        返回值matched_trades列表中的元素形式为：
            [trade1,trade2,....,traden]
            满足    所有trade的volume之和为0，并且任何前m个trade的volume之和不为0(对于买先策略为大于0)
    '''
    matched_trades = []
    contexts = {}
    for trade in trades:
        if(trade.tstock in contexts):
            sum,items = contexts[trade.tstock]
            items.append(trade)
            sum += trade.tvolume
            if(sum == 0):#交易完成
                del contexts[trade.tstock] #以触发下一次的else (如果设置为None则第一次和每次新交易的判断不同)
                matched_trades.append(items) 
            else:
                contexts[trade.tstock] = (sum,items)
        else:
            contexts[trade.tstock] = (trade.tvolume,[trade])
    #print matched_trades
    #for matched_trade in matched_trades:logger.debug('matched trade:%s,%s',matched_trade[0],matched_trade[1])
    return matched_trades

def evaluate(trades,matcher=match_trades):
    ''' 对交易进行匹配和评估
    '''
    return Evaluation(matcher(trades))

import operator
def DEFAULT_EVALUATE_FILTER(matched_named_trades):
    ''' 输入是元素如下的列表：
            trades:[[trade1,trade2,...],[trade3,trade4,...],....] 闭合交易列表
        返回采纳的闭合交易的合并列表
            [[trade1,trade2,...],[trade3,trade4,...],....]
    '''
    return reduce(operator.add,matched_named_trades)

def gevaluate(named_trades,filter=DEFAULT_EVALUATE_FILTER,matcher=match_trades):
    ''' 对多个来源组的交易进行匹配、头寸管理和评估。一次交易可以允许多次买卖，以单个股票存续数量为0为交易完成标志
        named_trades为BaseObject列表，每个BaseObject包括name,evaluation,trades三个属性
            evalutaion用于对trades中的交易进行风险和期望管理
        filter为对已经匹配成功的交易进行头寸管理
        matched_named_trades列表中的元素为
            trades:[[trade1,trade2,...],[trade3,trade4,...],....]
            满足    所有trade的volume之和为0，并且任何前m个trade的volume之和不为0(对于买先策略为大于0)
                    trade有parent属性，指向其所属的named_trades
            本evaluate函数只有trade1,trade2两个成分，如果要一次买入多次卖出的，需要另一个evaluate
            并且要有相应的新的make_trades函数
    '''
    matched_named_trades = []
    for nt in named_trades:
        tradess=matcher(nt.trades)
        if not tradess: continue   #貌似无此必要,但可简化头寸管理部分的操作，而且更加符合直观
        for trades in tradess:
            for ctrade in trades:
                ctrade.parent = nt
        matched_named_trades.append(tradess)
    matched_trades = filter(matched_named_trades)   #头寸管理并转换成[trades,trades,...]形式
    for matched_trade in matched_trades:
        #print 'matched trade:%s,%s',matched_trade[0],matched_trade[1]
        logger.debug('matched trade:%s,%s',matched_trade[0],matched_trade[1])
    return Evaluation(matched_trades)
