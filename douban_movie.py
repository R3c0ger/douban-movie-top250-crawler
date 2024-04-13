#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
实验2：网络数据采集——网络爬虫
实验任务：爬取豆瓣电影TOP250，网址：https://movie.douban.com/top250
爬取字段：电影名称、电影链接、导演、演员、上映时间、国家、类型、评分、评价人数、短评
"""

import argparse
import csv
import sys
from time import sleep

import requests
from bs4 import BeautifulSoup
from tqdm import tqdm


def get_html(url):
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
                      'AppleWebKit/537.36 (KHTML, like Gecko) '
                      'Chrome/58.0.3029.110 Safari/537.3'
    }
    response = requests.get(url, headers=headers)
    if response.status_code != 200:
        raise Exception('Failed to get html!')
    return response.text

def parse_html(html):
    soup = BeautifulSoup(html, 'lxml')
    for item in soup.select('.item'):
        movie_name = item.select('.title')[0].get_text()
        movie_link = item.select('.hd a')[0].get('href')
        movie_info = item.select('.bd p')[0].get_text().strip().split('\n')

        movie_director_and_actor = movie_info[0].strip().split('\xa0\xa0\xa0')
        if len(movie_director_and_actor) == 1:
            movie_director = movie_director_and_actor[0]
            movie_actor = ''
        else:
            movie_director = movie_info[0].strip().split('\xa0\xa0\xa0')[0]
            movie_actor = movie_info[0].strip().split('\xa0\xa0\xa0')[1]
        sleep(5)
        movie_info = BeautifulSoup(get_html(movie_link), 'lxml').select('.attrs')
        print(movie_info[0].get_text(),"\n",movie_info[1].get_text())

        # # 导演和演员太长，可能抓不到，进入电影链接，然后再抓取
        # movie_director = ''
        # movie_actor = ''
        # for i in range(2):
        #     movie_info = BeautifulSoup(get_html(movie_link), 'lxml').select('.attrs')[i].get_text().strip().split('\n')
        #     if i == 0:
        #         movie_director = movie_info[0].strip().split('\xa0\xa0\xa0')[0]
        #         movie_actor = movie_info[0].strip().split('\xa0\xa0\xa0')[1]

        movie_other = movie_info[1].strip().split('\xa0/\xa0')
        movie_year = movie_other[0]
        movie_country = movie_other[1]
        movie_type = movie_other[2]

        movie_rating = item.select('.rating_num')[0].get_text()
        movie_comment = item.select('.star span')[3].get_text()[:-3]
        movie_quote = item.select('.quote span')[0].get_text() if item.select('.quote span') else ''

        yield {
            '电影名称': movie_name,
            '电影链接': movie_link,
            '导演': movie_director,
            '演员': movie_actor,
            '上映时间': movie_year,
            '国家': movie_country,
            '类型': movie_type,
            '评分': movie_rating,
            '评价人数': movie_comment,
            '短评': movie_quote
        }

def write_csv(data, fieldnames, csv_path):
    with open(csv_path, 'a', newline='', encoding='utf-8-sig') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writerow(data)

def main(csv_path='douban_movie.csv', sleep_time=5):
    url = 'https://movie.douban.com/top250'
    fieldnames = ['电影名称', '电影链接', '导演', '演员', '上映时间',
                  '国家', '类型', '评分', '评价人数', '短评']

    # 每次运行覆盖已有的csv文件，并在第一行列出字段名
    with open(csv_path, 'w', newline='', encoding='utf-8-sig') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()

    # 共需爬取10页
    pbar = tqdm(range(10))
    for i in pbar:
        page_url = f'{url}?start={i * 25}&filter='
        pbar.set_description(f'正在爬取第{i + 1}页({page_url})')
        html = get_html(page_url)
        for item in parse_html(html):
            write_csv(item, fieldnames, csv_path)
        sleep(sleep_time)
    print('爬取完成！')


if __name__ == '__main__':
    if len(sys.argv) > 1:
        parser = argparse.ArgumentParser(
            description='Douban Movie Top250 Crawler')
        parser.add_argument('-p', '--path', default='douban_movie.csv',
                            type=str, help='Path to save the csv file')
        parser.add_argument('-s', '--sleep', default=5,
                            type=int, help='Sleep time between requests')
        args = parser.parse_args()
        main(args.path, args.sleep)
    else:
        main()