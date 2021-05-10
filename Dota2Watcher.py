import json, dota2api, socket, re, threading, hashlib, time, random, string, requests
from random import randint
from urllib.parse import quote
# 引入内容数据
from Content import HEROES_LIST_CHINESE, WIN_NEGATIVE, WIN_POSTIVE, LOSE_NEGATIVE, LOSE_POSTIVE, robot_at_response, Tips_Response
from UserContent import GROUPID, MYQQID, USER_DICT, steamapi

# http代理端口
port = 5789
# http返回端口
host,hport = '', 8789

# steamapi
api = dota2api.Initialise(steamapi, raw_mode=True)

# 1. 实现qq登录，qq群聊消息发送

# 登录实现机制源于go-cqhttp --   https://github.com/Mrs4s/go-cqhttp

# 帮助 https://docs.go-cqhttp.org/guide/quick_start.html
# 操作api  https://docs.go-cqhttp.org/api/

# 发送私聊
def send_private_msg(uid, msg):
    r = requests.get('http://127.0.0.1:%s/send_private_msg?user_id=%s&message=%s' %(port,uid, msg))
    return r

# 发送特殊私聊
def send_private_rawmsg(uid, msg):
    r = requests.get('http://127.0.0.1:%s/send_private_msg?user_id=%s&message=%s' %(port,uid, msg))
    return r

# 发送群聊
def send_group_msg(gid, msg):
    r = requests.get('http://127.0.0.1:%s/send_group_msg?group_id=%s&message=%s' %(port,gid, msg))
    return r

# 发送特殊群聊

def send_group_rawmsg(gid, msg):
    r = requests.get('http://127.0.0.1:%s/send_group_msg?group_id=%s&message=%s' %(port,gid, msg))
    return r

# 撤回消息，暂时无效
def back_msg(mid):
    r = requests.get('http://127.0.0.1:%s/delete_msg?message_id=%s' %(port,mid))
    

# 获取上一把比赛id
def get_last_match_id_by_userid(uid):
    return api.get_match_history(account_id=uid)['matches'][0]['match_id']

def get_match_id_by_userid(uid, num=5):
    mids = []
    for n in range(num):
        mids.append(api.get_match_history(account_id=uid)['matches'][n]['match_id'])
    return mids

# 获取比赛战绩
def get_match_detail(mid, uid):
    data = api.get_match_details(match_id=mid)
    if data:
        radiant_win = data['radiant_win']
        match_detail = [data['game_mode'], data['lobby_type'], data['radiant_score'], data['dire_score']]
        for p in data['players']:
            if p['account_id'] == int(uid):
                # print('ok')
                person_detail = [p['hero_id'], [p['item_0'], p['item_1'],p['item_2'],p['item_3'],p['item_4'],p['item_5']], p['kills'], p['deaths'], p['assists'], p['hero_damage']]
                return [(p['player_slot']<5)==radiant_win, match_detail, person_detail]
        else:
            print('未知原因1')
            return 0
    else:
        print(uid,'获取比赛战绩失败, 编号为',mid )
        return 0

# 比赛数据处理，亮点提取
def check_match_detail(mdata):
    iswin = mdata[0]

    if mdata[1][1] == 7:
        if mdata[1][0] == 22:
            game_mode = '天梯ap'
        elif mdata[1][0] == 3:
            game_mode = '天梯rd'
        else:
            print('没见过的模式', mdata)
            return 0
    elif mdata[1][1] == 0:
        if mdata[1][0] == 18:
            game_mode = '技能征召'
        elif mdata[1][0] == 22:
            game_mode = '匹配ap'
        elif mdata[1][0] == 3:
            game_mode = '匹配rd'
        else:
            print('没见过的模式', mdata)
            return 0
    else:
        print('没见过的模式', mdata)
        return 0
    if mdata[2][3] != 0:
        kda = round((mdata[2][2] + mdata[2][4])/mdata[2][3], 1)
    else:
        kda = mdata[2][2] + mdata[2][4]

    # 情绪分类， 阴阳怪气语录和表情相关
    if mdata[0]:
        if kda>3:
            tauntList = WIN_POSTIVE
            faceid = 2
        else :
            tauntList = WIN_NEGATIVE
            faceid = 5
    else:
        if kda>2:
            tauntList = LOSE_POSTIVE
            faceid = 18
        else :
            tauntList = LOSE_NEGATIVE
            faceid = 36

    tips = []   # 特殊物品， 暴走，超神， 人头占比全队， 输出占比全队。
    return [mdata, iswin, game_mode, kda, tauntList, faceid, tips]

