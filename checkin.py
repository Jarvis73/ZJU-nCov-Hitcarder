# -*- coding: utf-8 -*-
import requests, json, re
import time, datetime, os, sys
import getpass
from halo import Halo
from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.jobstores.base import JobLookupError
import random
import time
from pathlib import Path
import argparse

scheduler = BlockingScheduler()
hour = 0
minute = 5


class CheckIn(object):
    """Hit card class

    Attributes:
        username: (str) 浙大统一认证平台用户名（一般为学号）
        password: (str) 浙大统一认证平台密码
        login_url: (str) 登录url
        base_url: (str) 打卡首页url
        save_url: (str) 提交打卡url
        self.headers: (dict) 请求头
        sess: (requests.Session) 统一的session
    """
    def __init__(self, username, password):
        self.username = username
        self.password = password
        self.login_url = "https://zjuam.zju.edu.cn/cas/login?service=https%3A%2F%2Fhealthreport.zju.edu.cn%2Fa_zju%2Fapi%2Fsso%2Findex%3Fredirect%3Dhttps%253A%252F%252Fhealthreport.zju.edu.cn%252Fncov%252Fwap%252Fdefault%252Findex"
        self.base_url = "https://healthreport.zju.edu.cn/ncov/wap/default/index"
        self.save_url = "https://healthreport.zju.edu.cn/ncov/wap/default/save"
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/75.0.3770.100 Safari/537.36"
        }
        self.sess = requests.Session()

    def login(self):
        """Login to ZJU platform"""
        res = self.sess.get(self.login_url, headers=self.headers)
        execution = re.search('name="execution" value="(.*?)"', res.text).group(1)
        res = self.sess.get(url='https://zjuam.zju.edu.cn/cas/v2/getPubKey', headers=self.headers).json()
        n, e = res['modulus'], res['exponent']
        encrypt_password = self._rsa_encrypt(self.password, e, n)

        data = {
            'username': self.username,
            'password': encrypt_password,
            'execution': execution,
            '_eventId': 'submit'
        }
        res = self.sess.post(url=self.login_url, data=data, headers=self.headers)

        # check if login successfully
        if '统一身份认证' in res.content.decode():
            raise LoginError('登录失败，请核实账号密码重新登录')
        return self.sess
    
    def post(self):
        """Post the hitcard info"""
        res = self.sess.post(self.save_url, data=self.info, headers=self.headers)
        return json.loads(res.text)
    
    def get_date(self):
        """Get current date"""
        today = datetime.date.today()
        return "%4d%02d%02d" %(today.year, today.month, today.day)
        
    def get_info(self, html=None):
        """Get hitcard info, which is the old info with updated new time."""
        if not html:
            res = self.sess.get(self.base_url, headers=self.headers)
            html = res.content.decode()

        try:
            old_infos = re.findall(r'oldInfo: ({[^\n]+})', html)
            if len(old_infos) != 0:
                old_info = json.loads(old_infos[0])
            else:
                raise RegexMatchError("未发现缓存信息，请先至少手动成功打卡一次再运行脚本")

            new_info_tmp = json.loads(re.findall(r'def = ({[^\n]+})', html)[0])
            new_id = new_info_tmp['id']
            name = re.findall(r'realname: "([^\"]+)",', html)[0]
            number = re.findall(r"number: '([^\']+)',", html)[0]
        except IndexError as err:
            raise RegexMatchError('Relative info not found in html with regex')
        except json.decoder.JSONDecodeError as err:
            raise DecodeError('JSON decode error')

        new_info = old_info.copy()
        new_info['id'] = new_id
        new_info['name'] = name
        new_info['number'] = number
        new_info["date"] = self.get_date()
        new_info["created"] = round(time.time())
        # form change
        # -----------------------------------------------------------------------------
        # new_info['address'] = ''                # 如: 'xx省xx市xx区xx街道xx小区'
        # new_info['area'] = 'xx省 xx市 xx区'      # 如: '浙江省 杭州市 西湖区'  记得中间用空格隔开, 省市区/县名称可以参考 打卡页面->基本信息->家庭所在地 中对应的省市区/县名
        # new_info['province'] = new_info['area'].split(' ')[0]   # 省名
        # new_info['city'] = new_info['area'].split(' ')[1]       # 市名
        # -----------------------------------------------------------------------------
        new_info['jrdqtlqk[]'] = 0
        new_info['jrdqjcqk[]'] = 0
        new_info['sfsqhzjkk'] = 1   # 是否申领杭州健康码
        new_info['sqhzjkkys'] = 1   # 杭州健康吗颜色，1:绿色 2:红色 3:黄色
        new_info['sfqrxxss'] = 1    # 是否确认信息属实
        new_info['jcqzrq'] = ""
        new_info['gwszdd'] = ""
        new_info['szgjcs'] = ""
        self.info = new_info
        # print(old_info, self.info)
        return new_info

    def _rsa_encrypt(self, password_str, e_str, M_str):
        password_bytes = bytes(password_str, 'ascii') 
        password_int = int.from_bytes(password_bytes, 'big')
        e_int = int(e_str, 16) 
        M_int = int(M_str, 16) 
        result_int = pow(password_int, e_int, M_int) 
        return hex(result_int)[2:].rjust(128, '0')


