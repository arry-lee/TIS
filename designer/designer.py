"""
基于爬取第三方接口实现的模板设计师模块
实现任意类型的平面设计
# cookie 和 authorization_header 需要从浏览器登录之后更新

"""
import concurrent.futures
import functools
import os.path
import re
import time
from hashlib import md5

import requests

# for json type use

null = None
true = True
false = False

# logger = getLogger(__name__)
# ch = logging.StreamHandler(sys.stdout)
# ch.setLevel(logging.DEBUG)
# logger.addHandler(ch)

headers = """\
accept: text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9
accept-encoding: gzip, deflate, br
accept-language: zh-CN,zh;q=0.9
cache-control: max-age=0
cookie: __wpkreporterwid_=8cefd0b4-c5d8-4986-bc41-8b0ad7414ff3; user_device_id=44d1c11886844cd39cce79907412ea0f; user_device_id_timestamp=1661323662644; gd.sid=v4r30Utn-ar41c37GInlLRwttz05Ydsg; gd.sid.sig=ffbA_9XCJsHdjFUTkras_5lT1X0; canary_uuid=1fdb56e9a3084f2e99c581989238a3db; new_user_lock=1; aliyungf_tc=e23fdfe5b52a2ec353457e64779249e1d0effdc54fb037c7dbe723c5e20eeb75; acw_tc=2f6fc10116672942343138707e5c2a3d1330e74b892ab3780e486a000b5249; Hm_lvt_fdafb975c7b15a614fe2dd7716c44e87=1666682102,1666708744,1666773332,1667294237; Hm_lpvt_fdafb975c7b15a614fe2dd7716c44e87=1667294237; _gid=GA1.2.1819567336.1667294238; _ga_GNS4BGH70N=GS1.1.1667294237.21.0.1667294237.0.0.0; _ga=GA1.1.1881071411.1666285499; token.prod=eyJhY2Nlc3NfdG9rZW4iOiJleUowZVhBaU9pSnFkM1FpTENKaGJHY2lPaUpJVXpJMU5pSjkuZXlKcGMzTWlPaUoxYlhNaUxDSnpkV0lpT2pFM05qWTVOekU1TkRZc0ltRjFaQ0k2SW1kaGIyUnBibWQ0SWl3aVpYaHdJam94TmpZM05EWTNNRE0zTENKcWRHa2lPaUl3WVRFell6QTJPR1ExTm1GbE1qbGpPR1kwWldGalpqWmlNelV4TXpsaFpUQTVNRFZoTVRReEluMC5iWFdyQjN6NWlhTEUzOTFERXNpemFLQjRoVXV6ZnZFcFBQU3ZvRUVCUFRjIiwiYWNjZXNzX3Rva2VuX2V4cGlyZXNfYXQiOiIyMDIyLTExLTAzVDA5OjE3OjE3LjAwMFoiLCJhY2Nlc3NfdG9rZW5fbGlmZV90aW1lIjoxNzI4MDAsInJlZnJlc2hfdG9rZW4iOiJhYjMyY2Q5NTA1N2EyN2UzMTkzZDU5YjU2ODAyMDdhNTY4NDQ2YzM4IiwicmVmcmVzaF90b2tlbl9leHBpcmVzX2F0IjoiMjAyMi0xMS0xNlQwOToxNzoxNy41MjFaIiwicmVmcmVzaF90b2tlbl9saWZlX3RpbWUiOjEyOTYwMDAsInRpbWVzdGFtcCI6MTY2NzI5NDIzODM4N30=; gray-user.prod=0; _dd_s=logs=1&id=04166d9c-5f16-4fd3-9caf-1eaebb445460&created=1667294237675&expire=1667295197049
sec-ch-ua: ".Not/A)Brand";v="99", "Google Chrome";v="103", "Chromium";v="103"
sec-ch-ua-mobile: ?0
sec-ch-ua-platform: "Windows"
sec-fetch-dest: document
sec-fetch-mode: navigate
sec-fetch-site: same-origin
sec-fetch-user: ?1
upgrade-insecure-requests: 1
user-agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/103.0.0.0 Safari/537.36
"""
headers = dict(line.split(": ", 1) for line in headers.splitlines() if line)

authorization_header = {
    "authorization": "Bearer eyJ0eXAiOiJqd3QiLCJhbGciOiJIUzI1NiJ9.eyJpc3MiOiJ1bXMiLCJzdWIiOjE3NjY5NzE5NDYsImF1ZCI6Imdhb2Rpbmd4IiwiZXhwIjoxNjY3NDY3MDM3LCJqdGkiOiIwYTEzYzA2OGQ1NmFlMjljOGY0ZWFjZjZiMzUxMzlhZTA5MDVhMTQxIn0.bXWrB3z5iaLE391DEsizaKB4hUuzfvEpPPSvoEEBPTc"}

