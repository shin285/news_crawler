# Daily crawler on naver news

import random
import logging

import datetime
import time
import requests
import codecs
import os.path
from bs4 import BeautifulSoup, NavigableString

root_logger = logging.getLogger()
root_logger.setLevel(logging.INFO)  # or whatever
handler = logging.FileHandler('naver_crawler.log', 'w', 'utf-8')  # or whatever
formatter = logging.Formatter('%(levelname)s : %(asctime)s %(message)s')  # or whatever
handler.setFormatter(formatter)  # Pass handler as a parameter, not assign
root_logger.addHandler(handler)


# logging.basicConfig(filename='naver_crawler.log', format='%(levelname)s : %(asctime)s %(message)s', level=logging.DEBUG)


def request_url(url):
    min_time = 5
    max_time = 10
    root_logger.debug("request url %s", url)
    while True:
        try:
            contents = requests.get(url)
            return contents
        except:
            sleep_time = random.randrange(min_time, max_time)
            print(str(datetime.datetime.now()) + ":" + "Sleep in {}".format(sleep_time))
            time.sleep(sleep_time)
            min_time += 5
            max_time += 5


def get_sub_category_urls_from_seed(_filename):
    main_url = "http://news.naver.com"
    url = "{}/main/main.nhn?mode=LSD&mid=shm&sid1={}"

    _category_name_url_dic = {}

    f = codecs.open(_filename, 'r', encoding='utf-8')
    lines = f.readlines()

    for line in lines:
        name, id = line.split()
        _category_main_html = BeautifulSoup(request_url(url.format(main_url, id)).text, 'lxml')
        _sub_category_area = _category_main_html.find("ul", attrs={"class": "nav"}).find_all("a")

        for a in _sub_category_area:
            sub_category_link = a.get("href")
            sub_category_name = a.text.strip().replace(" ", "_").strip()
            _category_name_url_dic[name + "-" + sub_category_name] = main_url + sub_category_link
    f.close()

    return _category_name_url_dic


def save_dic_to_file(dic, _filename):
    f = codecs.open(_filename, 'w', encoding='utf-8')
    for key, value in dic.items():
        f.write(key.strip() + "\t" + value.strip() + "\n")
    f.close()


def load_dic_from_file(_filename):
    _dic = {}
    f = codecs.open(_filename, 'r', encoding='utf-8')
    for line in f:
        key, value = line.split('\t')
        _dic[key.strip()] = value.strip()
    f.close()
    return _dic


def has_file(_filename):
    if os.path.exists(_filename):
        return True
    else:
        return False


def insert_news_link(news_link_list, _news_list_area):
    if _news_list_area is None:
        return None, None
    news_lists = _news_list_area.find_all('a')
    for a in news_lists:
        news_link_list.add(a.get('href'))


def get_article_links(_news_list_url, _cur_page, _cur_date):
    request_url_formatted = _news_list_url.format(_cur_page, _cur_date)
    _news_list_html = BeautifulSoup(request_url(request_url_formatted).text, 'lxml')
    _news_list_area = _news_list_html.find("ul", attrs={'class': 'type06'})
    _headline_news_list_area = _news_list_html.find("ul", attrs={'class': 'type06_headline'})
    news_link_list = set()
    insert_news_link(news_link_list, _news_list_area)
    insert_news_link(news_link_list, _headline_news_list_area)
    if len(news_link_list) == 0:
        return None, None

    page_numbers = _news_list_html.find("div", attrs={'class': 'paging'})
    has_next_page = False

    for page_number in page_numbers:
        if isinstance(page_number, NavigableString):
            continue
        page_number_text = page_number.text
        if len(page_number_text) == 0:
            continue
        elif page_number_text == '다음':
            has_next_page = True
            break
        elif page_number_text == '이전':
            continue
        elif _cur_page < int(page_number_text):
            has_next_page = True
            break
    return news_link_list, has_next_page


def get_title_and_body(article_link):
    _article_html = BeautifulSoup(request_url(article_link).text, 'lxml')
    for script in _article_html(["script", "style"]):
        script.decompose()
    try:
        article_title = _article_html.find("h3", attrs={'id': 'articleTitle'}).text
        article_body = _article_html.find("div", attrs={'id': 'articleBodyContents'}).text
    except AttributeError:
        return None, None
    return " ".join(article_title.split()), " ".join(article_body.split())


def naver_news_crawler(_category_name, _category_url, _cur_date):
    _news_list_url = _category_url + '&page={}&date={}'
    _cur_page = 1
    f = codecs.open('articles/articles_' + _category_name + '.txt', 'a', encoding='utf-8')
    _has_next_page = True
    doc_id = 1
    while _has_next_page:
        _news_article_links, _has_next_page = get_article_links(_news_list_url, _cur_page, _cur_date)
        if _news_article_links is None:
            _cur_page += 1
            continue
        for article_link in _news_article_links:
            title, body = get_title_and_body(article_link)
            if title is None:
                continue
            doc = "<id>\n" + str(doc_id) + "\n</id>\n<date>\n" + str(
                _cur_date) + "\n</date>\n<category>\n" + _category_name + "\n</category>\n<title>\n" + title + "\n</title>\n<body>\n" + body + "\n</body>\n\n"
            f.write(doc)
            doc_id += 1
            root_logger.info(
                _category_name + " : [date:" + str(_cur_date) + "][page:" + str(_cur_page) + "]," + article_link)
            print(str(datetime.datetime.now()) + ":" + str(cur_date) + "\t" + _category_name + " : " + str(
                _cur_page) + "," + title)
        _cur_page += 1
    f.close()


# build seed url from mapper file of category name and id
subcategory_filename = 'subcategory.txt'

if not has_file(subcategory_filename):
    root_logger.info("Load seed url from crawler")
    category_name_url_dic = get_sub_category_urls_from_seed('naver_sid1_category.map')
    save_dic_to_file(category_name_url_dic, subcategory_filename)
    root_logger.info("Save seed url to \'%s\'", subcategory_filename)
root_logger.info("Load seed url from file \'%s\'", subcategory_filename)

# key = category_name, value = url
seed_url_dic = load_dic_from_file(subcategory_filename)

begin_date = datetime.date(2017, 5, 1)
end_date = datetime.date(2017, 6, 30)
days = (end_date-begin_date).days + 1
target_date = [(begin_date + datetime.timedelta(days=i)).strftime("%Y%m%d") for i in range(0, days)]

# for cur_date in range(20170701, 20170709):
for cur_date in target_date:
    for category_name, category_url in seed_url_dic.items():
        category_name = category_name.strip().replace('/', '_')
        naver_news_crawler(category_name, category_url, cur_date)