# Exceptions 
class LoginError(Exception):
    """Login Exception"""
    pass

class RegexMatchError(Exception):
    """Regex Matching Exception"""
    pass

class DecodeError(Exception):
    """JSON Decode Exception"""
    pass


def main(username, password):
    """Hit card process

    Arguments:
        username: (str) 浙大统一认证平台用户名（一般为学号）
        password: (str) 浙大统一认证平台密码
    """
    try:
        scheduler.remove_job('checkin_ontime')
    except JobLookupError as e:
        pass

    print("\n[Time] %s" %datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
    print("🚌 打卡任务启动")
    spinner = Halo(text='Loading', spinner='dots')
    spinner.start('正在新建打卡实例...')
    ci = CheckIn(username, password)
    spinner.succeed('已新建打卡实例')

    spinner.start(text='登录到浙大统一身份认证平台...')
    try:
        ci.login()
        spinner.succeed('已登录到浙大统一身份认证平台')
    except Exception as err:
        spinner.fail(str(err))
        return

    spinner.start(text='正在获取个人信息...')
    try:
        ci.get_info()
        spinner.succeed('%s %s同学, 你好~' %(ci.info['number'], ci.info['name']))
    except Exception as err:
        spinner.fail('获取信息失败，请手动打卡，更多信息: ' + str(err))
        return

    spinner.start(text='正在为您打卡打卡打卡')
    try:
        res = ci.post()
        if str(res['e']) == '0':
            spinner.stop_and_persist(symbol='🦄 '.encode('utf-8'), text='已为您打卡成功！')
        else:
            spinner.stop_and_persist(symbol='🦄 '.encode('utf-8'), text=res['m'])

        # Random time
        random_time = random.randint(0, 60) + hour * 60 + minute
        random_hour = random_time // 60
        random_minute = random_time % 60
        weekday = (datetime.datetime.now().weekday() + 1) % 7

        # Schedule task
        scheduler.add_job(main, 'cron', id='checkin_ontime', args=[username, password], day_of_week=weekday, hour=random_hour, minute=random_minute)
        print('⏰ 已启动定时程序，明天 %02d:%02d 为您打卡' %(int(random_hour), int(random_minute)))
        print('Press Ctrl+{0} to exit'.format('Break' if os.name == 'nt' else 'C'))
    except:
        spinner.fail('数据提交失败')
        return 


def test():
    try:
        scheduler.remove_job('checkin_ontime')
    except JobLookupError as e:
        pass
    print("\n[Time] %s" %datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
    print("Run once")

    # Schedule task
    random_time = random.randint(-10, 10)
    print(random_time)
    hour = int(datetime.datetime.now().strftime('%H'))
    minute = int(datetime.datetime.now().strftime('%M'))
    if minute + 1 >= 60:
        hour += 1
        minute = 0
    if hour >= 24:
        hour = 0
    scheduler.add_job(test, 'cron', id='checkin_ontime', hour=hour, minute=minute + 1, second=30 + random_time)


def parse_args():
    parser = argparse.ArgumentParser("Auto CheckIn")
    parser.add_argument("-c", "--config", action="store_true", help="Use config file")
    args = parser.parse_args()
    return args


if __name__=="__main__":
    args = parse_args()
    cfg_file = Path(__file__).parent / "config.json"

    if args.config and cfg_file.exists():
        configs = json.loads(cfg_file.read_bytes())
        username = configs["username"]
        password = configs["password"]
        hour = int(configs["schedule"]["hour"])
        minute = int(configs["schedule"]["minute"])
    else:
        username = input("👤 浙大统一认证用户名: ")
        password = getpass.getpass('🔑 浙大统一认证密码: ')
        print("⏲  请输入锚点时间(默认为 00:05, 向上浮动1小时, 如 00:05 将对应 00:05-01:05 打卡):")
        hour = input("\thour: ") or hour
        hour = int(hour)
        minute = input("\tminute: ") or minute
        minute = int(minute)

    main(username, password)
    # test()

    try:
        scheduler.start()
    except (KeyboardInterrupt, SystemExit):
        pass
