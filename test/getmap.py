# -*- coding: utf-8 -*-
import re
from test import bot_osu
from test import bot_sql


min_member = 1  # 一首歌至少有几个人打过，才进入后续推荐指数计算


def infoMap(content):
    if content == '!mapinfo':
        return '倒是告诉我要查哪个图啊'
    check_map = re.match(r'^!mapinfo ([1-9][0-9]*)$', content)
    if check_map:
        bid = int(check_map.group(1))
        map_info = '谱面Bid: %s\n' % bid + bot_osu.getMapInfo(bid, '0', getlength=True)
        if not map_info:
            map_info =  '网络爆炸了,查询地图失败'
        sql = 'SELECT * FROM bpmsg WHERE `bid` = %s ORDER BY `mod` DESC' % bid
        result = bot_sql.select(sql)
        if not result:
            msg = '\n数据库中没有其余详细信息'
        else:
            msg = '\n数据库中有如下信息:\n括号内数据为平均值'
            total_list = list(result)
            i_now = 0
            i_max = len(total_list)
            # 数据库返回的每一条信息中,0:uid,1:bp_rank,2:bid,3:mod,4:score_pp,5:score_acc,6:suggest_mod,7:suggest_pp,8:user_pp
            user_last = total_list[0][8]
            user_top = total_list[0][8]
            pp_last = total_list[0][4]
            pp_top = total_list[0][4]
            acc_last = total_list[0][5]
            acc_top = total_list[0][5]
            user_total = total_list[0][8]
            pp_total = total_list[0][4]
            acc_total = total_list[0][5]
            user_num = 1
            while True:
                i_now = i_now + 1
                if i_now != i_max and total_list[i_now][3] == total_list[i_now-1][3]:
                    if user_last > total_list[i_now][8]:
                        user_last = total_list[i_now][8]
                    if user_top < total_list[i_now][8]:
                        user_top = total_list[i_now][8]
                    if acc_last > total_list[i_now][5]:
                        acc_last = total_list[i_now][5]
                    if acc_top < total_list[i_now][5]:
                        acc_top = total_list[i_now][5]
                    if pp_last > total_list[i_now][4]:
                        pp_last = total_list[i_now][4]
                    if pp_top < total_list[i_now][4]:
                        pp_top = total_list[i_now][4]
                    user_total = user_total + total_list[i_now][8]
                    user_num = user_num + 1
                    pp_total = pp_total + total_list[i_now][4]
                    acc_total = acc_total + total_list[i_now][5]
                else:
                    msg = msg + '\n【%s】共%s条记录' % (bot_osu.getMod(total_list[i_now-1][3]), user_num)
                    msg = msg + '\n玩家%s-%s (%s)' % (user_last, user_top, int(user_total / user_num))
                    msg = msg + '\n成绩%s-%s (%s)' % (pp_last, pp_top, int(pp_total / user_num))
                    acc_msg = '\n准确度%.2f-%.2f (%.1f)' % (acc_last, acc_top, (acc_total / user_num))
                    acc_msg = acc_msg.replace('100.00', '100')
                    acc_msg = acc_msg.replace('100.0', '100')
                    msg = msg + acc_msg
                    if i_now == i_max:
                        break
                    user_last = total_list[i_now][8]
                    user_top = total_list[i_now][8]
                    pp_last = total_list[i_now][4]
                    pp_top = total_list[i_now][4]
                    acc_last = total_list[i_now][5]
                    acc_top = total_list[i_now][5]
                    user_total = total_list[i_now][8]
                    pp_total = total_list[i_now][4]
                    acc_total = total_list[i_now][5]
                    user_num = 1
        return map_info + msg


