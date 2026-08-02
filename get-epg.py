import pytz
import requests
from datetime import datetime, timezone, timedelta

tz = pytz.timezone('Asia/Shanghai')

cctv_channel = ['cctv1','cctv2','cctv3','cctv4','cctv5','cctv5plus','cctv6',\
    'cctv7','cctv8','cctvjilu','cctv10','cctv11','cctv12','cctv13','cctvchild', \
        'cctv15','cctv16','cctv17','cctv4k','cctv8k','dongfang','jiangsu','zhejiang','hunan', \
        'cetv1','cetv2','cetv3','cetv4','btv1','btvjishi','dongfang', \
        'hunan','shandong','zhejiang','jiangsu','guangdong','dongnan','anhui', \
        'gansu','liaoning','travel','neimenggu','ningxia','qinghai','xiamen', \
        'yunnan','chongqing','jiangxi','shan1xi','shan3xi','shenzhen','sichuan','tianjin', \
        'guangxi','guizhou','hebei','henan','heilongjiang','hubei','jilin', \
        'yanbian','xizang','xinjiang','bingtuan','btvchild','gaoerfu','sdetv']

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

def escape_xml_special_chars(text):
    '''
    转义XML中的特殊字符
    '''
    text = text.replace('&', '&amp;')
    text = text.replace('<', '&lt;')
    text = text.replace('>', '&gt;')
    text = text.replace('"', '&quot;')
    text = text.replace("'", '&apos;')
    return text

BATCH_SIZE = 20

def fetch_epg(session, channelID, epgdate):
    '''
    分批请求央视EPG接口。该接口对单次请求的频道数量有限制（约50个），
    超出会返回 {"errcode":"1001","msg":"params error"}，
    因此按 BATCH_SIZE 分批拉取并合并结果。
    '''
    merged = {}
    for i in range(0, len(channelID), BATCH_SIZE):
        batch = channelID[i:i + BATCH_SIZE]
        api = "https://api.cntv.cn/epg/epginfo?c=%s&d=%s" % (','.join(batch), epgdate)
        resp = session.get(api, timeout=30)
        resp.raise_for_status()
        data = resp.json()
        if isinstance(data, dict) and 'errcode' in data:
            raise RuntimeError('CCTV EPG API error: %s %s' % (data.get('errcode'), data.get('msg')))
        merged.update(data)
    return merged

def write_programmes(fhandle, channel, epg):
    '''
    将单个频道一天的节目写入xml文件
    '''
    for detail in epg.get('program', []):
        #写节目
        st = (datetime.fromtimestamp(detail['st'], timezone.utc) + timedelta(hours=0)).strftime('%Y%m%d%H%M%S')
        et = (datetime.fromtimestamp(detail['et'], timezone.utc) + timedelta(hours=0)).strftime('%Y%m%d%H%M%S')

        fhandle.write('    <programme start="%s" stop="%s" channel="%s">\n' % (st, et, channel))
        fhandle.write('        <title lang="zh">%s</title>\n' % escape_xml_special_chars(detail.get('t', '')))
        fhandle.write('    </programme>\n')

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

    epgdate = datetime.now(tz).strftime('%Y%m%d')
    session = requests.Session()
    epgdata = fetch_epg(session, channelID, epgdate)

    for ch in channelID:
        if ch not in epgdata:
            print('skip missing channel:', ch)
            continue
        #write channel id info
        fhandle.write('    <channel id="%s">\n' % ch)
        fhandle.write('        <display-name lang="cn">%s</display-name>\n' % escape_xml_special_chars(transformChannelName(epgdata[ch]['channelName'])))
        fhandle.write('    </channel>\n')

def getChannelEPG(fhandle, channelID):

    epgdate = datetime.now(tz).strftime('%Y%m%d')
    epgdate2 = (datetime.now(tz) + timedelta(days=1)).strftime('%Y%m%d')
    epgdate3 = (datetime.now(tz) + timedelta(days=2)).strftime('%Y%m%d')
    session = requests.Session()
    epgdata = fetch_epg(session, channelID, epgdate)
    epgdata2 = fetch_epg(session, channelID, epgdate2)
    epgdata3 = fetch_epg(session, channelID, epgdate3)

    for ch in channelID:
        for epg in (epgdata, epgdata2, epgdata3):
            if ch not in epg:
                print('skip missing channel:', ch)
                continue
            write_programmes(fhandle, ch, epg[ch])

channels = list(dict.fromkeys(cctv_channel)) # 去掉列表中的重复频道
with open('guide.xml','w', encoding='utf-8') as fhandle: # 参数 w 表示覆盖，追加用 at (追加+文本)
    fhandle.write('<?xml version="1.0" encoding="utf-8" ?>\n')
    fhandle.write('<tv generator-info-name="frankwuzp" generator-info-url="https://github.com/frankwuzp/iptv-cn">\n')
    getChannelCNTV(fhandle, channels)
    getChannelEPG(fhandle, channels)
    fhandle.write('</tv>')
