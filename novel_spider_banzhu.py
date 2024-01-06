import bs4
from bs4 import BeautifulSoup
import time

from selenium.webdriver.common.by import By

from tools import WebDriver, Replace


class SpiderBanZhu:

    def __init__(self, driver_path: str, driver_option: list):
        webdriver = WebDriver(driver_path, driver_option)
        self._browser = webdriver.start_browser()
        self._replace = Replace(r'./replace/replacePictureFont.json',
                                r'./replace/replaceIconFont.json')
        self.cf_clearance = ''
        self.cf_referer = ''
        self.baseurl = ''
        self.default = 5
        self._menu()

    def _menu(self):
        print("====================")
        print("欢迎进入系统")
        print("====================")
        print(f'请指定网站地址 https://????? ')
        self.baseurl = input('url: ')
        print(f'请手动获取 cf_clearance ')
        self.cf_clearance = input('cf_clearance: ')
        print(f'请手动获取 cf_referer ')
        self.cf_referer = input('cf_referer: ')
        print("====================")
        print('系统初始化。。。')
        try:
            self._verify(self.baseurl)
            self._check()
        except BaseException:  # noqa
            print('初始化异常，程序退出')
            return 0
        print('初始化成功')
        print("====================")
        print('1.搜索')
        print('2.下载')
        print('6.退出')
        print("====================")
        while True:
            flag = input('请选择功能: ')
            if flag == '1':
                self._search()
            elif flag == '2':
                self._download()
            elif flag == '6':
                self._browser.quit()
                break
            else:
                print('无此功能')
                continue
        print('退出系统')

    def _search(self):
        key = input('请输入关键字(exit 退出): ')
        if key == 'exit':
            return 0
        self._browser.find_element(By.CSS_SELECTOR, '.text-border').send_keys(key)
        time.sleep(1)
        self._browser.find_element(By.CSS_SELECTOR, '.btn').click()
        time.sleep(self.default)
        while True:
            self._check()
            chap_text = []
            chap_link = []
            link = self._browser.find_elements(By.CSS_SELECTOR, 'li.column-2 > div > a:nth-child(1)')
            for each in link:
                chap_text.append(each.text)
                chap_link.append(each.get_attribute('href'))
            print('====================')
            print("name | url")
            for each in range(len(chap_text)):
                print(f'{chap_text[each]} | {chap_link[each]}')
            print('====================')
            next_page = input('前往下一页(q 退出): ')
            if next_page == 'q':
                print('结束搜索')
                print('====================')
                break
            else:
                self._browser.find_element(By.CSS_SELECTOR, '.nextPage').click()
                continue

    def _download(self):
        url = input('请输入链接 /?????/ (exit 退出): ')
        if url == 'exit':
            return 0
        self._browser.get(self.baseurl + url)
        time.sleep(self.default)
        self._check()
        novel_name = self._browser.find_element(By.CSS_SELECTOR, '.right > h1:nth-child(1)').text
        novel_author = self._browser.find_element(By.CSS_SELECTOR, 'p.info').text.split('\n')[0].replace('作者：', '')
        print("====================")
        print(novel_name)
        print(novel_author)
        print("====================")
        print('开始获取章节目录')
        catalog = self.get_catalog()
        print("====================")
        target = input('请输入开始章节，从 0 开始：')
        try:
            target = int(target)
        except BaseException:  # noqa
            target = 0
        print('跳转。。。')
        for value in catalog[target].values():
            url = value
        self._browser.get(url)
        print("====================")
        print("下载开始")
        while True:
            time.sleep(self.default)
            self._check()
            content = self.get_content()
            with open(f'./result/[{novel_author}] {novel_name}{target}.txt', 'wb') as f:
                for _ in content:
                    f.write(_.encode('UTF-8'))
                    f.write('\n\n'.encode('UTF-8'))
            target += 1
            if target < len(catalog):
                for value in catalog[target].values():
                    url = value
                self._browser.get(url)
            else:
                print('下载结束')
                print("====================")
                break

    def _verify(self, url):
        """进行验证绕过"""
        self._browser.get(url)
        self._browser.add_cookie({'name': 'cf_clearance', 'value': self.cf_clearance})
        self._browser.get(url + '/?__cf_chl_tk=' + self.cf_referer)
        time.sleep(self.default)
        self._browser.find_element(By.CSS_SELECTOR, '#password').send_keys('1234')
        self._browser.find_element(By.CSS_SELECTOR, '.login').click()
        time.sleep(self.default)

    def _check(self):
        """检查页面是否正常"""
        while True:
            try:
                self._browser.find_element(By.CSS_SELECTOR, '.logo img')
                break
            except BaseException:  # noqa
                print('跳转异常，重试中。。。')
                self._browser.refresh()
                time.sleep(self.default)

    def get_catalog(self):
        catalog = []
        flag = 0
        page = -1
        while True:
            node = self._browser.find_elements(By.CSS_SELECTOR, 'div.mod:nth-child(7) a')
            for each in node:
                catalog_name = f'【{flag}】{each.text}'
                catalog_link = each.get_attribute('href')
                catalog.append({catalog_name: catalog_link})
                flag += 1
            _next = self._browser.find_element(By.CSS_SELECTOR, '.nextPage')
            _end = self._browser.find_element(By.CSS_SELECTOR, '.endPage')
            if _next.get_attribute('href') == _end.get_attribute('href'):
                if page != 0:
                    page += 1
                else:
                    break
            _next.click()
            time.sleep(self.default)
            self._check()
        return catalog

    def get_content(self):
        print(self._browser.current_url)
        page = len(self._browser.find_elements(By.CSS_SELECTOR, 'center.chapterPages a'))
        if page == 0:
            content_page = range(1)
        else:
            content_page = range(page)  # 分页
        content = []
        for _ in content_page:
            if len(self._browser.find_elements(By.CSS_SELECTOR, '#chapterinfo')) != 0:
                content_html = self._browser.find_element(By.CSS_SELECTOR, '#chapterinfo')
                content = self.content_decode(content_html.get_attribute("outerHTML"), 'chapterinfo')
            elif len(self._browser.find_elements(By.CSS_SELECTOR, '#ad')) != 0:
                content_html = self._browser.find_element(By.CSS_SELECTOR, '#ad')
                new_content = self.content_decode(content_html.get_attribute("outerHTML"), 'ad')
                content = content + new_content
            else:
                content_html = self._browser.find_element(By.CSS_SELECTOR, 'div.neirong')
                new_content = self.content_decode(content_html.get_attribute("outerHTML"), 'neirong', 'class')
                content = content + new_content
            if _ + 1 < len(content_page):
                self._browser.find_elements(By.CSS_SELECTOR, 'center.chapterPages a')[_ + 1].click()
                time.sleep(self.default)
                self._check()
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
                content_temp = content_temp + self._replace.picture_font_reverse(img_id)
            elif _.name == 'i':
                iconfont = _.contents[0]
                icon_id = repr(iconfont).replace(r"\ue", "").replace('\'', '')
                content_temp = content_temp + self._replace.icon_font_reverse(icon_id)
            elif _.name == 'div':
                content = content + self.content_decode(_, '')
        if (content_temp not in content) and (content_temp != ''):
            content.append(content_temp)
        return content
