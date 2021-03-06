# -*- coding: utf-8 -*-

#商品期货   从9:00-15:00, 且中间有休息,5/15/30/60分钟处理比较麻烦

from wolfox.fengine.ifuture.ibase import *

def extract_if(line):
    items = line.split(',')
    record = BaseObject()
    record.date = int(items[0].replace('/',''))
    record.time = int(items[1].replace(':',''))
    if float(items[2]) < 10000:
        record.open = int(float(items[2])*10 + 0.1)
        record.high = int(float(items[3])*10 + 0.1)
        record.low = int(float(items[4])*10 + 0.1)
        record.close = int(float(items[5])*10 + 0.1)
    else:
        record.open = int(float(items[2]) + 0.1)
        record.high = int(float(items[3]) + 0.1)
        record.low = int(float(items[4]) + 0.1)
        record.close = int(float(items[5]) + 0.1)
    record.vol = int(float(items[6]) + 0.1)
    record.holding = int(float(items[7]) + 0.1)

    return record

def extract_if_wh(line):
    items = line.split(',')
    record = BaseObject()
    xdate = items[0].replace('/','')   #从mm/dd/yyyy转为yyyymmdd
    record.date = int(xdate[-4:] + xdate[:-4])
    record.time = int(items[1].replace(':',''))
    if float(items[2]) < 10000:
        record.open = int(float(items[2])*10 + 0.1)
        record.high = int(float(items[3])*10 + 0.1)
        record.low = int(float(items[4])*10 + 0.1)
        record.close = int(float(items[5])*10 + 0.1)
    else:
        record.open = int(float(items[2]) + 0.1)
        record.high = int(float(items[3]) + 0.1)
        record.low = int(float(items[4]) + 0.1)
        record.close = int(float(items[5]) + 0.1)
    #items[6]为平均价
    record.vol = int(float(items[7]) + 0.1)
    record.holding = int(float(items[8]) + 0.1)

    return record

def read_if_as_np(filename,extractor=extract_if):
    records = read_if(filename,extractor)
    n = len(records)
    narrays = [np.zeros(n,int),np.zeros(n,int),np.zeros(n,int),np.zeros(n,int),np.zeros(n,int),np.zeros(n,int),np.zeros(n,int),np.zeros(n,int),np.zeros(n,int)]
    i = 0
    for record in records:
        narrays[IDATE][i] = record.date
        narrays[ITIME][i] = record.time
        narrays[IOPEN][i] = record.open        
        narrays[ICLOSE][i] = record.close
        narrays[IHIGH][i] = record.high
        narrays[ILOW][i] = record.low       
        narrays[IVOL][i] = record.vol
        narrays[IHOLDING][i] = record.holding
        narrays[IMID][i] = (record.close*4 + record.low + record.high)/6
        i += 1
    return narrays

def read_if(filename,extractor=extract_if):
    records = []
    for line in file(filename):
        if len(line.strip()) > 0:
            record = extractor(line)
            if record.time < 1501 and record.time > 845:  #排除错误数据
                records.append(record)
    return records

FPATH = 'D:/work/applications/gcode/wolfox/data/ifuture/'
prefix = 'SF'
IFS = 'RU1011','FU1009','CU1011','CU1009'
SUFFIX = '.txt'

def readp(path,name,extractor=extract_if):
    ifs = {}
    ifs[name] = BaseObject(name=name,transaction=read_if_as_np(path + name + SUFFIX,extractor=extractor))
    prepare_index(ifs[name])
    return ifs

def read1(name,extractor=extract_if):
    ifs = {}
    ifs[name] = BaseObject(name=name,transaction=read_if_as_np(FPATH + prefix + name + SUFFIX,extractor=extractor))
    prepare_index(ifs[name])
    return ifs

def read_ifs(extractor=extract_if):
    ifs = {}
    for ifn in IFS:
        ifs[ifn] = BaseObject(name=ifn,transaction=read_if_as_np(FPATH + prefix + ifn + SUFFIX,extractor=extractor))
        prepare_index(ifs[ifn])
    return ifs

FBASE=10    #只用于macd提高精度，因为是整数运算，再往上就要溢出了

