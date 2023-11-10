import concurrent.futures
import functools
import os
import re
import time
from hashlib import md5

import requests

# for json type use

null = None
true = True
false = False

headers = """\
accept: application/json
accept-encoding: gzip, deflate, br
accept-language: zh-CN,zh;q=0.9
cookie: langKey=en; allowCookies=true; userid=6308922d2da6b05c2a65fae8; token=5D1EY3GtFpi94frAyvSuZ19OmlL6wBrSkVqaLfeG7BbUEHuDCtFdwEIW4ByaH5GO; tourTipsViewed=6; iterableEndUserId=arry_lee@qq.com; noWarBannerViewed=true; addTemplateMethod={"isRepeated":true,"method":"addNewPage"}; features={"exampleFeature":"group2","closedRegistration":"group2","mobileOnboardingToTrial":"group2","newArtboardOnboarding":"groupExcluded","startingFlow":"group1"}; videoEditorTourViewed=2; removeBackgroundTourViewed=true; iwidth=1242; nextDownloadTutorial=2; filterSidebarOpened=true; iheight=581; _dd_s=logs=1&id=faa84fe5-279f-4a69-93df-53c9f19fb555&created=1666163316956&expire=1666164546880
referer: https://create.vista.com/artboard/?formatKey=menuEO&template=62f15b94ca4d77aa72947d26
sec-ch-ua: ".Not/A)Brand";v="99", "Google Chrome";v="103", "Chromium";v="103"
sec-ch-ua-mobile: ?0
sec-ch-ua-platform: "Windows"
sec-fetch-dest: empty
sec-fetch-mode: cors
sec-fetch-site: same-origin
token: 5D1EY3GtFpi94frAyvSuZ19OmlL6wBrSkVqaLfeG7BbUEHuDCtFdwEIW4ByaH5GO
user-agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/103.0.0.0 Safari/537.36
"""
headers = dict(line.split(": ", 1) for line in headers.splitlines() if line)


class VistaDesigner:
    """
    create.vista.com 模板设计师
    """

    sess = requests.Session()
    sess.headers = headers
    url = "https://create.vista.com"
    max_retry_times = 30
    sleep_time = 2
    template_re = re.compile(r'data-value="(\w{24})"')

    def load_all(self, mode, save_dir):
        """多线程下载全部的模板PDF"""
        if "/" in mode:
            templist = self.get_template_from_url(mode)
        else:
            templist = self.get_template_from_type(mode)
        download_method = functools.partial(self.load, save_dir=save_dir)
        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as exe:
            for a in exe.map(download_method, templist):
                print(a)

    def get_template_from_type(self, mode):
        url = f"https://create.vista.com/templates/{mode}/"
        return self.get_template_from_url(url)

    def get_template_from_url(self, url):
        resp = self.sess.get(url)
        templates = []
        if resp.ok:
            temp_list = self.template_re.findall(resp.text)
            templates.extend(temp_list)
        has_next_page = re.compile(
            r'aria-label="Next Page" data-disabled="false" href="(/templates/menu/\?page=\d+)"'
        )
        next_page = has_next_page.search(resp.text)
        if next_page:
            templates.extend(self.get_template_from_url(self.url + next_page[1]))
        return templates

    def load(self, template="62f15b94ca4d77aa72947d26", save_dir="."):
        """按照ID下载模板"""
        print("Getting Template")
        template_json = self._get_template(template)
        project_post = {
            "pageWidth": template_json["pixelWidth"],
            "pageHeight": template_json["pixelHeight"],
            "originalDimensions": {
                "width": str(template_json["width"]),
                "height": str(template_json["height"]),
                "measureUnits": template_json["measureUnits"],
            },
            "format": template_json["format"],
            "group": template_json["group"],
            "pages": template_json["template"],
            "v2": true,
            "minPageDuration": 0,
            "projectType": template_json["templateType"],
            "audio": [],
            "name": f"{template_json['format']} {template_json['width']}x{template_json['height']} {template_json['measureUnits']}",
        }
        print("Getting Project ID")
        project_id = self._get_project_id(project_post)
        print("Creating Task")
        self._put_creat_task(project_id, project_post)
        print("Getting Download ID")
        download_id = self._get_download_id(project_id)
        print("Getting PDF url")
        pdf_url = self._get_pdf_url(download_id)
        # print('Downloading PDF')
        return self.download_pdf(self.url + pdf_url, save_dir)

    def _get_pdf_url(self, download_id):
        cnt = 0
        while cnt < self.max_retry_times:
            check_url = (
                f"https://create.vista.com/api/downloads/{download_id}?pagesRange=1"
            )
            check_resp = self.sess.get(check_url)
            check_json = check_resp.json()
            check_status = check_json["status"] == "completed"
            if check_status:
                pdf_url = check_json["path"]
                return pdf_url
            else:
                cnt += 1
                time.sleep(self.sleep_time)
        raise TimeoutError(f"{self.max_retry_times * self.sleep_time}s time out ")

    def _get_download_id(self, project_id):
        download_url = "https://create.vista.com/api/downloads"
        download_post = {
            "projectId": project_id,
            "options": {
                "format": "pdf",
                "scale": 1,
                "print": true,
                "pagesRange": "1",
                "bleed": true,
                "cropMarks": true,
            },
        }
        download_resp = self.sess.post(download_url, json=download_post)
        download_json = download_resp.json()
        download_id = download_json["id"]
        return download_id

    def _put_creat_task(self, project_id, project_post):
        create_url = f"https://create.vista.com/api/v2/projects/{project_id}"
        # create_put = project_post.update(
        #     {'versionId': '"2022-08-29T02:27:31.943Z"'})
        create_resp = self.sess.put(create_url, json=project_post)
        # create_json = create_resp.json()
        # print(create_resp)

    def _get_project_id(self, project_post):
        project_url = "https://create.vista.com/api/v2/projects"
        token = {
            "token": "5D1EY3GtFpi94frAyvSuZ19OmlL6wBrSkVqaLfeG7BbUEHuDCtFdwEIW4ByaH5GO"
        }
        self.sess.headers.update(token)
        project_resp = self.sess.post(project_url, json=project_post)
        project_json = project_resp.json()
        # print(project_resp, project_json)
        project_id = project_json["id"]
        return project_id

    def _get_template(self, template):
        template_url = f"https://create.vista.com/api/templates/{template}"
        template_resp = self.sess.get(template_url)
        template_json = template_resp.json()
        # print(template_resp)
        # print(template_json)
        return template_json

    def download_pdf(self, pdf_url, save_dir="."):
        print("Downloading PDF")
        resp = self.sess.get(pdf_url)
        fname = md5(pdf_url.encode()).hexdigest() + ".pdf"
        path = os.path.join(save_dir, fname)
        with open(path, "wb") as f:
            f.write(resp.content)
        print("Downloading PDF Success")
        return path


if __name__ == "__main__":
    d = VistaDesigner()
    d.load_all(
        "https://create.vista.com/templates/all-formats/coupons/",
        r"E:\00IT\P\uniform\multilang\templates\coupons\en",
    )
