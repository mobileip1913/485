from flask import Flask, render_template, request
import requests
import schedule
import time
import logging

app = Flask(__name__)

# 请求的URL和头部信息等，根据你的实际情况修改
url = "http://ggzy.hebei.gov.cn/inteligentsearchnew/rest/esinteligentsearch/getFullTextDataNew"
headers = {
    "accept": "application/json, text/javascript, */*; q=0.01",
    "accept-encoding": "gzip, deflate",
    "accept-language": "zh-CN,zh;q=0.9",
    "connection": "keep-alive",
    "content-type": "application/x-www-form-urlencoded; charset=UTF-8",
    "cookie": "_gscu_1921552764=27570106h3c0tf19; _gscbrs_1921552764=1; oauthClientId=demoClient; oauthPath=http://172.19.3.1; oauthLoginUrl=http://172.19.3.1/rest/oauth2/authorize?client_id=demoClient&state=a&response_type=code&scope=user&redirect_uri=; oauthLogoutUrl=http://172.19.3.1/rest/oauth2/logout?redirect_uri=; noOauthRefreshToken=04808045291937ae73a9a77871774306; noOauthAccessToken=102b007163a04d30a7f324708a3d5f7e; _gscs_1921552764=31380446c7wccd15|pv:4",
    "host": "ggzy.hebei.gov.cn",
    "origin": "http://ggzy.hebei.gov.cn",
    "referer": "http://ggzy.hebei.gov.cn/hbggfwpt/search/fullsearch.html?wd=%E6%B2%B3%E5%8C%97%E7%9C%81%E4%BD%93%E8%82%B2%E5%B1%80%E7%A7%A6%E7%9A%84%E5%B2%9B%E8%AE%AD%E7%BB%83%E5%9F%BA%E5%9C%B0%E9%A1%B9%E7%9B%AE",
    "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36",
    "x-requested-with": "XMLHttpRequest"
}
payload = {
    "token": "",
    "pn": 0,
    "rn": 10,
    "sdt": "2024-11-11 11:24:57",
    "edt": "2024-11-12 11:24:57",
    "wd": "",
    "inc_wd": "",
    "exc_wd": "",
    "fields": "title;content",
    "cnum": "001;008;005;",
    "sort": "{\"webdate\":0}",
    "ssort": "title",
    "cl": 500,
    "terminal": "",
    "condition": "[{\"equal\":\"河北省体育局秦皇岛训练基地项目\",\"isLike\":true,\"fieldName\":\"title\",\"likeType\":0}]",
    "time": None,
    "highlights": "title;content",
    "statistics": None,
    "unionCondition": None,
    "accuracy": "",
    "noParticiple": "0",
    "searchRange": None,
    "isBusiness": "1"
}

# 配置日志记录
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


def check_project_status():
    try:
        response = requests.post(url, headers=headers, data=payload)
        response.raise_for_status()  # 检查请求是否成功（状态码为200）
        data = response.json()
        if data["result"]["totalcount"]!= 0:
            logging.info("关注项目已发标！")
            print("关注项目已发标！")
        else:
            logging.info("未发标")
            print("未发标")
    except requests.exceptions.RequestException as e:
        logging.error(f"请求出错: {e}")
    except requests.exceptions.JSONDecodeError as e:
        logging.error(f"JSON解码错误: {e}")


@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        check_project_status()
    return render_template('index.html')


if __name__ == '__main__':
    # 每天早上8:30执行检查任务
    schedule.every().day.at("08:30").do(check_project_status)

    app.run(debug=True)

    while True:
        schedule.run_pending()
        time.sleep(1)