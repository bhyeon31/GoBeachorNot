from flask import Flask, render_template, request, redirect, url_for, session
from urllib import parse
from bson.json_util import dumps
import pymongo
import json
import requests
from datetime import timedelta
import datetime


url1 = 'http://apis.data.go.kr/1192000/service/OceansBeachSeawaterService1/getOceansBeachSeawaterInfo1'
key1 = 'JczkNAYUK0nuC7gzVNgSj2%2FUHiwakF7h%2BMI7BkHeAuKc7ctuY961tl%2F%2B%2Fo2hCS2TjorkkeQ2IEek%2BGPFiC0Xdg%3D%3D'
url2 = 'https://seantour.com/seantour_map/travel/getBeachCongestionApi.do'
url3 = 'http://apis.data.go.kr/1192000/service/OceansBeachInfoService1/getOceansBeachInfo1'
key2 = 'JczkNAYUK0nuC7gzVNgSj2%2FUHiwakF7h%2BMI7BkHeAuKc7ctuY961tl%2F%2B%2Fo2hCS2TjorkkeQ2IEek%2BGPFiC0Xdg%3D%3D'

sido_map = {'부산광역시':'부산','인천광역시':'인천','울산광역시':'울산','강원도':'강원','충청남도':'충남'
               ,'전라북도':'전북','전라남도':'전남','경상북도':'경북','경상남도':'경남','제주특별자치도':'제주'}

app = Flask(__name__)
app.secret_key = '~@gsafewf^@#$^vwssdf324315aw&^$#'


@app.before_request
def make_session_permanent():
    session.permanent = True
    app.permanent_session_lifetime = timedelta(minutes=5)

@app.route('/')
def index():
    return redirect(url_for('main'))


@app.route('/main',methods = ['POST','GET'])
def main():
    if request.method == 'POST':
        fil = request.form
        client = pymongo.MongoClient("mongodb://###:###@#########:#####/gobeachornot")  # defaults to port 27017
        db = client.gobeachornot
        col = db.BeachInfo

        f = col.find_all({})

        if 'search' in fil:

            name = f['해수욕장명'] == fil['search']
            data = f[name][['해수욕장명','시도 주소','시군구 주소','개장일','폐장일','홈페이지','연락처']]

            key = data.to_dict().keys()
            v = data.to_dict().values()
            v = list(map(lambda x: list(x.values()), v))
            value = []

            for i in range(7):
                d = {j: v[i][j] for j in range(len(v[i]))}
                value.append(d)

            result = dict(zip(key, value))

            if result['시도 주소'] != {}:
                result['시도 주소'] = result['시도 주소'][0]
                result['시군구 주소'] = result['시군구 주소'][0]
            else:
                del result['시도 주소']
                del result['시군구 주소']


        else:
            sido = f['시도 주소'] == fil['sido']
            sigun = f['시군구 주소'] == fil['sigun']

            if fil['sido'] != "none" and fil['sigun'] != "none":
                data = f[sido & sigun][['해수욕장명','개장일','폐장일','홈페이지','연락처']]
            elif fil['sigun'] == "none":
                data = f[sido][['해수욕장명', '개장일', '폐장일', '홈페이지', '연락처']]
            else :
                data = f[sigun][['해수욕장명','개장일','폐장일','홈페이지','연락처']]

            key = data.to_dict().keys()
            v = data.to_dict().values()
            v = list(map(lambda x:list(x.values()), v))
            value=[]

            for i in range(5):
                d = {j:v[i][j] for j in range(len(v[i]))}
                value.append(d)

            result = dict(zip(key, value))
            result['시도 주소'] = fil['sido']
            result['시군구 주소'] = fil['sigun']

        return render_template('main.html',result = result)


    if request.method == 'GET':
        return render_template('main.html')