# 比赛推送~
def match_push(mid, uid):
    mdata = get_match_detail(mid, uid)
    if not mdata:
        return 0
    cdata = check_match_detail(mdata)
    if not cdata:
        return 0
    content1 = '[CQ:at,qq=%s] %s上一把%s比赛中使用的 %s %s[CQ:face,id=%s]' \
               %(USER_DICT[int(uid)]['qq'], USER_DICT[int(uid)]['nickname'],cdata[2],
                 HEROES_LIST_CHINESE[cdata[0][2][0]], cdata[4][randint(0,len(cdata[4])-1)], cdata[5])
    content2 = '最终战绩为%s杀%s死%s助攻，kda为%s。'%(cdata[0][2][2], cdata[0][2][3], cdata[0][2][4], cdata[3])

    # send_private_rawmsg(MYQQID, content1+content2)
    send_group_msg(GROUPID, content1+content2)
    return 1

# dota2监听函数
def dota2_listen():
    # 静默启动
    with open('match_log.json','r') as f:
        match_log = json.loads(f.read())
    # for uid, mid in match_log.items():
    #     nowmid = get_last_match_id_by_userid(uid)
    #     if nowmid and nowmid != match_log[uid]:
    #         # 更新 match_log
    #         match_log[uid] = nowmid
    # print('静默启动完成')
    # 静默启动完成

    # 实时监测 每2分钟
    while(1):
        for uid, mid in match_log.items():
            nowmid = get_last_match_id_by_userid(uid)
            if  nowmid != match_log[uid]:
                # 检测到新比赛
                print(uid, 'have new match !')
                match_push(nowmid, uid)
                # 更新 match_log
                match_log[uid] = nowmid
        # 写入文件
        with open('match_log.json', 'w') as f:
            f.write(json.dumps(match_log))
        print('等待2分钟...',time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(time.time())))
        time.sleep(120)



# 语录 及 语录权限 控制函数
def load_talk_dict():
    with open('talk_dict.json', 'r', encoding='utf-8') as f:
        talk_dict = json.loads(f.read())
    return talk_dict

def save_talk_dict(dict):
    with open('talk_dict.json', 'w', encoding='utf-8') as f:
        f.write(json.dumps(dict))

#
def add_talk_dict(key, value):
    dict = load_talk_dict()
    if key not in dict.keys():
        dict[key] = [value]
    else:
        dict[key].append(value)
    save_talk_dict(dict)
    print('add', key)

def del_talk_dict(key):
    dict = load_talk_dict()
    dict.pop(key)
    save_talk_dict(dict)
    print('del',key)

def update_talk_dict1(dict):
    for k, v in dict.items():
        dict[k] = [v]
    return dict

# def mod_talk_dict(key, value):
#     dict = load_talk_dict()
#     dict[key] = value
#     save_talk_dict(dict)
#     print('mod', key)


# // 管理员权限 对于语录列表增删改， 对于语录权限列表增删
# // 用户权限 对于 语录列表 增， 不可操作语录权限列表。
def load_user_right():
    with open('user_right.json', 'r', encoding='utf-8') as f:
        user_right = json.loads(f.read())
    return user_right

def save_user_right(dict):
    with open('user_right.json', 'w', encoding='utf-8') as f:
        f.write(json.dumps(dict))

def check_user_right(uid):
    dict = load_user_right()
    if uid in dict['admin']:
        return 2
    elif uid in dict['user']:
        return 1
    else :
        return 0

def add_user_right(uid):
    dict = load_user_right()
    dict['user'].append(int(uid))
    save_user_right(dict)
    print('add', uid)

def del_user_right(uid):
    dict = load_user_right()
    dict['user'].remove(int(uid))
    save_user_right(dict)
    print('del', uid)



# 青云客聊天机器人api
def talk_robot1(msg):
    try:
        r = requests.get('http://api.qingyunke.com/api.php?key=free&appid=0&msg='+msg)
        return r.json()['content']
    except:
        return ''

def curlmd5(src):
    m = hashlib.md5(src.encode('UTF-8'))
    # 将得到的MD5值所有字符转换成大写
    return m.hexdigest().upper()

def get_params(plus_item):
    # 请求时间戳（秒级），用于防止请求重放（保证签名5分钟有效）
    t = time.time()
    time_stamp=str(int(t))
    # 请求随机字符串，用于保证签名不可预测
    nonce_str = ''.join(random.sample(string.ascii_letters + string.digits, 10))
    # 应用标志，这里修改成自己的id和key
    app_id = '2167970920'
    app_key = 'pMCDRiEO9SR6xKfJ'
    params = {'app_id':app_id,
              'question':plus_item,
              'time_stamp':time_stamp,
              'nonce_str':nonce_str,
              'session':'10000'}
    sign_before = ''
    # 要对key排序再拼接
    for key in sorted(params):
        # 键值拼接过程value部分需要URL编码，URL编码算法用大写字母，例如%E8。quote默认大写。
        sign_before += '{}={}&'.format(key,quote(params[key], safe=''))
    # 将应用密钥以app_key为键名，拼接到字符串sign_before末尾
    sign_before += 'app_key={}'.format(app_key)
    # 对字符串sign_before进行MD5运算，得到接口请求签名
    sign = curlmd5(sign_before)
    params['sign'] = sign
    return params

