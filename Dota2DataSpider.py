import dota2api
api = dota2api.Initialise("1BC6DE387E44B90EDFBB7E6C2E94478B", raw_mode=True)
import pymysql
import threading
import time

# data_list
player_data_list = []
player_ablilty_data_list = []
player_additional_units_list = []
match_pick_list = []
match_details = []

# error_list
except_mid_list = []
pass_gm_list = []

def get_data(mid):
    try:
        md = api.get_match_details(match_id=str(mid))
    except:
        print(str(mid),' 无数据')
        return 0

    # 比赛模式为 ap、rd、队长
    # 18 omg ，22 ap ，23 加速 ，3 rd ，4 小黑屋， 13 新玩家教程？
    gm = md['game_mode']
    if gm == 3 or gm == 22:
        if len(md) == 24:
            pass
        else:
            except_mid_list.append(mid)
            return 0
    else:
        pass_gm_list.append(gm)
        return 0


    players = md.pop('players')
    for p in players:
        uid = p['account_id']
        if p.__contains__('ability_upgrades'):
            au = p.pop('ability_upgrades')
            for a in au:
                tmp = [mid, uid]
                tmp.extend(a.values())
                player_ablilty_data_list.append(tuple(tmp))
        tmp = [mid]
        if p.__contains__('additional_units'):
            addun = p.pop('additional_units')
            for ad in addun:
                adtmp = [mid, uid]
                adtmp.extend(ad.values())
                player_additional_units_list.append(tuple(adtmp))

            tmp.extend(p.values())
        else:
            tmp.extend(p.values())
        player_data_list.append(tuple(tmp))

    # match_pick_list
    picks_bans = md.pop('picks_bans')
    for p in picks_bans:
        tmp = [mid]
        tmp.extend(p.values())
        match_pick_list.append(tuple(tmp))

    # match_details
    match_details.append(tuple(md.values()))
    print(str(mid),' ok')
    return 1

def update_data():
    # 连接database
    conn = pymysql.connect(
        host='127.0.0.1',
        user='admin', password='123456',
        database='dota2data',
        charset='utf8')
    cursor = conn.cursor()

    # update data
    if match_details:
        sql = 'insert into match_players(match_id, account_id, player_slot, hero_id, item_0, item_1, item_2, item_3, item_4, item_5, backpack_0, backpack_1, backpack_2, item_neutral, kills, deaths, assists, leaver_status, last_hits, denies, gold_per_min, xp_per_min, level, hero_damage, tower_damage, hero_healing, gold, gold_spent, scaled_hero_damage, scaled_tower_damage, scaled_hero_healing) values(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s);'
        cursor.executemany(sql, player_data_list)

        sql = 'insert into match_players_ability(match_id,account_id,ability,time,level) values(%s,%s,%s,%s,%s);'
        cursor.executemany(sql, player_ablilty_data_list)

        sql = 'insert into match_details(radiant_win,duration,pre_game_duration,start_time,match_id,match_seq_num,tower_status_radiant,tower_status_dire,barracks_status_radiant,barracks_status_dire,cluster,first_blood_time,lobby_type,human_players,leagueid,positive_votes,negative_votes,game_mode,flags,engine,radiant_score,dire_score) values(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s);'
        cursor.executemany(sql, match_details)

        sql = 'insert into match_pick(match_id,is_pick,hero_id,team,order_) values(%s,%s,%s,%s,%s);'
        cursor.executemany(sql, match_pick_list)

        if player_additional_units_list:
            sql = 'insert into match_syllabear_players(match_id, account_id, unitname, item_0, item_1, item_2, item_3, item_4, item_5, backpack_0, backpack_1, backpack_2, item_neutral) values(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s);'
            cursor.executemany(sql, player_additional_units_list)
    conn.commit()

    print('成功:',len(match_details),'个；有例外的比赛：', len(except_mid_list),'个；例外的模式类型有', len(set(pass_gm_list)),'个。')
    print(except_mid_list)
    print(set(pass_gm_list))

s1 = threading.Semaphore(100)
threads = []
def run(mid):
    s1.acquire(timeout=20)
    try:
        get_data(mid)
    finally:
        s1.release()

def main():

    i = 5943304066
    while 1:

        for mid in range(i, i+50000):
            t = threading.Thread(target=run, args=(mid,))
            threads.append(t)
            t.start()

        for t in threads:
            t.join()

        update_data()
        i = i + 50000
main()

