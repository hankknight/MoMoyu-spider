import os
import requests
import threading

from lxml import etree
from queue import Queue
from util import folder
from config import settings


class MooYu(object):

    def __init__(self):
        self.temp_url = settings.ROOT_URL + "/illust/index_{}.html"
        self.headers = settings.HEADERS
        self.url_queue = Queue()  # url网址队列
        self.html_queue = Queue()  # html对象队列
        self.detail_queue = Queue()  # 详情页内容队列
        self.path = "./img"

    def get_url_list(self):
        """准备url地址数据"""
        for i in range(1, settings.PAGE + 1):
            self.url_queue.put(self.temp_url.format(i))

    def parse_url(self):
        """生成html对象"""
        while True:
            url = self.url_queue.get()
            response = requests.get(url, headers=self.headers)
            # print(response)

            if response.status_code != 200:
                self.url_queue.put(url)
            else:
                self.html_queue.put(response.content.decode(settings.CODING))
            self.url_queue.task_done()  # url请求队列计数-1

            # url队列为空，结束循环
            if self.url_queue.empty():
                break

    def get_content_list(self):
        """具体数据的提取"""
        while True:
            html_str = self.html_queue.get()
            html_obj = etree.HTML(html_str)
            div_list = html_obj.xpath("//div[@class='line']")
            for div in div_list:
                self.url_queue.put(settings.ROOT_URL + div.xpath("./div[1]/a/@href")[0])

    def get_detail_list(self):
        """获取详情数据"""
        while True:
            html_str = self.html_queue.get()
            html_obj = etree.HTML(html_str)
            img = html_obj.xpath("//div[@class='showpic']//li//img/@src")
            self.detail_queue.put(img)
            self.html_queue.task_done()

    def save_img(self):
        """保存图片"""
        while True:
            img_list = self.detail_queue.get()
            for img in img_list:
                img_name = os.path.basename(img)  # 提取最后一个/的内容
                resp = requests.get(img, headers=self.headers)
                with open(os.path.join(self.path, img_name), 'wb') as f:
                    f.write(resp.content)
            self.detail_queue.task_done()

    @folder.folder
    def run(self):
        """实现主要逻辑"""
        threading_list = []
        # 1 准备url列表
        t_url = threading.Thread(target=self.get_url_list)
        threading_list.append(t_url)
        # 2 发送请求，网页的响应
        for i in range(3):
            t_parse = threading.Thread(target=self.parse_url)
            threading_list.append(t_parse)
        # 3 数据提取
        t_content = threading.Thread(target=self.get_content_list)
        threading_list.append(t_content)

        # 4 进入详情页面
        t_detail = threading.Thread(target=self.get_detail_list)
        threading_list.append(t_detail)

        # 5 保存内容
        t_save = threading.Thread(target=self.save_img)
        threading_list.append(t_save)

        # 开启线程，进行线程守护
        for t in threading_list:
            t.setDaemon(True)
            t.start()

        # 让主线程阻塞，等待队列计算为0
        t_list = [self.url_queue, self.html_queue, self.detail_queue]
        for q in t_list:
            q.join()

