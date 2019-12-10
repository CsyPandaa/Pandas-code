import requests
import re
import time
import random
import jieba
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.naive_bayes import MultinomialNB
from cqhttp import CQHttp, Error


bot = CQHttp(api_root='http://127.0.0.1:5700/')

class Weather(object):

    def __init__(self,location,userlist):
        self.key='S039jLTeG4E9z50SB'
        self.goodmorning_key='fdf43f25376f1e860203a11a0bae35c1'
        self.location=location
        self.warnspeed=25
        self.raincode = [10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20]
        self.snowcode = [21, 22, 23, 24, 25]
        self.userlist=userlist
    def special_warn(self):
        warning_url = f'https://api.seniverse.com/v3/weather/alarm.json?key={self.key}&location={self.location}'
        warning_res = requests.get(url=warning_url)
        warning_data = warning_res.json()
        warning_data = warning_data['results'][0]
        warning_text = warning_data['alarms']
        warnlist = []
        for text_warn in warning_text:
            warnlist.append(text_warn['title'] + text_warn['description'])
        if len(warnlist) > 0:
            send=SendWarn(self.userlist)
            for text in warnlist:
                send.qqmessage('注意注意！有灾害预警来啦\n'+text)
                time.sleep(0.5)
    def future_warn(self,warnhours):
        send_warn=SendWarn(self.userlist)
        alert_rain = False
        alert_snow = False
        alert_wind = False
        future_url = f'https://api.seniverse.com/v3/weather/hourly.json?key={self.key}&location={self.location}&language=zh-Hans&unit=c&start=0&hours={warn_hours}'
        future_res = requests.get(url=future_url)
        future_data = future_res.json()
        selflocation = future_data['results'][0]['location']['path']
        future_text = future_data['results'][0]['hourly']
        for fut_data in future_text:
            weacode = int(fut_data['code'])
            if weacode in self.raincode and not alert_rain:
                raindate = fut_data['time'][:10]
                raintime_hour = fut_data['time'][11:13]
                message = fut_data['text']
                mstr = '' * random.randint(1, 5) + ''
                message=mstr+'要下雨了！！'+f'\n{self.location}在{raindate}日{raintime_hour}点 有{message}！别忘了带伞呀咯咯'
                send_warn.qqmessage(message)
                alert_rain = True
            if weacode in self.snowcode and not alert_snow:
                snowdate=fut_data['time'][:10]
                snowtime_hour=fut_data['time'][11:13]
                message=fut_data['text']
                mstr = '' * random.randint(1, 5) + ''
                message=mstr+'要下雪了！！'+f'\n{self.location}在{snowdate}日{snowtime_hour}点 有{message}！别忘了带伞呀咯咯'
                send_warn.qqmessage(message)
                alert_snow = True
            if float(fut_data['wind_speed']) >= self.warnspeed and not alert_wind:
                winddate=fut_data['time'][:10]
                windtime_hour=fut_data['time'][11:13]
                wind_speed=fut_data['wind_speed']+ ' km/h'
                speed_int=int(float(fut_data['wind_speed']))

                if speed_int in range(25,29):
                    windgrade=4
                elif speed_int in range(29,39):
                    windgrade=5
                elif speed_int in range(39,50):
                    windgrade=6
                elif speed_int in range(50,62):
                    windgrade=7
                elif speed_int in range(62,75):
                    windgrade=8
                elif speed_int in range(75,88):
                    windgrade=9
                else:
                    windgrade=10
                mstr=''*random.randint(1,5)+''
                message='！！！'+mstr+f'{self.location}一会要刮风了！！！'+f'\n在{winddate}日{windtime_hour}点会有等级为{windgrade}级，风速为{wind_speed}的风！\n'
                if windgrade in range(5,7):
                    message+='提示：风速有一点点大 但还是刮不走你的 请注意加衣避风喔~'
                elif windgrade>=7:
                    message+='警告！风速较大！此等级风速会导致行走困难！！尽量回到室内！！远离高楼、悬挂物以及可能坠落的物品！'
                elif windgrade>=8:
                    message+='警告！这不是演习！请立即前往室内！远离高楼、悬挂物以及可能坠落的物品！'
                elif windgrade>=9:
                    message+='危险！可能造成严重伤害！这不是演习！请立即前往室内！远离高楼、悬挂物以及可能坠落的物品！ '
                send_warn.qqmessage(message)
                alert_wind = True
    def aqiWarn(self):
        alert_aqi = False
        api_url = f'https://api.seniverse.com/v3/air/hourly.json?key={self.key}&language=zh-Hans&location={self.location}'
        apires = requests.get(api_url)
        api_data = apires.json()
        future_text = api_data['results'][0]['hourly'][:2]
        for i in future_text:
            if int(i['aqi']) >= 250 and not alert_aqi:
                send=SendWarn(self.userlist)
                apidate = i['time'][:10]
                apitime_hour = i['time'][11:13]
                aqinum=int(i['aqi'])
                aqitext=i['quality']
                mstr = '' * random.randint(1, 5) + '\n'
                message=mstr+f'{self.location}{apidate}日{apitime_hour}点\n空气指数为{aqinum} 为{aqitext}'
                if aqinum>=300:
                    message+='注意！ 重度污染啦 尽量呆在室内喔~'
                elif aqinum>=450:
                    message+='警告！ 空气严重污染！ 尽量呆在室内！！出门一定要带口罩呀！！'
                send.qqmessage(message)
                alert_aqi = True
    def suggestions(self):
        morningurl=f'http://api.tianapi.com/txapi/zaoan/index?key={self.goodmorning_key}'
        res=requests.get(morningurl)
        morndata=res.json()
        goodmorning=morndata['newslist'][0]['content']
        send_warn=SendWarn(self.userlist)
        res = requests.get(
            f'https://api.seniverse.com/v3/life/suggestion.json?key={self.key}&location={self.location}&language=zh-Hans')
        data = res.json()
        local=self.location
        comfortable = '舒适指数:'+data['results'][0]['suggestion']['comfort']['details']+'\n'
        dressing = '穿衣指数:'+data['results'][0]['suggestion']['dressing']['details']+'\n'
        flu = '感冒指数:'+data['results'][0]['suggestion']['flu']['details']+'\n'
        sport = '运动指数:'+data['results'][0]['suggestion']['sport']['details']+'\n'
        sunhurt = '紫外线指数:'+data['results'][0]['suggestion']['sunscreen']['details']+'\n'
        umbrella = '降雨提醒:'+data['results'][0]['suggestion']['umbrella']['details']+'\n'
        message=self.location+'\n'+comfortable+dressing
        message2=flu+sport
        message3=sunhurt+umbrella
        message4=goodmorning
        send_warn.qqmessage(message)
        time.sleep(1)
        send_warn.qqmessage(message2)
        time.sleep(1)
        send_warn.qqmessage(message3)
        time.sleep(1)
        send_warn.qqmessage(message4)
    def check_working(self):
        adminid='1225753951'
        message=self.location+'Working'
        try:
            qqmessage_url = f'http://127.0.0.1:5700/send_private_msg?user_id={adminid}&message={message}'
            res=requests.get(qqmessage_url)
            resjson = res.json()
        except:
            errmoudle='check_working Err'
            Err_record.fatalerr_record(errmoudle)
        else:
            if resjson['status'] != 'ok':
                errname = f'send meaage to adminid False--check_wroking'
                Err_record.funerr_record(errname)
