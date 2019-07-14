import pymongo
from selenium import webdriver
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.wait import WebDriverWait
from pyquery import PyQuery as pq
from urllib.parse import quote
import requests
import os
from hashlib import md5

# browser = webdriver.Chrome()
# browser = webdriver.PhantomJS(service_args=SERVICE_ARGS)
MONGO_URL = 'localhost'
MONGO_DB = 'taobao'
KEYWORD = 'ps4'
MONGO_COLLECTION = KEYWORD
MAX_PAGE = 10
url = 'https://login.taobao.com/member/login.jhtml'
chromedriver_path = "D:/MyPython/Scripts/chromedriver.exe"  # 改成你的chromedriver的完整路径地址
weibo_username = "改成你的微博账号"  # 改成你的微博账号
weibo_password = "改成你的微博密码"  # 改成你的微博密码

options = webdriver.ChromeOptions()
options.add_experimental_option('excludeSwitches',
                                ['enable-automation'])  # 此步骤很重要，设置为开发者模式，防止被各大网站识别出来使用了Selenium
browser = webdriver.Chrome(executable_path=chromedriver_path, options=options)
wait = WebDriverWait(browser, 10)  # 超时时长为10s
#chrome_options.add_argument('--headless')
client = pymongo.MongoClient(MONGO_URL)
db = client[MONGO_DB]
browser.get(url)

def index_page(page):
    """
    抓取索引页
    :param page: 页码
    """
    print('正在爬取第', page, '页')
    try:
        url = 'https://s.taobao.com/search?q=' + quote(KEYWORD)
        browser.get(url)
        #下面if里面的代码实现页面跳转
        if page > 1:
            input = wait.until(
                EC.presence_of_element_located((By.CSS_SELECTOR, '#mainsrp-pager div.form > input')))
            submit = wait.until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, '#mainsrp-pager div.form > span.btn.J_Submit')))
            input.clear()
            input.send_keys(page)
            submit.click()
        #等待跳转成功
        wait.until(
            EC.text_to_be_present_in_element((By.CSS_SELECTOR, '#mainsrp-pager li.item.active > span'), str(page)))
        #等待商品加载出来
        wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, '.m-itemlist .items .item')))
        get_products()
    except TimeoutException:
        index_page(page)
    # finally:
    #     results = db[MONGO_COLLECTION].count_documents()
    #     print("A total of "+results+" data were obtained")

def get_products():
    """
    提取商品数据
    """
    html = browser.page_source
    doc = pq(html)
    items = doc('#mainsrp-itemlist .m-itemlist .items .item').items()
    for item in items:
        product = {
            'image': 'https:'+item.find('.pic .img').attr('data-src'),
            'price': item.find('.price').text(),
            'deal': item.find('.deal-cnt').text(),
            'title': item.find('.title').text(),
            'shop': item.find('.shop').text(),
            'location': item.find('.location').text()
        }
        #print(product)
        save_picture(product)
        save_to_mongo(product)
def save_picture(result):
    response = requests.get(result['image'])
    filename = result['title']
    img_path = 'img'
    if not os.path.exists(img_path):
        os.makedirs(img_path)
    try:
        print(response.content)
        if response.status_code == 200:
            file_path = img_path + os.path.sep + '{file_name}.{file_suffix}'.format(
                # file_name=md5(response.content).hexdigest(),
                file_name = filename,
                file_suffix='jpg')
            if not os.path.exists(file_path):
                with open(file_path, 'wb') as f:
                    f.write(response.content)
                print('Downloaded image path is %s' % file_path)
            else:
                print('Already Downloaded', file_path)
    except Exception as e:
        print(e)
def save_to_mongo(result):
    """
    保存至MongoDB
    :param result: 结果
    """
    try:
        if db[MONGO_COLLECTION].insert(result):
            print('Save to MongoDB success!')
    except Exception:
        print('Cannt save to MongoDB!')

def auto_login():

    # 打开网页
    # 等待 密码登录选项 出现
    password_login = wait.until(
        EC.presence_of_element_located((By.CSS_SELECTOR, '.qrcode-login > .login-links > .forget-pwd')))
    password_login.click()

    # 等待 微博登录选项 出现
    weibo_login = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, '.weibo-login')))
    weibo_login.click()

    # 等待 微博账号 出现
    weibo_user = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, '.username > .W_input')))
    weibo_user.send_keys(weibo_username)

    # 等待 微博密码 出现
    weibo_pwd = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, '.password > .W_input')))
    weibo_pwd.send_keys(weibo_password)

    # 等待 登录按钮 出现
    submit = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, '.btn_tip > a > span')))
    submit.click()

    # 直到获取到淘宝会员昵称才能确定是登录成功
    taobao_name = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR,
                                                                  '.site-nav-bd > ul.site-nav-bd-l > li#J_SiteNavLogin > div.site-nav-menu-hd > div.site-nav-user > a.site-nav-login-info-nick ')))
    # 输出淘宝昵称
    print("登陆成功" + taobao_name.text)
def main():
    """
    遍历每一页
    """
    auto_login()
    try:
        for i in range(1, MAX_PAGE + 1):
            index_page(i)
    except BaseException as e :
        print(e)
    browser.close()


if __name__ == '__main__':
    main()
