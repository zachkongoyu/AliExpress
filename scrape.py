import requests
from bs4 import BeautifulSoup
from datetime import datetime
import pandas as pd
import datetime
import os

def crawling(id_, page, lastupdate=None):

	headers = {
	'authority': 'feedback.aliexpress.com',
	'cache-control': 'max-age=0',
	'upgrade-insecure-requests': '1',
	'origin': 'https://feedback.aliexpress.com',
	'content-type': 'application/x-www-form-urlencoded',
	'user-agent': 'Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.107 Safari/537.36',
	'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
	'sec-gpc': '1',
	'sec-fetch-site': 'same-origin',
	'sec-fetch-mode': 'navigate',
	'sec-fetch-user': '?1',
	'sec-fetch-dest': 'document',
	'referer': 'https://feedback.aliexpress.com/display/productEvaluation.htm',
	'accept-language': 'zh-CN,zh;q=0.9',
	}

	data = {
	'ownerMemberId': '235231370',
	'memberType': 'seller',
	'productId': str(id_),
	'companyId': '',
	'evaStarFilterValue': 'all Stars',
	'evaSortValue': 'sortlarest@feedback',
	'page': str(page),
	'currentPage': str(page),
	'startValidDate': '',
	'i18n': 'true',
	'withPictures': 'false',
	'withAdditionalFeedback': 'false',
	'onlyFromMyCountry': 'false',
	'version': '',
	'isOpened': 'true',
	'translate': ' Y ',
	'jumpToTop': 'true',
	'v': '2'
	}

	response = requests.post('https://feedback.aliexpress.com/display/productEvaluation.htm', headers=headers, data=data)
	soup = BeautifulSoup(response.content, 'html.parser')

	if lastupdate != None:
		dates = [datetime.datetime.strptime(temp.text, '%d %b %Y %H:%M').replace(hour=0, minute=0) for temp in soup.find_all('span', class_='r-time-new') if datetime.datetime.strptime(temp.text, '%d %b %Y %H:%M') >= lastupdate]
	
	else:
		dates = [datetime.datetime.strptime(temp.text, '%d %b %Y %H:%M').replace(hour=0, minute=0) for temp in soup.find_all('span', class_='r-time-new')]

	countries = [temp.text for temp in soup.find_all('div', class_='user-country')][:len(dates)]

	return dates, countries


def save_file(company, name, id_, df, now):

	idx = pd.date_range(df.index[0], df.index[-1])
	df = df.reindex(idx)
	df.index = df.index.strftime('%Y-%m-%d')

	review_nums = df['sum'].sum(skipna=True).sum()
	print(f'--- {name} --- {review_nums} reviews')
	print()

	df.replace(0, float('NaN'), inplace=True)

	try:
		df.to_csv(f'{company}/{name}_{id_}.csv')
	except:
		os.mkdir(company)
		df.to_csv(f'{company}/{name}_{id_}.csv')

def update():

	with open('Aliexpress_Names.txt') as f:
		names_ids = f.read().splitlines()

	names_ids = [pair for pair in names_ids if pair != "\ufeff" and pair != '']

	with open('lastupdate.txt') as f:
		lastupdate = f.read().strip()

	lastupdate = datetime.datetime.strptime(lastupdate, '%Y-%m-%d %H:%M')

	companies = set()
	now = datetime.datetime.now()

	with open('lastupdate.txt', 'w+') as f:
		f.write(now.strftime("%Y-%m-%d %H:%M"))
		f.write('\n')

	for name_id in names_ids:

		name_id = name_id.split(', ')
		page = 1
		name = name_id[0]
		id_ = name_id[1]
		company = name_id[2]
		companies.add(company)
		country_time = dict()
		print(name, id_, company)

		try:
			df = pd.read_csv(f'{company}/{name}_{id_}.csv', index_col = 0)
		except:
			df = pd.DataFrame()

		while True:

			print('Page', page)

			if os.path.isfile(f'{company}/{name}_{id_}.csv') == True:
				dates, countries = crawling(id_, page, lastupdate)
			else:
				dates, countries = crawling(id_, page)

			for i, country in enumerate(countries):

				if country not in country_time:
					country_time[country] = {dates[i] : 1}
				else:
					if dates[i] in country_time[country]:
						country_time[country][dates[i]] += 1
					else:
						country_time[country][dates[i]] = 1


			if len(dates) < 10:
				break
			else:
				page += 1

		temp_df = pd.DataFrame(country_time)
		temp_df['sum'] = temp_df.sum(axis=1)
		temp_df.sort_index(inplace=True)
		df = pd.concat([df, temp_df], axis=0) 
		df = df.groupby(df.index, axis=0).sum()

		save_file(company, name, id_, df, now)

if __name__ == '__main__':

	update()