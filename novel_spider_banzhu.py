import sys
from urllib.parse import urljoin

import bs4
from bs4 import BeautifulSoup
import time

from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as ec

from tools import WebDriver, Replace


class SpiderBanZhu:

    def __init__(self, driver_path: str, driver_option: list=None):
        self.webdriver = WebDriver(driver_path, driver_option)
        self.browser = None
        self.cf_clearance = None
        self.cf_referer = None
        self.baseurl = None
        self.default = 3
        self.replace = Replace(r'./replace/replacePictureFont.json', r'./replace/replaceIconFont.json')
        # 启动菜单
        self.menu()

    def menu(self):
        print("====================")
        print("欢迎进入系统")
        print("====================")
        print(f'请指定网站地址 https://????? ')
        self.baseurl = input('url: ')
        print(f'是否具有 Cloudflare 盾？')
        if input('Yes(y) or No(n,Enter): ') == 'y':
            print(f'请手动获取 cf_clearance ')
            self.cf_clearance = input('cf_clearance: ')
            print(f'请手动获取 cf_referer ')
            self.cf_referer = input('cf_referer: ')
        else:
            pass
        print("====================")
        print('系统初始化。。。')
        # 启动浏览器
        self.browser = self.webdriver.start_browser()
        if self.cf_clearance:
            # 绕过验证
            self.verify()
        else:
            self.browser.get(self.baseurl)
            self.check()
        print('初始化成功')
        print("====================")
        print('1.搜索')
        print('2.下载')
        print('6.退出')
        print("====================")
        while True:
            flag = input('请选择功能: ')
            if flag == '1':
                self.search()
            elif flag == '2':
                self.download()
            elif flag == '6':
                self.browser.quit()
                break
            else:
                print('无此功能')
                continue
        print('退出系统')

    def verify(self):
        print("进行验证绕过！")
        self.browser.get(self.baseurl)
        self.browser.execute_script('window.stop()')
        self.browser.add_cookie({'name': 'cf_clearance', 'value': self.cf_clearance})
        self.browser.get(urljoin(self.baseurl, f'/?__cf_chl_tk={self.cf_referer}'))
        try:
            print('检查登录状态！')
            # 检查左上角是否有 LOGO
            WebDriverWait(
                self.browser, self.default, 1
            ).until(
                ec.visibility_of_element_located((By.CSS_SELECTOR, '.logo img'))
            )
        except BaseException:  # noqa
            print('未登录，执行登录操作！')
            self.find_element('#password').send_keys('1234')
            time.sleep(1)
            self.find_element('.login').click()
            time.sleep(3)
        # 检查网站是否正常
        self.check()

    def find_element(self, css, strong=True):
        try:
            element = self.browser.find_element(By.CSS_SELECTOR, css)
            return element
        except BaseException as e:
            print(e)
            if not strong:
                return None
            sys.exit('find_element 元素定位异常，请检查，程序退出！')

    def find_elements(self, css, strong=True):
        try:
            element = self.browser.find_elements(By.CSS_SELECTOR, css)
            return element
        except BaseException as e:
            print(e)
            if not strong:
                return None
            sys.exit('find_elements 元素定位异常，请检查，程序退出！')

    def check(self):
        """检查页面是否正常（尝试 5 次，10 s 每 2 s 一次）"""
        print('检查页面正常...')
        time.sleep(self.default)
        try:
            WebDriverWait(
                self.browser, 10, 1
            ).until(
                ec.visibility_of_element_located((By.CSS_SELECTOR, '.logo img'))
            )
            WebDriverWait(
                self.browser, 10, 1
            ).until(
                ec.visibility_of_element_located((By.CSS_SELECTOR, '.container'))
            )
        except BaseException as e:  # noqa
            print(e)
            sys.exit('check 页面异常，请检查，程序退出！')

    def search(self):
        key = input('请输入关键字(exit 退出): ')
        if key == 'exit':
            return 0
        self.find_element('.text-border').send_keys(key)
        time.sleep(2)
        self.find_element('.btn').click()
        while True:
            self.check()
            chap_text = []
            chap_link = []
            link = self.find_elements('li.column-2 > div > a:nth-child(1)')
            for each in link:
                chap_text.append(each.text)
                chap_link.append(each.get_attribute('href'))
            print('====================')
            print("name | url")
            for each in range(len(chap_text)):
                print(f'{chap_text[each]} | {chap_link[each]}')
            print('====================')
            next_page = input('q 退出: ')
            if next_page == 'q':
                print('结束搜索')
                print('====================')
                break
            else:
                ele = self.find_element('.nextPage', strong=False)
                if ele:
                    ele.click()
                    continue
                break

    def download(self):
        url = input('请输入链接 /?????/ (exit 退出): ')
        if url == 'exit':
            return 0
        if self.baseurl in url:
            self.browser.get(url)
        else:
            self.browser.get(urljoin(self.baseurl, url))
        self.check()
        novel_name = self.find_element('.right > h1:nth-child(1)').text
        novel_author = self.find_element('p.info').text.split('\n')[0].replace('作者：', '')
        print("====================")
        print(novel_name)
        print(novel_author)
        print("====================")
        if input('是否开始下载(exit 退出): ') == 'exit':
            return 0
        print("====================")
        print('开始获取章节目录')
        catalog = self.get_catalog()
        print("====================")
        print(f'总共 {len(catalog)} 章')
        target = input('请输入开始章节，从 1 开始：')
        try:
            target = int(target) - 1
        except BaseException:  # noqa
            target = 0
        print("====================")
        print("下载开始")
        for value in catalog[target].values():
            url = value
        self.browser.get(url)
        while True:
            self.check()
            content = self.get_content()
            with open(f'./result/[{novel_author}] {novel_name}{target}.txt', 'wb') as f:
                for _ in content:
                    f.write(_.encode('UTF-8'))
                    f.write('\n\n'.encode('UTF-8'))
            target += 1
            if target < len(catalog):
                for value in catalog[target].values():
                    url = value
                self.browser.get(url)
            else:
                print('下载结束')
                print("====================")
                break

    def get_catalog(self):
        catalog = []
        flag = 0
        while True:
            node = self.find_elements('div.mod:nth-child(7) a')
            for each in node:
                catalog_name = f'【{flag}】{each.text}'
                catalog_link = each.get_attribute('href')
                if self.baseurl not in catalog_link:
                    catalog_link = urljoin(self.baseurl, catalog_link)
                catalog.append({catalog_name: catalog_link})
                flag += 1
            print('请确认是否存在分页，并跳转到下一页')
            if input('Yes(y) or No(n,Enter): ') == 'y':
                self.check()
                print('获取章节中...')
                continue
            else:
                break
        return catalog

    def get_content(self):
        page_number = len(self.find_elements('center.chapterPages a'))
        print(self.browser.current_url)
        print(f'分页：{page_number}')
        if page_number == 0:
            content_page = range(1)
        else:
            content_page = range(page_number+1)  # 分页
        content = None
        for _ in content_page:
            print(f'当前：{_}')
            content_html = self.find_element('#nr1', strong=False)
            if content_html:
                if content is None:
                    content = self.content_decode(content_html.get_attribute("outerHTML"), 'nr1')
                else:
                    new_content = self.content_decode(content_html.get_attribute("outerHTML"), 'nr1')
                    content += new_content
            if _ == page_number:
                break
            next_page = self.find_elements('center.chapterPages a')[_]
            next_page.click()
            self.check()
        return content

    def content_decode(self, content_html, target, target_type='id'):
        """正文解码"""
        content = []
        content_temp = ''
        if target != '':
            soup = BeautifulSoup(content_html, 'html.parser')
            if target_type == 'class':
                div = soup.find('div', class_=target)
            else:
                div = soup.find('div', id=target)
        else:
            div = content_html
        for _ in div:
            if isinstance(_, bs4.element.NavigableString):
                content_temp = content_temp + _.strip()
            elif _.name == 'br':
                if (content_temp not in content) and (content_temp != ''):
                    content.append(content_temp)
                    content_temp = ''
            elif _.name == 'img':
                img_id = _.get('src').replace('/toimg/data/', '')
                content_temp = content_temp + self.replace.picture_font_reverse(img_id)
            elif _.name == 'i':
                iconfont = _.contents[0]
                icon_id = repr(iconfont).replace(r"\ue", "").replace('\'', '')
                content_temp = content_temp + self.replace.icon_font_reverse(icon_id)
            elif _.name == 'div':
                content = content + self.content_decode(_, '')
        if (content_temp not in content) and (content_temp != ''):
            content.append(content_temp)
        return content

if __name__ == '__main__':
    SpiderBanZhu(r'F:\Sdk\webdriver\geckodriver.exe')
    # 测试地址: https://m.05banzhu.store/
