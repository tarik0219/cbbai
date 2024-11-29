"""
The utils module provides utility functions, such as logging in.
"""

import cloudscraper
import pandas as pd
import re
from io import StringIO
from cloudscraper import CloudScraper
from bs4 import BeautifulSoup
from typing import Optional

def login(email: str, password: str):
	"""
	Logs in to kenpom.com using user credentials.

	Args:
		email (str): User e-mail for login to kenpom.com.
		password (str): User password for login to kenpom.com.

	Returns:
		browser (mechanicalsoup StatefulBrowser): Authenticated browser with full access to kenpom.com.
	"""

	browser = cloudscraper.create_scraper()
	browser.get('https://kenpom.com/index.php')

	# form_data = {
	# 	'email': email,
	# 	'password': password,
	# 	'submit': 'Login!',
	# }

	# # Response page actually throws an error but further navigation works and will show you as logged in.
	# browser.post(
	# 	'https://kenpom.com/handlers/login_handler.php',
	# 	data=form_data, 
	# 	allow_redirects=True
	# )

	# home_page = browser.get('https://kenpom.com/')
	# if 'Logout' not in home_page.text:
	# 	raise Exception('Logging in failed - check your credentials')

	return browser

def get_efficiency(browser: CloudScraper, season: Optional[str]=None):
	"""
	Scrapes the Efficiency stats table (https://kenpom.com/summary.php) into a dataframe.

	Args:
		browser (CloudScraper): Authenticated browser with full access to kenpom.com generated
			by the `login` function.
		season (str, optional): Used to define different seasons. 1999 is the earliest available season but 
			possession length data wasn't available until 2010. Most recent season is the default.

	Returns:
		eff_df (pandas dataframe): Pandas dataframe containing the summary efficiency/tempo table from kenpom.com.

	Raises:
		ValueError: If `season` is less than 1999.
	"""

	url = 'https://kenpom.com'

	if season:
		if int(season) < 1999:
			raise ValueError(
				'season cannot be less than 1999, as data only goes back that far.')
		url = url + '?y=' + str(season)

	eff = BeautifulSoup(get_html(browser, url), "html.parser")
	table = eff.find_all('table')[0]
	eff_df = pd.read_html(StringIO(str(table)))

	# Dataframe tidying.
	eff_df = eff_df[0]

	# Handle seasons prior to 2010 having fewer columns.
	if len(eff_df.columns) == 18:
		eff_df = eff_df.iloc[:, 0:18]
		eff_df.columns = ['Team', 'Conference', 'Tempo-Adj', 'Tempo-Adj.Rank', 'Tempo-Raw', 'Tempo-Raw.Rank',
						  'Avg. Poss Length-Offense', 'Avg. Poss Length-Offense.Rank', 'Avg. Poss Length-Defense',
						  'Avg. Poss Length-Defense.Rank', 'Off. Efficiency-Adj', 'Off. Efficiency-Adj.Rank',
						  'Off. Efficiency-Raw', 'Off. Efficiency-Raw.Rank', 'Def. Efficiency-Adj',
						  'Def. Efficiency-Adj.Rank', 'Def. Efficiency-Raw', 'Def. Efficiency-Raw.Rank']
	else:
		eff_df = eff_df.iloc[:, 0:14]
		eff_df.columns = ['Team', 'Conference', 'Tempo-Adj', 'Tempo-Adj.Rank', 'Tempo-Raw', 'Tempo-Raw.Rank',
						  'Off. Efficiency-Adj', 'Off. Efficiency-Adj.Rank', 'Off. Efficiency-Raw',
						  'Off. Efficiency-Raw.Rank', 'Def. Efficiency-Adj', 'Def. Efficiency-Adj.Rank',
						  'Def. Efficiency-Raw', 'Def. Efficiency-Raw.Rank']

	# Remove the header rows that are interjected for readability.
	eff_df = eff_df[eff_df.Team != 'Team']
	# Remove NCAA tourny seeds for previous seasons.
	eff_df['Team'] = eff_df['Team'].str.replace(r'\d+', '', regex=True)
	eff_df['Team'] = eff_df['Team'].str.rstrip()
	eff_df = eff_df.dropna()

	return eff_df

def get_html(browser: CloudScraper, url: str):
	"""
	Performs a get request on the specified url.

	Args:
		browser (CloudScraper): Authenticated browser with full access to kenpom.com generated
            by the `login` function.
		url (str): The url to perform the get request on.
	
	Returns:
		html (Bytes | Any): The return content.
	
	Raises:
		Exception if get request gets a non-200 response code.
	"""	
	response = browser.get(url)
	if response.status_code != 200:
		raise Exception(f'Failed to retrieve {url} (status code: {response.status_code})')
	return response.content

browser = login('email', 'password')
eff_df = get_efficiency(browser)
print(eff_df.head())
#print rows 10 through 15
print(eff_df[8:12])