class SendWarn():
    def __init__(self,userlist):
        self.userlist=userlist
    def qqmessage(self,message):
        for userid in self.userlist:
            try:
                qqmessage_url = f'http://127.0.0.1:5700/send_private_msg?user_id={userid}&message={message}'
                res = requests.get(qqmessage_url)
                time.sleep(0.5)
            except:
                errname='Send to QQ Moudle Err'
                Err_record.fatalerr_record(errname)
            else:
                resjson=res.json()
                if resjson['status']!='ok':
                    errname=f'send meaage to {userid} False'
                    Err_record.funerr_record(errname)
    def hello_message(self):
        message=f'MyWeather System Start\n 系统初始化 '
        for userid in self.userlist:
            try:
                qqmessage_url = f'http://127.0.0.1:5700/send_private_msg?user_id={userid}&message={message}'
                res = requests.get(qqmessage_url)
                time.sleep(0.5)
            except:
                errname='Send to QQ Moudle Err'
                Err_record.fatalerr_record(errname)
            else:
                resjson=res.json()
                if resjson['status']!='ok':
                    errname=f'send meaage to {userid} False'
                    Err_record.funerr_record(errname)

class Err_record():
    @staticmethod
    def fatalerr_record(errmoudle):
        with open('fatalerr.txt', 'a')as f:
            f.write(time.asctime() + '\t' + errmoudle + '\n')
    @staticmethod
    def funerr_record(errfun):
        with open('funerr.txt','a')as f:
            f.write(time.asctime()+ '\t' + errfun + '\n')
class alone_response():
    def __init__(self,location):
        self.loaction=location
    def getswea(self):
        pass
class words_conform():
    def __init__(self,sentence):
        self.sentence=sentence
    def getword(self):
        X = ['有雨 吗', '有雪 吗', '有风 吗','冷 吗','下雨']
        y = ['雨', '雪', '风','天气','雨']
        ti = TfidfVectorizer(norm=None, token_pattern="[a-zA-Z|\u4e00-\u9fa5]+")
        x = ti.fit_transform(X)
        model = MultinomialNB()
        model.fit(x, y)
        if self.sentence != '':
            word_cut = jieba.cut(self.sentence, cut_all=False)
            word_cut = ' '.join(word_cut)
            print(word_cut)
            result = model.predict(ti.transform([word_cut]))
            return result
        else:
            pass
if __name__ == '__main__':
    userlist_all=[1225753951]
    firsttest=SendWarn(userlist_all)
    firsttest.hello_message()
    @bot.on_message()
    def handle_msg(context):
        # 下面这句等价于 bot.send_private_msg(user_id=context['user_id'], message='你好呀，下面一条是你刚刚发的：')
        words=words_conform(context['message'])
        judge=words.getword()
        print(judge)
        # if '天气' in context['message']:
        #     viplocation=re.findall(r'(.*?)天气',context['message'])[0]
        #     wea = alone_response(viplocation)
        #
        #     try:
        #         bot.send(context,f'你正在查询{viplocation}天气')
        #     except Error:
        #         pass
            # return {'reply': context['message'],
            #         'at_sender': False}  # 返回给 HTTP API 插件，走快速回复途径


    bot.run(host='127.0.0.1', port=3031)


    raise Exception('pause')


    while True:
        nowtime=time.localtime().tm_hour
        if nowtime==21 or nowtime==6:
            warn_hours=10
        else:
            warn_hours = 1
        userlist_c=[1225753951]
        userlist_d=[2792457328]
        s=Weather(location='上海奉贤',userlist=userlist_d)
        j=Weather(location='河南济源',userlist=userlist_d)
        b=Weather(location='北京海淀',userlist=userlist_c)
        if nowtime==6:
            s.suggestions()
            b.suggestions()
        b.aqiWarn()
        b.special_warn()
        b.future_warn(warn_hours)
        s.special_warn()
        s.aqiWarn()
        s.future_warn(warn_hours)
        j.special_warn()
        j.aqiWarn()
        j.future_warn(warn_hours)
        print(time.asctime())
        time.sleep(3600)
