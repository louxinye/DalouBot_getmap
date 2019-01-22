# -*- coding: utf-8 -*-
# osu相关系统
import requests
import json


osu_api_key = '7f2f84a280917690158a6ea1f7a72b7e8374fbf9'
headers = {
    'Accept' : 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
    'Accept-Language' : 'zh-CN,zh;q=0.8',
    'Cache-Control': 'max-age=0',
    'Upgrade-Insecure-Requests' : '1',
    'User-Agent': 'Mozilla/5.0 (Linux; Android 6.0; Nexus 5 Build/MRA58N) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/55.0.2883.87 Mobile Safari/537.36'
}
bp_list = []


# 输入用户名或uid(此时需要指明type_mode为id)，输出确切的用户信息
def getUserInfo(osu_name, osu_mode, type_mode='string'):
    url = 'https://osu.ppy.sh/api/get_user?k=%s&u=%s&type=%s&m=%s&limit=1' % (osu_api_key, osu_name, type_mode, osu_mode)
    res = getUrl(url)
    if not res:
        return 0, 0, 0, 0, 0, 0, 0
    result = json.loads(res.text)
    if len(result) == 0:
        return 0, 0, 0, 0, 0, 0, 0
    else:
        uid = result[0]['user_id']
        name = result[0]['username']
        pp = float(valueChange(result[0]['pp_raw']))
        pc = int(valueChange(result[0]['playcount']))
        tth = int(valueChange(result[0]['count300'])) + int(valueChange(result[0]['count100'])) + int(valueChange(result[0]['count50']))
        acc = float(valueChange(result[0]['accuracy']))
        sec = int(valueChange(result[0]['total_seconds_played']))
        return uid, name, pp, pc, tth, acc, sec


# 输入uid，输出bp前50
def getUserBp(uid, osu_mode, max_num=50):
    url = 'https://osu.ppy.sh/api/get_user_best?k=%s&u=%s&type=id&m=%s&limit=%s' % (osu_api_key, uid, osu_mode, max_num)
    res = getUrl(url)
    if not res:
        return []
    result = json.loads(res.text)
    if len(result) == 0:
        return []
    else:
        return result


# 输入bid，输出图的名字难度和长度(此时需要指明getlength为True)
def getMapInfo(bid, mode, getDiff=True, getlength=False):
    url = 'https://osu.ppy.sh/api/get_beatmaps?k=%s&b=%s&m=%s&limit=1' % (osu_api_key, bid, mode)
    res = getUrl(url)
    if not res:
        return 0
    result = json.loads(res.text)
    if len(result) == 0:
        msg = '不存在这张图'
    else:
        msg = '%s - %s [%s]' % (result[0]['artist'], result[0]['title'], result[0]['version'])
        if getDiff:
            msg = msg + '\n难度: % .2f(未计算mod)' % float(result[0]['difficultyrating'])
        if getlength:
            length = getLength(int(result[0]['total_length']))
            msg = msg + '\n长度: %s' % length
    return msg


# 输入uid，bid，输出此人打这图的pp
def getMapPlay(uid, bid, mode):
    url = 'https://osu.ppy.sh/api/get_scores?k=%s&b=%s&u=%s&type=id&m=%s&limit=1' % (osu_api_key, bid, uid, mode)
    res = getUrl(url)
    if not res:
        return 0
    result = json.loads(res.text)
    if len(result) == 0:
        return 0
    else:
        pp = result[0]['pp']
        return pp


def getUserRecent(uid, mode, max_num=20):
    url = 'https://osu.ppy.sh/api/get_user_recent?k=%s&u=%s&type=id&m=%s&limit=%s' % (osu_api_key, uid, mode, max_num)
    res = getUrl(url)
    if not res:
        return []
    result = json.loads(res.text)
    if not result:
        return []
    else:
        return result


# request请求
def getUrl(url):
    try:
        res = requests.get(url=url, headers=headers, params=None, timeout=3)
        return res
    except requests.exceptions.RequestException:
        return 0


# 评分转化
def getRank(content):
    if content == 'X' or content == 'XH':
        msg = 'SS'
    elif content == 'SH':
        msg = 'S'
    else:
        msg = content
    return msg


# acc计算
def getAcc(num_33, num_22, num_11, num_00, type='string'):
    num_300 = int(num_33)
    num_100 = int(num_22)
    num_50 = int(num_11)
    num_0 = int(num_00)
    total = 6 * (num_300 + num_100 + num_50 + num_0)
    real = 6 * num_300 + 2 * num_100 + num_50
    if total > 0:
        acc = real / total
        if type == 'float':
            return acc
        msg = '%.2f' % (acc * 100)
    else:
        if type == 'float':
            return -1
        msg = '???'
    return msg


# 将mod数字变成字符串
def getMod(mod_id):
    mod = int(mod_id)
    mod_list = ['NF', 'EZ', '', 'HD', 'HR', 'SD', 'DT', 'RL', 'HT', 'NC', 'FL', 'AT', 'SO', 'AP', 'PF',
                '4K', '5K', '6K', '7K', '8K', 'FI', 'RD', 'LM', '', '9K', '10K', '1K', '2K', '3K']
    choose = []
    msg = ''
    for i in range(28, -1, -1):
        if mod >= 2**i:
            choose.append(mod_list[i])
            mod = mod - 2**i
            if mod_list[i] == 'NC':
                mod = mod - 64
            if mod_list[i] == 'PF':
                mod = mod - 32
    num = len(choose)
    for i in range(num-1, -1, -1):
        msg = msg + '%s' % choose[i]
    if not msg:
        msg = 'None'
    return msg


# mod增益计算
def getMultiply(mod_id, EZbuff=1, Mtype=1):
    result = 1
    mod_list = []
    mods = getMod(mod_id)
    if mods == 'None':
        return result, mod_list
    num = len(mods)//2
    for i in range(num):
        get = mods[2*i: 2*i+2]
        mod_list.append(get)
        if get == 'NF':
            result = result * 0.5
        elif get == 'EZ':
            result = result * 0.5 * EZbuff
        elif get == 'HT':
            result = result * 0.3
        elif get == 'HR':
            result = result * (1.06 if Mtype==1 else 1.12)
        elif get == 'SD' or get == 'PF':
            pass
        elif get == 'DT' or get == 'NC':
            result = result * (1.12 if Mtype==1 else 1.2)
        elif get == 'HD':
            result = result * 1.06
        elif get == 'FL':
            result = result * 1.12
        elif get == 'SO':
            result = result * 0.9
    return result, mod_list


# 将秒转化为时分秒结构
def getLength(len):
    if len < 1:
        msg = '算不出来'
    else:
        if len > 3599:
            hour = len // 3600
            rest = len % 3600
            minute = rest // 60
            rest = rest % 60
            msg = '%s小时%s分%s秒' % (hour, minute, rest)
        elif len > 59:
            minute = len // 60
            rest = len % 60
            msg = '%s分%s秒' % (minute, rest)
        else:
            msg = '%s秒' % len
    return msg


# 打印mode
def getMode(mode_id):
    if mode_id == '0' or mode_id == 0:
        msg = 'std'
    elif mode_id == '1' or mode_id == 1:
        msg = 'taiko'
    elif mode_id == '2' or mode_id == 2:
        msg = 'ctb'
    elif mode_id == '3' or mode_id == 3:
        msg = 'mania'
    else:
        msg = 'unknown'
    return msg


# 将null转化为字符0
def valueChange(a):
    if not a:
        return '0'
    else:
        return a