def searchMap(user_name, mod_name):
    suggest_num = 50
    mod_id = modIdCal(mod_name)
    if mod_id == -1:
        return '非法Mod输入'
    (uid, name, pp, pc, tth, acc, sec) = bot_osu.getUserInfo(user_name, '0')
    if not uid:
        return '用户查询出错,请稍后再试'
    if pp > 15000 or pp < 500:
        return '本推荐只支持pp在500-15000的玩家'
    bp_result = bot_osu.getUserBp(uid, '0')
    if not bp_result:
        return '用户bp查询出错,请稍后再试'
    bp_bid = []
    for bp in bp_result:
        bp_bid.append(int(bp['beatmap_id']))
    pp_min = int(pp - 150)
    pp_max = int(pp + 350)
    if mod_id == -999:
        sql = 'SELECT * FROM bpmsg WHERE `user_pp` > %d AND `user_pp` < %d ORDER BY bid DESC' % \
              (pp_min, pp_max)
    else:
        sql = 'SELECT * FROM bpmsg WHERE `user_pp` > %d AND `user_pp` < %d AND `suggest_mod` = %d ORDER BY bid DESC' % \
              (pp_min, pp_max, mod_id)
    result = bot_sql.select(sql)
    total_list = list(result)
    suggest_list = []
    i_max = len(total_list)
    i_now = 0
    # 数据库返回的每一条信息中,0:uid,1:bp_rank,2:bid,3:mod,4:score_pp,5:score_acc,6:suggest_mod,7:suggest_pp,8:user_pp
    while True:
        if i_now > i_max - min_member:  # 查询到头的时候，结束
            break
        if total_list[i_now][2] in bp_bid:  # 如果这张图已经打过了，跳过
            i_now = i_now + 1
            continue
        if total_list[i_now][2] != total_list[i_now + min_member - 1][2]:  # 如果这张图打的人少于n个，跳过
            i_now = i_now + 1
            continue
        for j in range(i_now + min_member - 1, i_max):  # 至少有n个人打了一张你没打过的图，开始计算
            if j == i_max - 1 or total_list[i_now][2] != total_list[j + 1][2]:
                e_pp = 0  # 期望pp
                e_acc = 0  # 期望acc
                e_good = 0  # 推荐指数
                for songs in range(i_now, j + 1):
                    e_pp = e_pp + total_list[songs][7]
                    e_acc = e_acc + total_list[songs][5]
                    e_good = e_good + 50 - total_list[songs][1]
                e_pp = int(e_pp / (j - i_now + 1))
                e_acc = '%.1f' % (e_acc / (j - i_now + 1))
                if e_acc == '100.0':
                    e_acc = '100'
                suggest_list.append(
                    {'bid': total_list[i_now][2], 'mod': total_list[i_now][6], 'pp': e_pp, 'acc': e_acc, 'good': e_good})
                i_now = j  # 处理完毕后，索引直接跳转到相同歌曲的最后那一位
                break
        i_now = i_now + 1
    suggest_list.sort(key=lambda x: x['good'], reverse=True)
    if not suggest_list:
        msg = '你太强了, bot不知道该给你推荐什么图才合适'
    else:
        msg = '%s的推荐图如下:\n序号, Bid, Mod, 参考pp, 参考acc, 推荐指数' % name
    a = 1
    for i in range(min(suggest_num, len(suggest_list))):
        mod_name = bot_osu.getMod(suggest_list[i]['mod'])
        msg = msg + '\n%02d,  %s,  %s,  %s,  %s,  %s' % (
        a, suggest_list[i]['bid'], mod_name, suggest_list[i]['pp'], suggest_list[i]['acc'], suggest_list[i]['good'])
        a = a + 1
    return msg


# 输入mod字符串,进行模糊转化，并输出转化后的modid
def modIdCal(mod_name):
    if mod_name == 'None' or mod_name == 'none' or mod_name == 'NONE':
        return 0
    if not mod_name:
        return -999
    if len(mod_name)%2 != 0:
        return -1
    num = int(len(mod_name)/2)
    mod_id = 0
    mod_pick = [0,0,0,0,0,0]
    for i in range(num):
        get = mod_name[2*i: 2*i+2]
        if get == 'hd' or get == 'HD':
            if mod_pick[0] == 0:
                mod_pick[0] = 1
            else:
                return -1
        elif get == 'nf' or get == 'NF' or get == 'sd' or get == 'SD' or get == 'pf' or get == 'PF':
            if mod_pick[1] == 0:
                mod_pick[1] = 1
            else:
                return -1
        elif get == 'so' or get == 'SO':
            if mod_pick[2] == 0:
                mod_pick[2] = 1
            else:
                return -1
        elif get == 'nc' or get == 'NC'or get == 'dt' or get == 'DT':
            if mod_pick[3] == 0:
                mod_pick[3] = 1
            else:
                return -1
            mod_id = mod_id + 64
        elif get == 'ht' or get == 'HT':
            if mod_pick[3] == 0:
                mod_pick[3] = 1
            else:
                return -1
            mod_id = mod_id + 256
        elif get == 'hr' or get == 'HR':
            if mod_pick[4] == 0:
                mod_pick[4] = 1
            else:
                return -1
            mod_id = mod_id + 16
        elif get == 'ez' or get == 'EZ':
            if mod_pick[4] == 0:
                mod_pick[4] = 1
            else:
                return -1
            mod_id = mod_id + 2
        elif get == 'fl' or get == 'FL':
            if mod_pick[5] == 0:
                mod_pick[5] = 1
            else:
                return -1
            mod_id = mod_id + 1024
        else:
            return -1
    return mod_id