class Designer:
    """设计者类,提供模板ID即可下载PDF"""
    
    sess = requests.Session()
    sess.headers = headers
    
    max_retry_times = 30
    sleep_time = 2
    
    # 第0步，登录
    def open_template(self, template_id=88797, category_id=None):
        print("Opening Template")
        if category_id:
            template_url = f"https://www.gaoding.com/design?id={template_id}&category_id={category_id}"
        else:
            template_url = f"https://www.gaoding.com/design?id={template_id}"
        resp = self.sess.get(template_url)
        return resp
    
    def get_token(self):
        print("Getting Token")
        token_url = "https://www.gaoding.com/api/filems/access/token"
        resp = self.sess.get(token_url)
        token = resp.json()
        print(f'Token is {token["auth_key"]}')
        return token["auth_key"]
    
    def get_me(self):
        print("Getting User")
        me_url = "https://www.gaoding.com/api/users/me"
        self.sess.headers.update({
            "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9",
            # "refer":null,
        })
        resp = self.sess.get(me_url)
        print(resp)
        me = resp.json()
        me_id = me.get("id")
        repository_id = None
        for one in me.get("repositories"):
            if one["type"] == 1:
                repository_id = one["id"]
                break
        print(f"me_id:{me_id}, repository_id:{repository_id}")
        return me_id, repository_id
    
    def get_user(self):
        user_url = "https://www.gaoding.com/api/structure/gray/user"
        resp = self.sess.get(user_url)
        user = resp.json()
        # user = {"ums_id": "1766971946", "status": "2"}
        return user
    
    def get_template_info(self, user_id, template_id):
        print("Getting Template Info")
        info_url = f"https://www.gaoding.com/api/open/editor/materials/{template_id}/info?user_id={user_id}&region_id=1&biz_code=1&endpoint=4&is_free="
        resp = self.sess.get(info_url)
        info = resp.json()
        print("Getting Template Info Success")
        return info
    
    @staticmethod
    def patch_info(info, template_id, user_id, repository_id):
        sp_info = {
            "id"           : template_id,
            "source_id"    : template_id,
            "user_id"      : str(user_id),
            "repository_id": repository_id,
            "shot"         : true,
            "shot_config"  : {"delay": 60000},
            "channel_id"   : 8,
        }
        info.update(sp_info)
        return info
    
    def post_template_info(self, info_post):
        """
        :param info_post: 数据字典
        :return: target_id
        """
        print("Post Template Info")
        info_url = "https://www.gaoding.com/api/open/editor/dam/editors/materials/info"
        # 继承自info
        info_resp = self.sess.post(info_url, json=info_post,
                                   headers=authorization_header)
        print(info_resp)
        info_resp = info_resp.json()
        print(f"Get Target ID {info_resp.get('id')}")
        return info_resp.get("id")
    
    def put_editor_info(self, target_id, info_put):
        print("put_editor_info")
        info_url = f"https://www.gaoding.com/api/open/editor/dam/editors/materials/{target_id}/info"
        info_resp = self.sess.put(info_url, json=info_put).json()
        print(info_resp)
        return info_resp
    
    def post_render_task(self, user_id, target_id):
        print("post_render_task")
        render_url = "https://www.gaoding.com/api/open/editor/media-render"
        render_post = {
            "mode"         : "user",
            "user_id"      : user_id,
            "target_id"    : target_id,
            "export_config": {
                "from"            : "dam",
                "type"            : "template",
                "export_type"     : "pdf",
                "indexes"         : "0,1",
                "format"          : "",
                "timeout"         : 180000,
                "shot_enable"     : true,
                "watermark_enable": true,
            },
        }
        
        render_resp = self.sess.post(render_url, json=render_post,
                                     headers=authorization_header).json()
        # render_resp = {"id": 1275483, "task_id": "1799832589"}
        print(render_resp)
        print(f"task id is {render_resp.get('id')}")
        return render_resp.get("id")
    
    def get_render_result(self, task_id):
        print("Getting Render Result")
        result_url = (
            f"https://www.gaoding.com/api/open/editor/media-render?id={task_id}"
        )
        
        result_resp = self.sess.get(result_url,
                                    headers=authorization_header).json()
        if int(result_resp.get("status")) == 1:
            print("Getting Render Result Success")
            return result_resp["result"]["url"]
        print("Getting Render Result Failed")
        return None
    
    def download_pdf(self, pdf_url, save_dir="."):
        print("Downloading PDF")
        resp = self.sess.get(pdf_url)
        fname = md5(pdf_url.encode()).hexdigest() + ".pdf"
        path = os.path.join(save_dir, fname)
        with open(path, "wb") as f:
            f.write(resp.content)
        print("Downloading PDF Success")
        return path
    
    def load(self, template_id, category_id=None, save_dir="."):
        # 第一步，打开模板
        self.open_template(template_id, category_id)
        # 第二步，获取token
        self.get_token()
        # 第三步，获取个人信息
        user_id, repository_id = self.get_me()  # 1766971946,96428059#
        # self.get_user()
        # 第四步，获取模板信息
        info = self.get_template_info(user_id, template_id)
        print(info)
        # 第五步，点击下载
        info_post = self.patch_info(info, template_id, user_id, repository_id)
        # print(info_post)
        target_id = self.post_template_info(info_post)
        # # 第六步，下载
        # put_editor_info(target_id,info_post)
        # 第七步，提交渲染任务
        task_id = self.post_render_task(user_id, target_id)
        # 第八步，轮询
        cnt = 0
        pdf_url = None
        while cnt < self.max_retry_times:
            pdf_url = self.get_render_result(task_id)
            if pdf_url:
                break
            time.sleep(self.sleep_time)
            cnt += 1
        if pdf_url is None:
            raise TimeoutError(
                f"{self.max_retry_times * self.sleep_time}s time out ")
        # 第九步，下载PDF
        return self.download_pdf(pdf_url, save_dir)
    
    def load_all(self,templates,save_dir):
        """多线程下载全部的模板PDF"""
        
        download_method = functools.partial(self.load,save_dir=save_dir)
        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as exe:
            for a in exe.map(download_method, templates):
                print(a)
                
    def batch_pull(self, wordlist):
        url = "https://www.gaoding.com/api/v3/oc/search-directs/batch-pull"
        if isinstance(wordlist, str):
            wordlist = [wordlist]
        data = {"keywords": wordlist}
        self.sess.headers.update(
            {
                "content-type" : "application/json",
                "referer"      : "https://www.gaoding.com/templates/f4814229",
                "x-business-id": "1",
                "x-channel-id" : "8",
                "x-device-id"  : "44d1c11886844cd39cce79907412ea0f",
            }
        )
        resp = self.sess.post(url, json=data)
        print(resp)
        return resp.json()
    
    def get_filters(self, mode="pricelist123"):
        """获取资源的过滤器"""
        resources_url = (
            f"https://www.gaoding.com/api/v3/cp/exhibitions/{mode}/resources"
        )
        self.sess.headers.update(
            {
                "x-business-id": "1",
                "x-channel-id" : "8",
                "x-device-id"  : "44d1c11886844cd39cce79907412ea0f",
            }
        )
        resources_resp = self.sess.get(resources_url).json()
        filters = []
        for one in resources_resp["pits"]:
            mts = one.get("materials")
            if mts:
                for mt in mts:
                    filter_value = mt.get("material").get("filter").get("value")
                    # print(filter)
                    
                    filters.append(filter_value)
        return filters
    
    def recommend(self, filters, page_num=1, page_size=50):
        """推荐系统推荐相关的模板
        返回模板列表
        """
        filter_nodes = []
        for filter_value in filters:
            filter_node = {"id": filter_value, "type": 1, "children": []}
            filter_nodes.append(filter_node)
            break
        
        recommend_url = (
            "https://www.gaoding.com/api/v3/cp/template-centers/v2/recommend-templates"
        )
        recommend_post = {
            "page_num"    : page_num,
            "page_size"   : page_size,
            "styles"      : [],
            "colors"      : [],
            "filter_nodes": filter_nodes,
            "is_group"    : true,
        }
        return self.sess.post(recommend_url, json=recommend_post).json()
    
    def search(self, word, page_num=1, page_size=50):
        """根据单词查找指定数量的模板"""
        url = self.batch_pull(word)[0]
        print(url)
        if "?" in url:
            url = url.split("?")[0]
        print(url)
        mode = url.rsplit("/", 1)[1]
        print(mode)
        filters = self.get_filters(mode)
        print(filters)
        recommend_result = self.recommend(filters, page_num, page_size)
        print(recommend_result)
        return [one["id"] for one in recommend_result]
    
    def get_templates_from_url(self, url):
        s = url.removeprefix(
            "https://www.gaoding.com/templates/fc").removesuffix(
            "?is_group=true")
        f1, f23 = s.split('-')
        f2, f3 = f23[1:].split(',')
        api = f"https://www.gaoding.com/api/v3/bp/search-contents/templates/search?page_size=120&page_num=1&q=&design_cid=&channel_cid=&industry_cid=&filter_id={f2}%2C{f3}%2C{f1}&type_filter_id={f2}%2C{f3}&channel_filter_id={f1}&channel_children_filter_id=&sort=&styles=&colors=&ratios=&is_group=true&user_id=1766971946"
        
        headers = {
            "x-business-id": "1",
            "x-channel-id" : "8",
            "x-device-id"  : "44d1c11886844cd39cce79907412ea0f",
        }
        resp = self.sess.get(api, headers=headers).json()
        # print(resp)
        return [one['id'] for one in resp]

def parse_html(path):
    with open(path,'r',encoding='utf-8') as file:
        text = file.read()
    pat = re.compile(r"/template/(\d+)")
    res = pat.findall(text)
    print(res)
    return res


if __name__ == "__main__":
    res = parse_html(r"E:\00IT\P\uniform\multilang\temp\bussinescard.html")
    d = Designer()
    print(len(res))
    d.load_all(res,save_dir='../templates/businesscard/')
    # for one in tqdm.tqdm(res):
    #     d.load(int(one),save_dir=r'E:\00IT\P\uniform\multilang\templates\coupons')
    # d.get_templates_from_url(
    #     "https://www.gaoding.com/templates/fc4815045-f4814229,4814234?is_group=true")
    # # d.load(48205953)
    # for one in d.search("名片",page_size=200):
    #     d.load(one,save_dir='../templates/businesscard/')
