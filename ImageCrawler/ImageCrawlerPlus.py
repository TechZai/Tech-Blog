import os
import time
import requests
import json
from multiprocessing import Pool


def crawl(name, need_pic_count, resume_fetch):

    # create store folder
    pic_store_folder = './Data/%s/' % name
    if not os.path.isdir(pic_store_folder):
        os.makedirs(pic_store_folder)

    url = 'http://pic.sogou.com/pics'
    next_pic_index = 0
    pic_max_end = need_pic_count
    success_pic_count = 0
    if resume_fetch:
        success_pic_count = len(os.listdir(pic_store_folder))
    while success_pic_count < min(pic_max_end, need_pic_count):
        # 抓取网页内容
        paramters = {
            'query': name,
            'mode': 1,
            'start': next_pic_index,
            'reqType': 'ajax',
            'reqFrom': 'result',
            'tn': 0}

        try:
            r = requests.get(url, paramters)
        except:
            print('search url[%s] failed!' % url)
            break

        try:
            parsed_json = json.loads(r.text)
        except:
            print('request [%s] images failed!' % name)
            next_pic_index += 20
            continue

        pic_items = parsed_json['items']    # 当次请求的图片
        pic_max_end = int(parsed_json['totalItems'].replace(',', ''))   # 搜索引擎中的所有图片

        for pic_item in pic_items:
            pic_url = pic_item['pic_url']

            next_pic_index += 1

            if len(pic_url) == 0:
                continue

            # get pic
            try:
                pic = requests.get(pic_url, timeout=(3.05, 60))
            except:
                print('Get pic url [%s] failed!' % pic_url)
                continue
            else:
                print('Get pic url [%s] success!' % pic_url)

            if len(pic.content) >= 4 and \
                    pic.content[0] == 0xFF and \
                    pic.content[1] == 0xD8 and \
                    pic.content[-2] == 0xFF and \
                    pic.content[-1] == 0xD9:
                print('Verify pic [%s], is picture!' % pic_url)
            else:
                print('Verify pic [%s], not picture!' % pic_url)
                continue

            # save pic
            pic_filename = ''
            try:
                pic_filename = "%s%d.jpg" % (pic_store_folder, success_pic_count)
                with open(pic_filename, "wb") as f:
                    f.write(pic.content)
            except:
                print('Save file [%s] failed' % pic_filename)
            else:
                print('Save file [%s] success' % pic_filename)
                success_pic_count += 1

            if success_pic_count >= need_pic_count:
                break


if __name__ == '__main__':

    pic_count = 200
    with open("config.json") as f:
        config = json.load(f)
        pic_count = config["countPerItem"]
        process_count = config["processCount"]
        resume_fetch = config["resumeFetch"]
    mode = input(u'图像抓取程序，'
                 u'\n抓取结果存放在exe相同目录Data文件夹下, 每条抓取%d张'
                 u'\n抓取模式'
                 u'\n【1.手动输入名称（人名，物体，建筑等）】'
                 u'\n【2.输入名称列表文件名】'
                 u'\n 请选择：' % pic_count)

    if mode == '1':
        while True:
            query_name = input(u'请输入名称[直接输入回车退出]：')
            if len(query_name) == 0:
                break
            crawl(query_name, pic_count)
    elif mode == '2':
        while True:
            name_list_file = input(u'请输入名称列表文件[直接输入回车退出]：')
            if len(name_list_file) == 0:
                break

            start = time.time()
            f = open(name_list_file)
            p = Pool(process_count)
            for line in f:
                query_name = line.replace('\n', '')
                print(query_name)

                if len(query_name):
                    p.apply_async(crawl, (query_name, pic_count, resume_fetch))
                    # crawl(query_name, pic_count)

            p.close()
            p.join()
            print(time.time() - start)
    print(u'程序退出')