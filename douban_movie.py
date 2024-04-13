#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
实验2：网络数据采集——网络爬虫
实验任务：爬取豆瓣电影TOP250，网址：https://movie.douban.com/top250
爬取字段：电影名称、电影链接、导演、主演、上映时间、国家、类型、评分、评价人数、短评
"""

import argparse
import csv
from time import sleep

import requests
from bs4 import BeautifulSoup
from tqdm import tqdm


def get_html(url):
    """
    获取网页源代码，返回html文本
    :param url: 网页链接
    :return: html文本
    """
    header = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
                      'AppleWebKit/537.36 (KHTML, like Gecko) '
                      'Chrome/58.0.3029.110 Safari/537.3'
    }
    try:
        response = requests.get(url, headers=header)
        response.raise_for_status()
        return response.text
    except requests.RequestException as e:
        print("请求失败：", e)
        return None

def parse_html(html, sleep_time, fast_mode):
    """
    生成器函数，解析html文本，提取电影信息，返回包含各字段的字典
    :param html: html文本
    :param sleep_time: 请求间隔时间，防止被封IP
    :param fast_mode: 快速爬取选项，直接使用榜单页的信息，而不进入电影链接
    :return: 包含各字段的字典
    """
    soup = BeautifulSoup(html, 'lxml')
    items = soup.select('.item')
    if not fast_mode:
        items = tqdm(items)

    for item in items:
        # 1. 第一行，电影名称和链接
        movie_name = item.select('.title')[0].get_text()
        movie_link = item.select('.hd a')[0].get('href')
        if not fast_mode:
            items.set_description(f'正在解析当前页中的《{movie_name}》')

        # 2. 第二行，导演和主演
        movie_info = item.select('.bd p')[0].get_text().strip().split('\n')
        if fast_mode:
            # 以下代码仅在榜单页直接获取导演和主演信息时使用
            line2 = movie_info[0].strip().split('\xa0\xa0\xa0')
            movie_director = line2[0][4:]
            if len(line2) == 1:
                movie_actor = ''
            else:
                movie_actor = line2[1][4:] if len(line2[1]) > 4 else ''
        else:
            # 使用上面代码时，由于导演和主演太长，可能抓不全，尝试进入电影链接再抓取
            sleep(sleep_time)
            detail = BeautifulSoup(get_html(movie_link), 'lxml').select('.attrs')
            movie_director = detail[0].get_text().strip().split('\n')[0]
            # movie_director = movie_director.replace('\xa0/\xa0', '，')
            # 有些电影没有主演，如《二十二》
            if len(detail) > 2:
                movie_actor = detail[2].get_text().strip().split('\n')[0]
                # movie_actor = movie_actor.replace('\xa0/\xa0', '，')
            else:
                movie_actor = ''

        # 3. 第三行，上映时间、国家和类型
        # 《大闹天宫》《高山下的花环》有多个年份，故按"/"分割后应取倒数第一、第二个作为类型和国家
        line3 = movie_info[1].strip().split('\xa0/\xa0')
        movie_year = '/'.join(line3[:-2])
        movie_country, movie_type = line3[-2], line3[-1]

        # 4. 评价和短评
        movie_rating = item.select('.rating_num')[0].get_text()
        movie_comment = item.select('.star span')[3].get_text()[:-3]
        movie_quote = item.select('.quote span')[0].get_text() if item.select('.quote span') else ''

        yield {
            '电影名称': movie_name,
            '电影链接': movie_link,
            '导演': movie_director,
            '主演': movie_actor,
            '上映时间': movie_year,
            '国家': movie_country,
            '类型': movie_type,
            '评分': movie_rating,
            '评价人数': movie_comment,
            '短评': movie_quote,
        }

def write_csv(data, fieldnames, csv_path):
    with open(csv_path, 'a', newline='', encoding='utf-8-sig') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writerow(data)

def crawler(csv_path, sleep_time, resume_page, fast_mode):
    """爬虫主体函数\n
    经试验，爬取8页时，豆瓣会封IP；假设能顺利爬取10页，则需87分钟左右。
    :param csv_path: 保存csv文件的路径，默认为当前目录下的douban_movie.csv
    :param sleep_time: 请求间隔时间，防止被封IP，默认15秒
    :param resume_page: “断点续传”功能，从指定页码开始爬取，并将结果追加到csv文件中而非覆盖
                        值等于1表示不使用该功能，值位于[2, 10]之间正常使用该功能
    :param fast_mode: 快速爬取选项，在爬取导演和主演时，直接使用榜单页的信息，而不进入电影链接
    """
    url = 'https://movie.douban.com/top250'
    fieldnames = ['电影名称', '电影链接', '导演', '主演', '上映时间',
                  '国家', '类型', '评分', '评价人数', '短评']

    if resume_page == 1:
        # 在第一行列出字段名(不使用断点续传功能时)
        print(f'开始爬取，结果将保存到{csv_path}')
        with open(csv_path, 'w', newline='', encoding='utf-8-sig') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
    else:
        print(f'从第{resume_page}页开始爬取，结果将追加到{csv_path}中')

    # 每页最多25条，共需爬取10页
    pbar = tqdm(range(resume_page - 1, 10))
    for i in pbar:
        page_url = f'{url}?start={i * 25}&filter='
        pbar.set_description(f'正在爬取第{i + 1}页({page_url})')
        html = get_html(page_url)
        for item in parse_html(html, sleep_time, fast_mode):
            write_csv(item, fieldnames, csv_path)
        sleep(sleep_time)
    print('爬取完成！')

def arg_parser():
    parser = argparse.ArgumentParser(
        description='Douban Movie Top250 Crawler')
    parser.add_argument('-p', '--path', default='douban_movie.csv',
                        type=str, help='Relative path to save the csv file')
    parser.add_argument('-s', '--sleep', default=15,
                        type=int, help='Sleep time between requests(unit: s)')
    # “断点续传”功能，从指定页码开始爬取，并将结果追加到csv文件中而非覆盖
    # 值等于1表示不使用该功能，值位于[2, 10]之间正常使用该功能
    parser.add_argument('-r', '--resume', default=1, choices=range(1, 11),
                        type=int, help='Resume from the specified page, '
                        'value=1: no resume; in [2, 10]: normal resume')
    # 快速爬取选项，在爬取导演和主演时，直接使用榜单页的信息，而不进入电影链接
    parser.add_argument('-f', '--fast', action='store_true',
                        help='Fast mode, get director and actor information '
                             'from the top-250 list page directly')
    parser.add_argument('-v', '--version', action='version',
                        version='%(prog)s 2.3')
    return parser.parse_args()


if __name__ == '__main__':
    args = arg_parser()
    crawler(args.path, args.sleep, args.resume, args.fast)