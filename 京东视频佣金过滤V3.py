
import os
import json
import time
import requests
from datetime import datetime, timedelta
import hashlib
import threading
from urllib.parse import quote
from playwright.sync_api import sync_playwright
from bs4 import BeautifulSoup



#要处理文件夹： input #
vPath="D:\京东采集融合视频"
# vPath= input("被检测视频所在文件夹:")
vBase=5 #佣金比率　起点5%, 或佣金5元　，　可设置　默认5

br_PORT="12345"

  
def get_skuName_by_skuid(skuid):
    url=f"https://item.jd.com/{skuid}.html"  # https://item.m.jd.com/product/{skuid}.html
    with sync_playwright() as playwright:      
        browser = playwright.chromium.connect_over_cdp(f'http://localhost:{br_PORT}/')   #新接管已手工打开的浏览器======   
        context = browser.contexts[0]     
        # context = browser.new_context(java_script_enabled=False)# 创新上下文禁用JavaScript
        page = context.new_page()   

        ##################        
        initial_html = None
        def handle_response(response):
            nonlocal initial_html
            # 检查响应 URL 是否为原始 URL
            if response.url == url:                
                initial_html = response.body()# 获取页面的 HTML 内容

        # 给 page 对象添加事件监听器
        page.on('response', handle_response)
        # 访问 URL       
        page.goto(url)        
        # 等待一段时间，确保 response 事件被触发
        page.wait_for_timeout(5000)  # 等待5秒，可以根据实际情况调整等待时间
        # 移除事件监听器
        page.remove_listener('response', handle_response)
        if initial_html:
            # 使用 BeautifulSoup 解析 HTML 内容
            soup = BeautifulSoup(initial_html, 'html.parser')
            title = soup.title.string if soup.title else '未找到标题'
            print("***初始页面标题0:", title)
        else:
            print("未能捕获到初始页面 HTML")
            
        ##################     
            page.goto(url) 
            page.wait_for_load_state('load')  # 等待页面完全加载完成
            page.wait_for_timeout(1000)# time.sleep(3) 再多等1秒时间

            title = page.title() # 获取页面标题
            print(f"标题1： {title}")

        #检测title是否为 "京东验证" 如果是京东验证 循环暂停1秒
        while "京东验证"  in title or title=="":
            print("检测到京东验证页面，暂停20秒...")
            time.sleep(20)  # 暂停1秒
            page.reload()  # 重新加载页面，尝试绕过验证
            title = page.title()  # 重新获取页面标题

        if "京东(JD.COM)-正品低价" in title  or title=="":
            page.close()
            print("PC频繁转向  重新禁用JS访问...")
            # https://cfe.m.jd.com/privatedomain/risk_handler/03101900/?returnurl=https%3A%2F%2Fitem.jd.com%2F10099650217866.html&evtype=2&rpid=rp-191308537-10190-1734679780581
            context = browser.new_context(java_script_enabled=False)# 创新上下文禁用JavaScript
            page = context.new_page() 
            page.goto(url)
            page.wait_for_timeout(2000)
            title = page.title()
            print(f"标题2： {title}") 
            if "京东(JD.COM)-正品低价" in title or   title=="": 
                page.close()
                print("禁用JS频繁重新取m手机版... 需要先登录m.jd.com")
                mUrl=f"https://item.m.jd.com/product/{skuid}.html" 
                context = browser.new_context(java_script_enabled=False)# 创新上下文禁用JavaScript
                page = context.new_page() 
                page.goto(mUrl)
                page.wait_for_timeout(2000)
                title = page.title()
                print(f"标题3： {title}")

        

        # print(f"页面标题: {title}")
        parts = title.rsplit('【', 1)
        # 取第一部分，即最后一个【之前的部分
        # clean_title = parts[0] 
        clean_title = parts[0]   

        parts = clean_title.split('】', 1)
        if len(parts)>1:              
            if len(parts[1].strip())>25:
                clean_title = parts[1] 


        clean_title=clean_title.replace("&"," ").replace("/"," ").replace("+"," ").replace("#"," ").replace("%"," ")  
        page.close()   # 关闭浏览器
        print(f"===处理后的商品名:{clean_title}")
        # print(clean_title)
        return clean_title


