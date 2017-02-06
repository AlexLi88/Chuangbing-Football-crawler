#Author: Alex Li
#Date: Jan 2017

import requests
import urllib
import urllib2 as url
from bs4 import BeautifulSoup
import os
import json
import sys
import zlib
import logging
from random import randint


request_headers = {
	'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
	'Accept-Encoding': 'gzip, deflate, sdc',
	'Accept-Language': 'en,zh-CN;q=0.8,zh;q=0.6,zh-TW;q=0.4',
	'Cache-Control': 'no-cache',
	'Connection': 'keep-alive',
	'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/54.0.2840.98 Safari/537.36'
}


def _urlRequest(request_url):
	request = url.Request(request_url, headers = request_headers)
	opener = url.build_opener()
	response = opener.open(request)
	html = response.read()
	gzipped = response.headers.get('Content-Encoding')
	if gzipped:
		html = zlib.decompress(html, 16+zlib.MAX_WBITS)

	return html



def _postRequest(session, url, data):
	body_value = urllib.urlencode(data)
	res = session.post(url, data = body_value)
	return res




class CBCrawler(object):
	def __init__(self, start_url):
		self.start_url = start_url
		self.url_prefix = "http://data.champdas.com"
		self.s = requests.Session()
		self.sheaders = {
						'Content-Type':'application/x-www-form-urlencoded; charset=UTF-8',
						'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/54.0.2840.98 Safari/537.36',
						}
		self.s.headers.update(self.sheaders)
		self.team_list = []

	def getTeamLink(self):
		all_teams_link = "http://data.champdas.com/team/rank-1-2016.html"
		html = _urlRequest(all_teams_link)
		soup = BeautifulSoup("".join(html), "lxml")
		table_wrapper = soup.find('div', id='run1-answer')
		table_body = table_wrapper.find('tbody')
		trs = table_body.find_all('tr')
		for tr in trs:
			try:
				team = {}
				team_td = tr.find('td', class_='nameAlign')
				a = team_td.find('a')
				#print a.get_text()
				team_link = a['href']
				#print team_link
				team['name'] = a.get_text()
				team['link'] = self.url_prefix + team_link
				self.team_list.append(team)
			except Exception as e:
				print "error", e

		#print self.team_list



	def getTeamPlayer(self):
		for team in self.team_list:
			print team['link']
			team_data = team['link'].split('-')
			league_id = 1
			season = 2016
			team_id = int(team_data[1])
			data = {'leagueId':league_id, 'teamId': team_id, 'season': season}
			res = _postRequest(self.s, 'http://data.champdas.com/team/getPersonDataForTeam/index.html', data)
			res_data = json.loads(res.text)


			#get all players in the team   
			print res_data[0]['index']






	def getRoundLink(self):
		html = _urlRequest(self.start_url)
		soup = BeautifulSoup("".join(html), "lxml")
		round1 = soup.find("div", class_="round1")
		lis = round1.find_all("li")
		self.round_list = []
		for li in lis:
			a = li.find('a')
			link = self.url_prefix + a['href'].encode('ascii', 'ignore')
			self.round_list.append(link)
		# print self.round_list

	def getGameLink(self, round_link):
		html = _urlRequest(round_link)
		soup = BeautifulSoup("".join(html), "lxml")
		against = soup.find('div', class_="against")
		lis = against.find_all('li')
		for li in lis:
			a = li.find('span').find('a')
			link = self.url_prefix + a['href'].encode('ascii', 'ignore')
			print link

if __name__ == '__main__':
	myCrawler = CBCrawler("http://data.champdas.com/match/scheduleDetail-1-2016-1.html")
	myCrawler.getTeamLink()
	myCrawler.getTeamPlayer()