def talk_robot2(plus_item):  
    try:
        # 聊天的API地址  
        url = "https://api.ai.qq.com/fcgi-bin/nlp/nlp_textchat"    
        # 获取请求参数
        plus_item = plus_item.encode('utf-8')
        payload = get_params(plus_item)  
        r = requests.post(url,data=payload)  
        return r.json()["data"]["answer"]
    except:
        return ''

# robot_func_list = [talk_robot2, talk_robot2]

# qq机器人监听函数
def qq_listen():
    # 1.2 监听qq消息，实现自动回复
    listen_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    listen_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    listen_socket.bind((host, hport))
    listen_socket.listen(1)
    print('Serving HTTP on port %s ...' % hport)
    # send_group_rawmsg(522201349, '爷上线了')
    while(1):
        client_connection, client_address = listen_socket.accept()
        request = client_connection.recv(2048)

        # 提取聊天文字
        jdata = json.loads(request.decode("utf-8").split('\r\n')[-1])
        msg = jdata['raw_message']
        uid = jdata['user_id']
        # 仅限 csgo 群
        if 'group_id' in jdata.keys() and jdata['group_id'] == 522201349:
            gid = jdata['group_id']
        else:
            gid = 0
        print(msg, uid, gid)

        # 处理命令
        ms = msg.split()
        if 'add' == ms[0] and len(ms) == 3 and check_user_right(uid):
            add_talk_dict(ms[1], ms[2])
            if gid:
                send_group_rawmsg(gid, '爷记住了')
            else:
                send_private_rawmsg(863347350, '爷记住了')
            continue
        elif 'del' == ms[0] and len(ms) == 2 and check_user_right(uid):
            del_talk_dict(ms[1])
            if gid:
                send_group_rawmsg(gid, '爷记住了')
            continue
        # elif 'mod' == ms[0] and len(ms) == 3 and check_user_right(uid):
        #     mod_talk_dict(ms[1], ms[2])
        #     if gid:
        #         send_group_rawmsg(gid, '爷记住了')
        #     continue
        else:
            print('no')

        # 处理权限命令
        if 'addu' == ms[0] and len(ms) == 2 and check_user_right(uid)==2:
            add_user_right(ms[1])
            if gid:
                send_group_rawmsg(gid, '爷记住了')
            continue
        elif 'delu' == ms[0] and len(ms) == 2 and check_user_right(uid)==2:
            del_user_right(ms[1])
            if gid:
                send_group_rawmsg(gid, '爷记住了')
            continue
        else:
            print('no')

        # 处理关键字命令
        talk_dict = load_talk_dict()
        if ms[0] in talk_dict.keys():
            tlist = talk_dict[ms[0]]
            if gid:
                send_group_rawmsg(gid, random.choice(tlist))
            print(ms[0], random.choice(tlist))


        # if '[CQ:at,qq=2257856228]' in msg:
        #     msg1 = msg.replace('[CQ:at,qq=2257856228]', '')
        #     msg1
        # 处理 @ 请求
        # pass


#         # 处理at请求
#         if '[CQ:at,qq=2257856228]' in rm:
#             rm = rm.replace('[CQ:at,qq=2257856228]', '')
#             # 冷知识推送
#             if 'tips' in rm:
#                 res = Tips_Response[randint(0,len(Tips_Response)-1)]
#                 send_group_msg(GROUPID, res)
#                 # send_private_rawmsg(MYQQID, res)
#                 continue
#
#
#             # 接入聊天机器人
#             robot_res = talk_robot1(rm)
#             if robot_res:
#                 print(robot_res)
#                 res = robot_res
#             else :
#                 # 聊天机器人坏了， 用备用语录 robot_at_response
#                 res = robot_at_response[randint(0,len(robot_at_response)-1)]
#
#             send_group_msg(GROUPID, res)
#             # send_private_rawmsg(MYQQID, res)
#             continue
#

#
# #         http_response = """\
# # HTTP/1.1 200 OK
# #
# # ok"""
# #         client_connection.sendall(http_response.encode("utf-8"))
#         client_connection.close()



def main():

    # threading.Thread(target=qq_listen).start()
    # threading.Thread(target=dota2_listen).start()

    # save_talk_dict(update_talk_dict1(load_talk_dict()))
    qq_listen()

    # get_match_detail(5956077603, 162255543)
    # match_push(5956077603, 162255543)





main()