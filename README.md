# news_crawler
You can run this project following environments.
- python3.x
- install bs4 (BeautifulSoup4)
- make folder 'articles' on root of project

It will crawl news published on between 2017, 5, 1 and 2017, 6, 30.
You can modify source code get news published other dates as follow
line 178 : begin_date = datetime.date(2016, 5, 1)
line 179 : end_date = datetime.date(2016, 5, 15)