def getListGoodsQuery(keyword):    

    dataListArr=[]
    timestamp = (datetime.now() - timedelta(minutes=1)).strftime('%Y-%m-%d %H:%M:%S')
    timestampC = timestamp + ".043+0800"
    timestampCURL = timestampC.replace(":", "%3A").replace("+", "%2B").replace(" ", "+")   



    app_key = "85c77421c5fec5717bb1998bc03a920e"    
    app_secret = "4ad6269154624f6f93a7d2938226abf9"
    access_token = ""
    methodC = "jd.union.open.goods.query"
    v = "1.0"    
    arrSKU = {"goodsReqDTO":{"sceneId":1,"keyword":f"{keyword}"}} #360buy_param_json={"goodsReqDTO":{"sceneId":1,"keyword":"文竹盆栽植物"}}
    param_json = json.dumps(arrSKU)   
    # signStrV1 = "360buy_param_json" + param_json + "access_token" + access_token + "app_key" + app_key + "method" + methodC + "timestamp" + timestampC + "v" + v
    signStrV1 = "360buy_param_json" + param_json +  "app_key" + app_key + "method" + methodC + "timestamp" + timestampC + "v" + v
    signStr = app_secret + signStrV1 + app_secret
    m = hashlib.md5(signStr.encode()).hexdigest().upper()
    sign = m
    webapiUrl = 'https://api.jd.com/routerjson?app_key=' + app_key + '&method=' + methodC + '&v=1.0&sign=' + sign + '&360buy_param_json=' + param_json + '&timestamp=' + timestampCURL
   
    # webapiUrl = 'https://api.jd.com/routerjson?access_token=&app_key=' + app_key + '&method=' + methodC + '&v=1.0&sign=' + sign + '&360buy_param_json=' + param_json + '&timestamp=' + timestampCURL
   #  webapiUrl = 'https://api.jd.com/routerjson?360buy_param_json='+param_json +'&access_token=&app_key='+app_key +'&method='+methodC+'&sign='+sign+ '&timestamp='+ timestampCURL+ '&v='+v  
    #https://api.jd.com/routerjson?access_token=&app_key=app_key&method=methodC&v=1.0&sign=sign&360buy_param_json=%7B%22goodsReqDTO%22%3A%7B%22sceneId%22%3A1%2C%22keyword%22%3A%22AABBCC%22%7D%7D&timestamp=2024-12-04+20%3A14%3A10.030%2B0800
    webapi_json_str = requests.get(webapiUrl).json()
    # print(webapi_json_str)  
    webapi_data = webapi_json_str
    try:
        webapi_responce = webapi_data['jd_union_open_goods_query_responce']
        resultJStr = webapi_responce['queryResult']
        resultJStr_data = json.loads(resultJStr)
        # 检查是否存在"data"键,且不为空值，如果正常，取data值数据，并按佣金降序排列
        if 'data' in resultJStr_data and len(resultJStr_data['data']) > 0:
            dataListArr = resultJStr_data['data'] 
    except: 
        # print(keyword) 
        # print(webapiUrl)
        print(f"API结果异常jd_union_open_goods_query_responce：{webapi_json_str}")    
    return dataListArr   
    
# 参数准备
# skuid = "10042039661521,10042390332504"  
def getCommValues(skuid):
    commissionShare=0.123
    commission=0.123
    proName=get_skuName_by_skuid(skuid)
    if proName:
        dataListArr=getListGoodsQuery(proName)
        if len(dataListArr)==0:
            print("自然搜索第一次无结果，下面补搜一次 取半关键词")
            half_length = len(proName) // 2 # 计算字符串长度的一半
            half_kw = proName[:half_length + 1]  # 注意这里加1以包含中间的字符
            dataListArr=getListGoodsQuery(half_kw)
            
        if len(dataListArr) > 0:
            item=dataListArr[0]
            # print(item)
            commissionShare=item['commissionInfo']['commissionShare']
            commission = item['commissionInfo']['commission']
        else:
            print("2次搜索产品名都无结果，跳过")    

    else:
        print("取产品名出错NONE")        
    return commissionShare, commission 