@app.route('/detail')
def detail():

    name = request.args.get('name')
    if request.args.get('sido') in sido_map.keys():
        sido = sido_map[request.args.get('sido')]
    else:
        sido = request.args.get('sido')

    client = pymongo.MongoClient("mongodb://###:###@#########:#####/gobeachornot")  # defaults to port 27017
    db = client.gobeachornot
    col = db.BeachInfo

    f = col.find_all({})
    data = f[f['해수욕장명'] == name].to_dict()

    result = {}
    result['name'] = name
    result['sido'] = request.args.get('sido')

    key = list(data['연번'])[0]

    result['해수욕장명'] = data['해수욕장명'][key]
    result['주소'] = data['시도 주소'][key] + " " + data['시군구 주소'][key] + " " + data['읍면동 주소'][key]
    if data['이하 주소'][key] != "-":
        result['주소'] = result['주소'] + " " + data['이하 주소'][key]
    result['개장일'] = data['개장일'][key]
    result['폐장일'] = data['폐장일'][key]
    result['주요행사'] = ""
    for i in range(1, 9):
        s = '주요행사' + str(i)
        if data[s][key] != "-":
            result['주요행사'] = result['주요행사'] + data[s][key] + ", "
        if i == 8:
            result['주요행사'] = result['주요행사'][:-2]
    result['홈페이지'] = data['홈페이지'][key]
    result['연락처'] = data['연락처'][key]

    tmp = {}

    for i in range(2018, 2013, -1):
        queryParams = f'?{parse.quote_plus("ServiceKey")}={key1}&' + parse.urlencode({
            parse.quote_plus('resultType'): 'json',
            parse.quote_plus('SIDO_NM'): sido,
            parse.quote_plus('RES_YEAR'): i})
        req = requests.get(url1 + queryParams)
        d = req.json()['getOceansBeachSeawaterInfo']['item']

        for j in d:
            if j['sta_nm'] == name:
                tmp['대장균'] = j['res1']
                tmp['장구균'] = j['res2']
                tmp['적합여부'] = j['res_yn']
                tmp['조사지점(위도)'] = j['lat']
                tmp['조사지점(경도)'] = j['lon']
                break
        if tmp != {}:
            break
        if tmp == {} and i == 2014: #TODO: 수정?
            tmp['대장균'] = d[0]['res1']
            tmp['장구균'] = d[0]['res2']
            tmp['적합여부'] = d[0]['res_yn']
            tmp['조사지점(위도)'] = d[0]['lat']
            tmp['조사지점(경도)'] = d[0]['lon']

    result.update(tmp)

    req = requests.get(url2)

    data = req.json()

    for i in data:
        nm = data[i]['poiNm'].split(' ')[1]
        if nm in name or name in nm:
            result['uniqPop'] = data[i]['uniqPop']
            result['congestion'] = data[i]['congestion']
            break

    if 'uniqPop' not in result:
        result['uniqPop'] = '미측정'
        result['congestion'] = '미측정'

    if result['congestion'] == '3' and result['적합여부'] == '부적합':
        result['휴양적합여부'] = '부적합1'
    elif result['congestion'] == '2' and result['적합여부'] == '부적합':
        result['휴양적합여부'] = '부적합2'
    else: result['휴양적합여부'] = '적합'



    queryParams = f'?{parse.quote_plus("ServiceKey")}={key2}&' + parse.urlencode({
        parse.quote_plus('resultType'): 'json',
        parse.quote_plus('SIDO_NM'): sido})
    data3 = requests.get(url3 + queryParams).json()['getOceansBeachInfo']['item']

    for i in data3:
        if i['sta_nm'] in name or name in i['sta_nm']:
            result['beach_wid'] = i['beach_wid']
            result['beach_len'] = i['beach_len']
            result['beach_knd'] = i['beach_knd']
            result['lat'] = i['lat']
            result['lon'] = i['lon']
            break

    print(result)

    if request.args.get('reg') == '1':
        result['alarm'] = "등록 되었습니다."
        return render_template('detail.html', result=result)
    return render_template('detail.html',result=result)

@app.route('/login',methods = ['POST','GET'])
def login():
    if request.method == 'GET':
        return render_template("login.html")

    if request.method == 'POST':
        info = request.form

        client = pymongo.MongoClient("mongodb://###:###@#########:#####/gobeachornot")  # defaults to port 27017
        db = client.gobeachornot
        col = db.SignupInfo

        query = {"id":info["id"], "pw":info["pw"]}

        cur = col.find(query)
        doc = dumps(list(cur))

        if doc != "[]":
            session['uid'] = info['id']
            print("{0} login!".format(session['uid']))
            return redirect(url_for('main'))
        else :
            message = "아이디 또는 비밀번호를 확인하시오."
            return render_template("login.html",message=message)

        return render_template("login.html")

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('main'))

@app.route('/mybeach',methods=['POST','GET'])
def mybeach():
    if 'uid' in session:
        if request.method == 'POST':
            value = request.form.getlist('check')

            client = pymongo.MongoClient("mongodb://###:###@#########:#####/gobeachornot")  # defaults to port 27017
            db = client.gobeachornot
            col = db.MyBeachInfo

            for i in value:
                q = {}
                q['name'] = i
                col.delete_one(q)

            return redirect(url_for("mybeach"))
        else:
            print("mybeach session id : {0}".format(session['uid']))

            client = pymongo.MongoClient("mongodb://###:###@#########:#####/gobeachornot")  # defaults to port 27017
            db = client.gobeachornot
            col = db.MyBeachInfo
            cur = col.find({'id':session['uid']})
            doc = dumps(list(cur))
            result={}
            no = 0
            if doc != "[]":
                for i in json.loads(doc):   #list
                    result[no]=i
                    no+=1

            return render_template("mybeach.html",result=result)

    else:
        return render_template("login.html")


@app.route('/signup',methods = ['POST','GET'])
def signup():
    if request.method == 'GET':
        return render_template("signup.html")
    if request.method == 'POST':
        client = pymongo.MongoClient("mongodb://###:###@#########:#####/gobeachornot")  # defaults to port 27017
        db = client.gobeachornot
        col = db.SignupInfo

        tmp = request.form

        if tmp['id']=="" or tmp['pw']=="" or tmp['name']=="" or tmp['hp']=="":
            message = "빈칸 없이 모두 작성 부탁드립니다."
            return render_template("signup.html", message=message)

        info = {'id':tmp['id'], 'pw':tmp['pw'], 'name':tmp['name'], 'hp':tmp['hp']}
        col.insert_one(info)

        return render_template("login.html")

@app.route('/registerBeach')
def registerBeach():
    if 'uid' in session:
        now = datetime.datetime.now()
        nowDatetime = now.strftime('%Y-%m-%d %H:%M:%S')

        print("register session id : {0}".format(session['uid']))

        name = request.args.get('name')
        sido = sido_map[request.args.get('sido')]

        client = pymongo.MongoClient("mongodb://###:###@#########:#####/gobeachornot")  # defaults to port 27017
        db = client.gobeachornot
        col = db.MyBeachInfo

        q = {'id':session['uid'],'name':name,'sido':sido,'time':nowDatetime}
        col.insert_one(q)

        qp = "?"+'name='+name+'&sido='+request.args.get('sido')+'&reg=1'

        return redirect(url_for('detail')+qp)
    else:
        return render_template("login.html")


if __name__ == '__main__':
    app.run(debug=True)