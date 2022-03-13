import json
import random
import time
from datetime import datetime, timedelta

from mysports.original_json import no_free_data, host
from mysports.sports import *
from path_plan.plan import path_plan, get_school_location
from mysports.utils import get_token


def no_free_run(userid: str, ses, extra_pn=1, school="", rg=(1, 2), debug=False):
    school_location = get_school_location(school)
    init_location = str(school_location['lng']) + "," + str(school_location['lat'])
    data = json.dumps({"initLocation": init_location, "type": "1", "userid": userid})

    res = ses.get(host + '/api/run/runPage', headers={'ntoken': get_token()},
                  params={'sign': get_md5_code(data), 'data': data.encode('ascii')})
    print(res.json())
    if res.json()['code'] == 404:
        print('<NoFreeRunModule>: 体育锻炼接口返回 JSON：', res.json()['msg'])
        print(res.headers)
        return
    resj = res.json()['data']
    print('<NoFreeRunModule>: 体育锻炼接口返回 JSON：', resj)

    # red, green
    red, green = rg

    if debug:
        print('school:' + str(school) + ' ' + 'location:' + str(school_location))
    # 处理节点
    possible_bNode = [item for item in resj['ibeacon'] if haversine(item['position'], school_location)['km'] < 60]
    possible_tNode = [item for item in resj['gpsinfo'] if haversine(item, school_location)['km'] < 60]

    no_free_data['bNode'] = possible_bNode[:red]
    no_free_data['tNode'] = possible_tNode[:green]
    print('possible_bNode：', possible_bNode)
    print('possible_tNode：', possible_tNode)
    if debug:
        print('bNode to use:' + str(no_free_data['bNode']['position']))
        print('tNode to use:' + str(no_free_data['tNode']))
    try:
        position_info = no_free_data['bNode'][0]['position']
    except:
        position_info = no_free_data['tNode'][0]
    start_point = gps_point(float(position_info['latitude']), float(position_info['longitude']))

    # pass_by_ps : List[gps_point]
    pass_by_ps = gps_point_list([start_point.zouzou(strip=0.003) for _ in range(extra_pn)])

    # reformat bnode, tnode ;  collect passby points
    for node in no_free_data['bNode']:
        pos = node['position']
        pos['latitude'] = float(pos['latitude'])
        pos['longitude'] = float(pos['longitude'])
        pos['speed'] = 0.0
        node['position'] = pos

        pass_by_ps.append(gps_point(pos['latitude'], pos['longitude']))

    for pos in no_free_data['tNode']:
        pos['latitude'] = float(pos['latitude'])
        pos['longitude'] = float(pos['longitude'])
        pos['speed'] = 0.0

        pass_by_ps.append(gps_point(pos['latitude'], pos['longitude']))

    # path plan
    plan = path_plan(pass_by_ps)
    maxdis = 2.5 + random.randint(1, 20) * 0.01
    dis = max(plan['distance'], maxdis)
    print(dis)
    print(plan['distance'])
    path = plan['path']

    # reformat path
    tmp = []
    for p in path:
        tmp.append({'latitude': p['lat'], 'longitude': p['lng']})
    path = tmp

    # gen speed, duration, speed...
    speed = random.randint(300, 500)  # seconds per km
    duration = dis * speed  # seconds

    # to 'minutes'seconds'microseconds'
    speed = "%s'%s''" % (speed // 60, speed - speed // 60 * 60)
    startTime = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # peisu = 1000 / (bupin * bufu)
    bupin = random.uniform(120, 140)
    bushu = random.randint(2000, 3000)
    # construct post data
    no_free_data['endTime'] = (datetime.now() + timedelta(seconds=duration)).strftime("%Y-%m-%d %H:%M:%S")
    no_free_data['startTime'] = startTime
    no_free_data['userid'] = userid
    no_free_data['runPageId'] = resj['runPageId']
    no_free_data['real'] = str(dis * 1000)
    no_free_data['duration'] = str(duration)
    no_free_data['speed'] = speed
    no_free_data['track'] = path
    no_free_data['buPin'] = '%.1f' % bupin
    no_free_data['totalNum'] = "%d" % bushu
    if not debug:
        print('plan run %s km til %s' % (dis, no_free_data['endTime']))
        print("Ignore it now.")
        print("Wait for time pass.")
        # time.sleep(duration)
    xs = json.dumps(no_free_data)

    r = ses.post(host + '/api/run/saveRunV2', headers={'ntoken': get_token()},
                 data={'sign': get_md5_code(xs), 'data': xs.encode('ascii')})
    print(r.content.decode('utf-8'))
    return dis