#遍历AAA文件夹下所有子文件夹 选择符合条件的视频　转到 -待上传新目录
def runChoose(vPath,vBase):
    vPathOK=  vPath+"-待上传-"+str(vBase)
    #检查是否存在vPathOK文件夹
    if not os.path.exists(vPathOK):
        #不存在则创建vPathOK文件夹
        os.mkdir(vPathOK)
    vPathChecked= vPath+"/已检测"  
    if not os.path.exists(vPathChecked):
        #不存在则创建vPathOK文件夹
        os.mkdir(vPathChecked) 

    i=0
    for file_name in os.listdir(vPath):
        if file_name.endswith(".mp4"):   
        #如果文件夹下有mp4文件,则将文件夹名和mp4文件名拼接保存        
            mp4_name = file_name
            # jpg_name = file_name.replace('.mp4','.jpg') #　string.replace(old, new) 
            skuID=mp4_name.split(' ')[0] 

            # dir=dir.strip()
            commRate,makeMoney=getCommValues(skuID) # dir就是SKUID集合 有多个的是","分隔的
            print(skuID,commRate,makeMoney)
            if commRate==0.123:                
                print("可能频繁,暂停15秒...")
                time.sleep(15)
                continue

            #如果佣金条件成立 ，搬运 ， 否则 跳过 下一个
            if commRate>=vBase or makeMoney>=vBase:                
                if not os.path.exists(os.path.join(vPathOK, mp4_name)):                             
                    os.rename(f"{vPath}/{mp4_name}", os.path.join(vPathOK, mp4_name))  
                    # os.rename(f"{vPath}/{jpg_name}", os.path.join(vPathOK, jpg_name)) 
                    i=i+1
                    print(f"符合条件:第{i}个：{mp4_name,commRate,makeMoney}")
                else:
                    print(f"重复跳过:{mp4_name}")    #output_elem.Update(f' 符合条件: {mp4_name} ')  
            else:
                target_path = os.path.join(vPathChecked, mp4_name)
                if os.path.exists(target_path):
                    os.remove(target_path)  # 删除已存在的文件
                os.rename(f"{vPath}/{mp4_name}", target_path)  

    print(f"***处理完成:　{vPath}")

#取txt行，返回行列表 广告语句，从广告配置文件 中， 一行一个， 随机一个
def read_txt_file(txt_file):
    lines = []
    try:
        with open(txt_file, 'r', encoding='utf-8') as file:
            lines = [line.strip() for line in file.readlines()]
    except FileNotFoundError:
        print(f"File '{txt_file}' not found.")
    except Exception as e:
        print(f"An error occurred: {e}")    
    return lines

def buildComboBrPort():
    portList=[]
    portList=read_txt_file("browser_port.ini") #固定写入程序
    return portList

# GUI界面 
import PySimpleGUI as sg
sg.theme('DarkBlue12')
layout = [            
           [sg.Output( size=(66, 12),font=("微软雅黑", 10), key='output')], 
           [sg.Input(f'{vPath}',key='videoDir', size=(47, 1)), sg.FolderBrowse('选择源视频目录')],       

           [sg.Text('端口:',font=("微软雅黑", 10)),sg.Combo(buildComboBrPort(), size=(6,1),key="br_PORT",default_value=br_PORT,enable_events=True,),
            sg.Text('佣比起点：',font=("微软雅黑", 10)),
            sg.InputText(key='vCommBase',size=(4,1),font=("微软雅黑", 10),default_text=f'{vBase}'),

            sg.Button('开始过滤',font=("微软雅黑", 10),button_color ='Blue'), 
            sg.Button('打开目录',font=("微软雅黑", 10),button_color ='Green'),
            sg.Button('关闭程序',font=("微软雅黑", 10),button_color ='red'),
             ],
          ]      

# 创建窗口
window = sg.Window('JD视频过滤-V2，作者@微信：liumingdada', layout,font=("微软雅黑", 12),default_element_size=(50,1), icon='iconJDpro.ico')    

# 事件循环
while True:
    # 主界面WINDOWS 
    event, values = window.read()  

    if event in (None, '关闭程序'):
        break   
    
    if event =='br_PORT':
        br_PORT=values['br_PORT']
        window.TKroot.title(f'{br_PORT}-京东视频佣金过滤')
        print(f'浏览器 chrome.exe 远程调试的端口已选：{br_PORT}') 
     
    if event == '开始过滤':   
        vPath=values['videoDir']
        vBase= int(values['vCommBase']) # int('10')
        thread = threading.Thread(target=runChoose, args=(vPath, vBase))
        thread.start() 

    if event == '打开目录':   
        vPath=values['videoDir']
        os.startfile(vPath)    

window.close()  

# pyinstaller -F -w -i iconJDpro.ico 京东视频佣金过滤V3.py  