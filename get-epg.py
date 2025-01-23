#-*- coding: utf-8 -*-                                                                                                                                  
import re
import pytz
import requests
from lxml import html
from datetime import datetime, timezone, timedelta

tz = pytz.timezone('Asia/Shanghai')

cctv_channel = ['cctv1','cctv2','cctv3','cctv4','cctv5','cctv5plus','cctv6',\
    'cctv7','cctv8','cctvjilu','cctv10','cctv11','cctv12','cctv13','cctvchild', \
        'cctv15','cctv16','cctv17','cctv4k','cctv8k']

def transformChannelName(input):
    '''
    这里做一些特殊命名的转换
    '''
    if input == 'CCTV-4 (亚洲)' :
        return 'CCTV-4 中文国际'
    elif input == 'CCTV-4K':
        return 'CCTV-4K 超高清'
    elif input == 'CCTV-8K':
        return 'CCTV-8K 超高清'
    return input

def getChannelCNTV(fhandle, channelID):
    '''
    通过央视cntv接口，获取央视，和上星卫视的节目单，写入同目录下 guide.xml 文件，文件格式符合xmltv标准
    接口返回的json转换成dict后类似如下
    {'cctv1': {'isLive': '九九第1集', 'liveSt': 1535264130, 'channelName': 'CCTV-1 综合', 'program': [{'t': '生活提示2018-187', 'st': 1535215320, 'et': 1535215680, 'showTime': '00:42', 'eventType': '', 'eventId': '', 'duration': 360}

    Args:
        fhandle,文件处理对象，用于后续调用，直接写入xml文件
        channelID,电视台列表，list格式，可以批量一次性获取多个节目单

    Return:
        None,直接写入xml文件
    '''

    #change channelID list to str cids
    cids = ''
    for x in channelID:
        cids = cids + x + ','

    epgdate = datetime.now(tz).strftime('%Y%m%d')
    session = requests.Session()
    api = "https://api.cntv.cn/epg/epginfo?c=%s&d=%s" % (cids, epgdate)
    epgdata = session.get(api).json()

    for n in range(len(channelID)):
        program = epgdata[channelID[n]]['program']

        #write channel id info
        fhandle.write('    <channel id="%s">\n' % channelID[n])
        fhandle.write('        <display-name lang="cn">%s</display-name>\n' % transformChannelName(epgdata[channelID[n]]['channelName']))
        fhandle.write('    </channel>\n')

def getChannelEPG(fhandle, channelID):

    #change channelID list to str cids
    cids = ''
    for x in channelID:
        cids = cids + x + ','

    epgdate = datetime.now(tz).strftime('%Y%m%d')
    epgdate2 = (datetime.now(tz) + timedelta(days=1)).strftime('%Y%m%d')
    epgdate3 = (datetime.now(tz) + timedelta(days=2)).strftime('%Y%m%d')
    session = requests.Session()
    api = "https://api.cntv.cn/epg/epginfo?c=%s&d=%s" % (cids, epgdate)
    api2 = "https://api.cntv.cn/epg/epginfo?c=%s&d=%s" % (cids, epgdate2)
    api3 = "https://api.cntv.cn/epg/epginfo?c=%s&d=%s" % (cids, epgdate3)
    epgdata = session.get(api).json()
    epgdata2 = session.get(api2).json()
    epgdata3 = session.get(api3).json()

    for n in range(len(channelID)):
        program = epgdata[channelID[n]]['program']
        for detail in program:
            #write programe
            st = (datetime.fromtimestamp(detail['st'], timezone.utc) + timedelta(hours=8)).strftime('%Y%m%d%H%M%S')
            et = (datetime.fromtimestamp(detail['et'], timezone.utc) + timedelta(hours=8)).strftime('%Y%m%d%H%M%S')

            fhandle.write('    <programme start="%s" stop="%s" channel="%s">\n' % (st, et, channelID[n]))
            fhandle.write('        <title lang="zh">%s</title>\n' % detail['t'])
            fhandle.write('    </programme>\n')

        program2 = epgdata2[channelID[n]]['program']
        for detail2 in program2:
            #write programe
            st = (datetime.fromtimestamp(detail2['st'], timezone.utc) + timedelta(hours=8)).strftime('%Y%m%d%H%M%S')
            et = (datetime.fromtimestamp(detail2['et'], timezone.utc) + timedelta(hours=8)).strftime('%Y%m%d%H%M%S')

            fhandle.write('    <programme start="%s" stop="%s" channel="%s">\n' % (st, et, channelID[n]))
            fhandle.write('        <title lang="zh">%s</title>\n' % detail2['t'])
            fhandle.write('    </programme>\n')

        program3 = epgdata3[channelID[n]]['program']
        for detail3 in program3:
            #write programe
            st = (datetime.fromtimestamp(detail3['st'], timezone.utc) + timedelta(hours=8)).strftime('%Y%m%d%H%M%S')
            et = (datetime.fromtimestamp(detail3['et'], timezone.utc) + timedelta(hours=8)).strftime('%Y%m%d%H%M%S')

            fhandle.write('    <programme start="%s" stop="%s" channel="%s">\n' % (st, et, channelID[n]))
            fhandle.write('        <title lang="zh">%s</title>\n' % detail3['t'])
            fhandle.write('    </programme>\n')            

with open('guide.xml','w', encoding='utf-8') as fhandle: # 参数 w 表示覆盖，追加用 at (追加+文本)
    fhandle.write('<?xml version="1.0" encoding="utf-8" ?>\n')
    fhandle.write('<tv generator-info-name="frankwuzp" generator-info-url="https://github.com/frankwuzp/iptv-cn">\n')
    getChannelCNTV(fhandle, cctv_channel)
    getChannelEPG(fhandle, cctv_channel)
    fhandle.write('</tv>')