def prepare_index(sif):
    trans = sif.transaction
    
    sif.close = trans[ICLOSE]
    sif.open = trans[IOPEN]
    sif.high = trans[IHIGH]
    sif.low = trans[ILOW]
    sif.vol = trans[IVOL]
    sif.holding = trans[IHOLDING]
    sif.i_cof = sif.i_oof = np.arange(len(sif.close))
    sif.time = trans[ITIME]
    sif.date = trans[IDATE]

    

    sif.diff1,sif.dea1 = cmacd(trans[ICLOSE]*FBASE)
    sif.diff2,sif.dea2 = cmacd(trans[ICLOSE]*FBASE,19,39,15)    
    sif.diff3,sif.dea3 = cmacd(trans[ICLOSE]*FBASE,36,78,27)
    sif.diff5,sif.dea5 = cmacd(trans[ICLOSE]*FBASE,60,130,45)
    sif.diff15,sif.dea15 = cmacd(trans[ICLOSE]*FBASE,180,390,135)
    sif.diff30,sif.dea30 = cmacd(trans[ICLOSE]*FBASE,360,780,270)
    sif.diff60,sif.dea60 = cmacd(trans[ICLOSE]*FBASE,720,1560,540)
    sif.di30,sif.de30 = smacd(trans[ICLOSE]*FBASE,360,780,270)  #计算误差太大，改用非指数版
    sif.di60,sif.de60 = smacd(trans[ICLOSE]*FBASE,720,1560,540)  #计算误差太大，改用非指数版

    sif.macd1 = sif.diff1-sif.dea1
    sif.macd5 = sif.diff5-sif.dea5
    sif.macd15 = sif.diff15-sif.dea15
    sif.macd30 = sif.diff30-sif.dea30    
    sif.macd60 = sif.diff60-sif.dea60    

    sif.ma3 = ma(trans[ICLOSE],3)
    sif.ma5 = ma(trans[ICLOSE],5)
    sif.ma10 = ma(trans[ICLOSE],10)
    sif.ma7 = ma(trans[ICLOSE],7)
    sif.ma13 = ma(trans[ICLOSE],13)    
    sif.ma20 = ma(trans[ICLOSE],20)
    sif.ma30 = ma(trans[ICLOSE],30)
    sif.ma60 = ma(trans[ICLOSE],60)
    sif.ma90 = ma(trans[ICLOSE],90)    
    sif.ma135 = ma(trans[ICLOSE],135)    
    sif.ma270 = ma(trans[ICLOSE],270)        
    sif.atr = atr(trans[ICLOSE]*XBASE,trans[IHIGH]*XBASE,trans[ILOW]*XBASE,20)
    sif.atr2 = atr2(trans[ICLOSE]*XBASE,trans[IHIGH]*XBASE,trans[ILOW]*XBASE,20)    
    sif.xatr = sif.atr * XBASE * XBASE / trans[ICLOSE]
    sif.mxatr = ma(sif.xatr,13)

    sif.sk,sif.sd = skdj(sif.high,sif.low,sif.close)

    sm270 = sif.ma270 - rollx(sif.ma270)
    sif.state_270 = msum(sm270,20)
    sif.state_270s = strend(sif.state_270)

    sm135 = sif.ma135 - rollx(sif.ma135)
    sif.state_135 = msum(sm135,20)
    sif.state_135s = strend(sif.state_135)

    sm60 = sif.ma60 - rollx(sif.ma60)
    sif.state_60 = msum(sm60,20)
    sif.state_60s = strend(sif.state_60)

    sm30 = sif.ma30 - rollx(sif.ma30)
    sif.state_30 = msum(sm30,20)
    sif.state_30s = strend(sif.state_30)

    sif.i_cof5 = np.where(
            gor(gand(trans[ITIME]%5==0,trans[ITIME]%1000 != 900)
                ,gand(trans[ITIME]%10000 == 1459)
            )
        )[0]    #5分钟收盘线,不考虑隔日的因素
    sif.i_oof5 = roll0(sif.i_cof5)+1    
    sif.i_oof5[0] = 0
    sif.close5 = trans[ICLOSE][sif.i_cof5]
    #sif.open5 = rollx(sif.close5)   #open5看作是上一个的收盘价,其它方式对应open和close以及还原的逻辑比较复杂
    sif.open5 = trans[IOPEN][sif.i_oof5]
    #sif.high5 = tmax(trans[IHIGH],5)[sif.i_cof5]
    #sif.low5 = tmin(trans[ILOW],5)[sif.i_cof5]
    sif.high5,sif.low5,sif.vol5 = calc_high_low_vol(trans,sif.i_oof5,sif.i_cof5)
    sif.holding5 = trans[IHOLDING][sif.i_cof5]


    sif.atr5 = atr(sif.close5*XBASE,sif.high5*XBASE,sif.low5*XBASE,20)
    sif.xatr5 = sif.atr5 * XBASE * XBASE / sif.close5
    sif.mxatr5 = ma(sif.xatr5,13)
    sif.xatr5x = np.zeros_like(trans[ICLOSE])
    sif.xatr5x[sif.i_cof5] = sif.xatr5
    sif.xatr5x = extend2next(sif.xatr5x)

    sif.atr5x = np.zeros_like(trans[ICLOSE])
    sif.atr5x[sif.i_cof5] = sif.atr5
    sif.atr5x = extend2next(sif.atr5x)
    

    sif.diff5x,sif.dea5x = cmacd(sif.close5*FBASE)
    sif.diff5x5,sif.dea5x5 = cmacd(sif.close5*FBASE,60,130,45)    

    sif.sdiff5x,sif.sdea5x = np.zeros_like(trans[ICLOSE]),np.zeros_like(trans[ICLOSE])
    sif.sdiff5x[sif.i_cof5] = sif.diff5x
    sif.sdea5x[sif.i_cof5] = sif.dea5x
    sif.sdiff5x=extend2next(sif.sdiff5x)
    sif.sdea5x=extend2next(sif.sdea5x)

    strend_macd5x = strend(sif.diff5x-sif.dea5x)
    sif.smacd5x = np.zeros_like(trans[ICLOSE])
    sif.smacd5x[sif.i_cof5] = strend_macd5x
    sif.smacd5x=extend2next(sif.smacd5x)


    ##3分钟
    sif.i_cof3 = np.where(
            gor(gand((trans[ITIME]%100+1)%3 == 0,trans[ITIME]%1000!=900)
                ,gand(trans[ITIME]%10000 == 1459)
            )
        )[0]    #5分钟收盘线,不考虑隔日的因素
    sif.i_oof3 = roll0(sif.i_cof3)+1    
    sif.i_oof3[0] = 0
    sif.close3 = trans[ICLOSE][sif.i_cof3]
    #sif.open3 = rollx(sif.close3)   #open3看作是上一个的收盘价,其它方式对应open和close以及还原的逻辑比较复杂
    sif.open3 = trans[IOPEN][sif.i_oof3]
    #sif.high3 = tmax(trans[IHIGH],3)[sif.i_cof3]
    #sif.low3 = tmin(trans[ILOW],3)[sif.i_cof3]
    sif.high3,sif.low3,sif.vol3 = calc_high_low_vol(trans,sif.i_oof3,sif.i_cof3)
    sif.holding3 = trans[IHOLDING][sif.i_cof3]


    sif.atr3 = atr(sif.close3*XBASE,sif.high3*XBASE,sif.low3*XBASE,20)
    sif.xatr3 = sif.atr3 * XBASE * XBASE / sif.close3
    sif.mxatr3 = ma(sif.xatr3,13)
    sif.xatr3x = np.zeros_like(trans[ICLOSE])
    sif.xatr3x[sif.i_cof3] = sif.xatr3
    sif.xatr3x = extend2next(sif.xatr3x)

    sif.atr3x = np.zeros_like(trans[ICLOSE])
    sif.atr3x[sif.i_cof3] = sif.atr3
    sif.atr3x = extend2next(sif.atr3x)
    

    sif.diff3x,sif.dea3x = cmacd(sif.close3*FBASE)
    sif.diff3x5,sif.dea3x5 = cmacd(sif.close3*FBASE,60,130,45)    

    sif.sdiff3x,sif.sdea3x = np.zeros_like(trans[ICLOSE]),np.zeros_like(trans[ICLOSE])
    sif.sdiff3x[sif.i_cof3] = sif.diff3x
    sif.sdea3x[sif.i_cof3] = sif.dea3x
    sif.sdiff3x=extend2next(sif.sdiff3x)
    sif.sdea3x=extend2next(sif.sdea3x)

    strend_macd3x = strend(sif.diff3x-sif.dea3x)
    sif.smacd3x = np.zeros_like(trans[ICLOSE])
    sif.smacd3x[sif.i_cof3] = strend_macd3x
    sif.smacd5x=extend2next(sif.smacd3x)

    ##10分钟
    sif.i_cof10 = np.where(
            gor(gand((trans[ITIME]%10) == 0,trans[ITIME]%1000!=900)
                ,gand(trans[ITIME]%10000 == 1459
            )
        ))[0]    #5分钟收盘线,不考虑隔日的因素
    sif.i_oof10 = roll0(sif.i_cof10)+1    
    sif.i_oof10[0] = 0
    sif.close10 = trans[ICLOSE][sif.i_cof10]
    #sif.open10 = rollx(sif.close10)   #open10看作是上一个的收盘价,其它方式对应open和close以及还原的逻辑比较复杂
    sif.open10 = trans[IOPEN][sif.i_oof10]
    #sif.high10 = tmax(trans[IHIGH],10)[sif.i_cof10]
    #sif.low10 = tmin(trans[ILOW],10)[sif.i_cof10]
    sif.high10,sif.low10,sif.vol10 = calc_high_low_vol(trans,sif.i_oof10,sif.i_cof10)
    sif.holding10 = trans[IHOLDING][sif.i_cof10]


    sif.atr10 = atr(sif.close10*XBASE,sif.high10*XBASE,sif.low10*XBASE,20)
    sif.xatr10 = sif.atr10 * XBASE * XBASE / sif.close10
    sif.mxatr10 = ma(sif.xatr10,13)
    sif.xatr10x = np.zeros_like(trans[ICLOSE])
    sif.xatr10x[sif.i_cof10] = sif.xatr10
    sif.xatr10x = extend2next(sif.xatr10x)

    sif.atr10x = np.zeros_like(trans[ICLOSE])
    sif.atr10x[sif.i_cof10] = sif.atr10
    sif.atr10x = extend2next(sif.atr10x)
    

    sif.diff10x,sif.dea10x = cmacd(sif.close10*FBASE)
    sif.diff10x5,sif.dea10x5 = cmacd(sif.close10*FBASE,60,130,45)    

    sif.sdiff10x,sif.sdea10x = np.zeros_like(trans[ICLOSE]),np.zeros_like(trans[ICLOSE])
    sif.sdiff10x[sif.i_cof10] = sif.diff10x
    sif.sdea10x[sif.i_cof10] = sif.dea10x
    sif.sdiff10x=extend2next(sif.sdiff10x)
    sif.sdea10x=extend2next(sif.sdea10x)

    strend_macd10x = strend(sif.diff10x-sif.dea10x)
    sif.smacd10x = np.zeros_like(trans[ICLOSE])
    sif.smacd10x[sif.i_cof10] = strend_macd10x
    sif.smacd5x=extend2next(sif.smacd10x)
    
    #30分钟
    sif.i_cof30 = np.where(gor(
        gand(trans[ITIME]%10000==1459)   
        ,gand(trans[ITIME]%100==0,trans[ITIME]%1000!=900) 
        ,trans[ITIME]%100==30
        ))[0]    #30分钟收盘线,不考虑隔日的因素
    sif.i_oof30 = roll0(sif.i_cof30)+1    
    sif.i_oof30[0] = 0    
    sif.close30 = trans[ICLOSE][sif.i_cof30]
    #sif.open30 = rollx(sif.close30)   #open5看作是上一个的收盘价,其它方式对应open和close以及还原的逻辑比较复杂
    sif.open30 = trans[IOPEN][sif.i_oof30]
    #sif.high30 = tmax(trans[IHIGH],30)[sif.i_cof30]
    #sif.low30 = tmin(trans[ILOW],30)[sif.i_cof30]
    sif.high30,sif.low30,sif.vol30 = calc_high_low_vol(trans,sif.i_oof30,sif.i_cof30)
    sif.holding30 = trans[IHOLDING][sif.i_cof30]


    sif.atr30 = atr(sif.close30*XBASE,sif.high30*XBASE,sif.low30*XBASE,20)
    sif.xatr30 = sif.atr30 * XBASE * XBASE / sif.close30
    sif.mxatr30 = ma(sif.xatr30,13)
    sif.xatr30x = np.zeros_like(trans[ICLOSE])
    sif.xatr30x[sif.i_cof30] = sif.xatr30
    sif.xatr30x = extend2next(sif.xatr30x)

    sif.atr30x = np.zeros_like(trans[ICLOSE])
    sif.atr30x[sif.i_cof30] = sif.atr30
    sif.atr30x = extend2next(sif.atr30x)
    
    sif.diff30x,sif.dea30x = cmacd(sif.close30*FBASE)

    sif.sdiff30x,sif.sdea30x = np.zeros_like(trans[ICLOSE]),np.zeros_like(trans[ICLOSE])
    sif.sdiff30x[sif.i_cof30] = sif.diff30x
    sif.sdea30x[sif.i_cof30] = sif.dea30x
    sif.sdiff30x=extend2next(sif.sdiff30x)
    sif.sdea30x=extend2next(sif.sdea30x)


    sif.i_cof15 = np.where(
                gor(gand(trans[ITIME]%100==0,trans[ITIME]%1000!=900)
                    ,trans[ITIME]%100==15
                    ,trans[ITIME]%100==30
                    ,trans[ITIME]%100==45
                    ,trans[ITIME]%10000 == 1459
                    )
        )[0]    #5分钟收盘线,不考虑隔日的因素
    sif.i_oof15 = roll0(sif.i_cof15)+1
    sif.i_oof15[0] = 0    
    sif.close15 = trans[ICLOSE][sif.i_cof15]
    #sif.open15 = rollx(sif.close15)   #open5看作是上一个的收盘价,其它方式对应open和close以及还原的逻辑比较复杂
    sif.open15 = trans[IOPEN][sif.i_oof15]
    #sif.high15 = tmax(trans[IHIGH],15)[sif.i_cof15] #算上上一个收盘
    #sif.low15 = tmin(trans[ILOW],15)[sif.i_cof15]
    sif.high15,sif.low15,sif.vol15 = calc_high_low_vol(trans,sif.i_oof15,sif.i_cof15)
    sif.holding15 = trans[IHOLDING][sif.i_cof15]


    sif.atr15 = atr(sif.close15*XBASE,sif.high15*XBASE,sif.low15*XBASE,20)
    sif.xatr15 = sif.atr15 * XBASE * XBASE / sif.close15
    sif.mxatr15 = ma(sif.xatr15,13)
    sif.xatr15x = np.zeros_like(trans[ICLOSE])
    sif.xatr15x[sif.i_cof15] = sif.xatr15
    sif.xatr15x = extend2next(sif.xatr15x)

    sif.atr15x = np.zeros_like(trans[ICLOSE])
    sif.atr15x[sif.i_cof15] = sif.atr15
    sif.atr15x = extend2next(sif.atr15x)
    

    sif.diff15x,sif.dea15x = cmacd(sif.close15*FBASE)
    sif.diff15x5,sif.dea15x5 = cmacd(sif.close15*FBASE,60,130,45)    

    sif.sdiff15x,sif.sdea15x = np.zeros_like(trans[ICLOSE]),np.zeros_like(trans[ICLOSE])
    sif.sdiff15x[sif.i_cof15] = sif.diff15x
    sif.sdea15x[sif.i_cof15] = sif.dea15x
    sif.sdiff15x=extend2next(sif.sdiff15x)
    sif.sdea15x=extend2next(sif.sdea15x)


    #60分钟线，每天最后半小时交易也算一小时
    sif.i_cof60 = np.where(gor(
        trans[ITIME]%10000==1459
        ,trans[ITIME]%10000==1400
        ,trans[ITIME]%10000==1100
        ,trans[ITIME]%10000==1000
        ))[0]    #60分钟收盘线,不考虑隔日的因素
    sif.i_oof60 = roll0(sif.i_cof60)+1    
    sif.i_oof60[0] = 0    
    sif.close60 = trans[ICLOSE][sif.i_cof60]
    #sif.open60 = rollx(sif.close60)   #open60看作是上一个的收盘价,其它方式对应open和close以及还原的逻辑比较复杂
    sif.open60 = trans[IOPEN][sif.i_oof60]
    #sif.high60 = tmax(trans[IHIGH],60)[sif.i_cof60]
    #sif.low60 = tmin(trans[ILOW],60)[sif.i_cof60]
    sif.high60,sif.low60,sif.vol60 = calc_high_low_vol(trans,sif.i_oof60,sif.i_cof60)
    sif.holding60 = trans[IHOLDING][sif.i_cof60]


    sif.atr60 = atr(sif.close60*XBASE,sif.high60*XBASE,sif.low60*XBASE,20)
    sif.xatr60 = sif.atr60 * XBASE * XBASE / sif.close60
    sif.mxatr60 = ma(sif.xatr60,13)
    sif.xatr60x = np.zeros_like(trans[ICLOSE])
    sif.xatr60x[sif.i_cof60] = sif.xatr60
    sif.xatr60x = extend2next(sif.xatr60x)

    sif.atr60x = np.zeros_like(trans[ICLOSE])
    sif.atr60x[sif.i_cof60] = sif.atr60
    sif.atr60x = extend2next(sif.atr60x)
    
    sif.diff60x,sif.dea60x = cmacd(sif.close60*FBASE)

    sif.sdiff60x,sif.sdea60x = np.zeros_like(trans[ICLOSE]),np.zeros_like(trans[ICLOSE])
    sif.sdiff60x[sif.i_cof60] = sif.diff60x
    sif.sdea60x[sif.i_cof60] = sif.dea60x
    sif.sdiff60x=extend2next(sif.sdiff60x)
    sif.sdea60x=extend2next(sif.sdea60x)


    sif.i_cofd = np.append(np.nonzero(trans[IDATE]-rollx(trans[IDATE])>0)[0]-1,len(trans[IDATE])-1)
    sif.i_oofd = roll0(sif.i_cofd)+1
    sif.i_oofd[0]=0
    sif.opend = trans[IOPEN][sif.i_oofd]
    sif.closed = trans[ICLOSE][sif.i_cofd]
    sif.highd,sif.lowd,sif.vold = calc_high_low_vol(trans,sif.i_oofd,sif.i_cofd)
    sif.holdingd = trans[IHOLDING][sif.i_cofd]

    sif.atrd = atr(sif.closed*XBASE,sif.highd*XBASE,sif.lowd*XBASE,20)
    sif.xatrd = sif.atrd * XBASE * XBASE / sif.closed
    sif.mxatrd = ma(sif.xatrd,13)
    sif.xatrdx = np.zeros_like(trans[ICLOSE])
    sif.xatrdx[sif.i_cofd] = sif.xatrd
    sif.xatrdx = extend2next(sif.xatrdx)

    sif.atrdx = np.zeros_like(trans[ICLOSE])
    sif.atrdx[sif.i_cofd] = sif.atrd
    sif.atrdx = extend2next(sif.atrdx)

    s30_13 = np.zeros_like(sif.diff1)
    s30_13[sif.i_cof30] = strend2(ma(sif.close30,13))
    sif.state_30_13 = extend2next(s30_13)


def calc_high_low_vol(trans,i_oof,i_cof):
    xhigh = np.zeros_like(i_oof)
    xlow = np.zeros_like(i_oof)
    xvol = np.zeros_like(i_oof)    
    i = 0
    for x,y in zip(i_oof,i_cof):
        xhigh[i] = np.max(trans[IHIGH][x:y+1])
        xlow[i] = np.min(trans[ILOW][x:y+1])
        xvol[i] = np.sum(trans[IVOL][x:y+1])
        i += 1
    return xhigh,xlow,xvol



