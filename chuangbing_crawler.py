#Author: Alex Li
#Date: Jan 2017

import requests
import urllib
import urllib2 as url
from bs4 import BeautifulSoup
from pymongo import MongoClient
import os
import json
import sys
import zlib
import logging
from random import randint


#Connect to local Mongo Database
client = MongoClient()
db = client.chuangbing


request_headers = {
	'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
	'Accept-Encoding': 'gzip, deflate, sdc',
	'Accept-Language': 'en,zh-CN;q=0.8,zh;q=0.6,zh-TW;q=0.4',
	'Cache-Control': 'no-cache',
	'Connection': 'keep-alive',
	'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/54.0.2840.98 Safari/537.36'
}

stat = {'shoot': '0',
		'shoot_in_target': '90',
		'shoot_off_target': '500',
		'assist': '78',
		'key_pass': '504',
		'center_ball': '9',
		'break_through': '86',
		'free_kick': '10',
		'interception': '26',
		'contain': '28',
		'block': '32',
		'goal_keeper_save': '502',
		'block_pass': '204',
		'block_shoot': '205',
		'foul': '21',
		'cards': ['24', '25', '117']
		}

def _getAllStats(tp):
	if tp == 'offense':
		return [stat['shoot'], stat['shoot_in_target'], stat['shoot_off_target'], stat['assist'], stat['key_pass'], stat['center_ball'], stat['break_through'], stat['free_kick']]
	elif tp == 'defense':
		return [stat['interception'], stat['contain'], stat['block'], stat['goal_keeper_save'], stat['block_pass'], stat['block_shoot'], stat['foul']]+ stat['cards']
	else:
		return [stat['shoot'], stat['shoot_in_target'], stat['shoot_off_target'], stat['assist'], stat['key_pass'], stat['center_ball'], stat['break_through'], stat['free_kick'], stat['interception'], stat['contain'], stat['block'], stat['goal_keeper_save'], stat['block_pass'], stat['block_shoot'], stat['foul']] + stat['cards']


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


		#The urls for ajax request
		self.match_position = 'http://data.champdas.com/getMatchPositionListAjax.html'
		self.match_person   = 'http://data.champdas.com/getMatchPersonAjax.html'
		self.match_static   = 'http://data.champdas.com/getMatchStaticListAjax.html'
		self.match_attack   = 'http://data.champdas.com/getMatchStaticListAjax.html'
		self.match_defence  = 'http://data.champdas.com/getMatchDefencesRateAjax.html'
		self.match_top      = 'http://data.champdas.com/getMatchTopAjax.html'



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

			 
			#res_data[0]['index']['team'] = {'teamName': team['name'], 'year': 2016}
			#get all players in the team
			for player_data in res_data[0]['index']:
				player_data['team'] = [{'teamName': team['name'], 'year': 2016}]

				#print json.dumps(player_data, indent=4, separators=(',', ': '), ensure_ascii=False, encoding="utf-8")
				inser_db_result = db.players.insert_one(player_data)
				print inser_db_result 


			#print res_data[0]['index']


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
	

	def getGameLink(self, round_link):
		html = _urlRequest(round_link)
		soup = BeautifulSoup("".join(html), "lxml")
		against = soup.find('div', class_="against")
		lis = against.find_all('li')
		rnd_games_list = []
		for li in lis:
			a = li.find('span').find('a')
			link = self.url_prefix + a['href'].encode('ascii', 'ignore')
			rnd_games_list.append(link)
		
		return rnd_games_list

	def getGameDetail(self, link):
		#First get game id   
		print link
		game_id = link.split('-')[1]
		game_id = game_id.replace('.html', '')
		print game_id

		#Get players attend in this match
		data = {'matchId': game_id}
		res = _postRequest(self.s, 'http://data.champdas.com/getMatchPersonAjax.html', data)
		players_data = json.loads(res.text)

		player_id_list = []
		for player in players_data:
			player_id_list.append(str(player['personId']))


		#get the right format for posting trace data
		player_post_data = ",".join("'" + player + "'" for player in player_id_list)
		#print player_post_data
		code_list = _getAllStats('all')
		code_post_data = ",".join("'" + code + "'" for code in code_list)
		#print code_post_data
		trace_post_data = {'matchId': game_id, 'half': 0, 'personId': player_post_data, 'code': code_post_data}
		res = _postRequest(self.s, 'http://data.champdas.com/getTraceAjax.html', trace_post_data)
		trace_res_data = json.loads(res.text)
		#print json.dumps(trace_res_data, indent=4, separators=(',', ': '), ensure_ascii=False, encoding="utf-8")


		match_stat_post_data = {'matchId': game_id, 'half': ''}
		res = _postRequest(self.s, 'http://data.champdas.com/getMatchStaticListAjax.html', match_stat_post_data)
		match_stat_res_data = json.loads(res.text)
		# print json.dumps(match_stat_res_data, indent=4, separators=(',', ': '), ensure_ascii=False, encoding="utf-8")


		match_att_post_data = {'matchId': game_id, 'half': ''}
		res = _postRequest(self.s, 'http://data.champdas.com/getMatchAttackAjax.html', match_att_post_data)
		match_att_res_data = json.loads(res.text)
		# print json.dumps(match_att_res_data, indent=4, separators=(',', ': '), ensure_ascii=False, encoding="utf-8")


		match_def_post_data = {'matchId': game_id, 'half': ''}
		res = _postRequest(self.s, 'http://data.champdas.com/getMatchDefencesRateAjax.html', match_def_post_data)
		match_def_res_data = json.loads(res.text)
		# print json.dumps(match_def_res_data, indent=4, separators=(',', ': '), ensure_ascii=False, encoding="utf-8")


		match_pos_post_data = {'matchId': game_id, 'half': 0}
		res = _postRequest(self.s, 'http://data.champdas.com/getMatchPositionListAjax.html', match_pos_post_data)
		match_pos_res_data = json.loads(res.text)
		#print json.dumps(match_pos_res_data, indent=4, separators=(',', ': '), ensure_ascii=False, encoding="utf-8")




		db_data = {}
		db_data['playerList'] = match_pos_res_data
		db_data['matchId'] = game_id
		db_data['events'] = trace_res_data
		db_data['stats'] = match_stat_res_data
		db_data['stats_att'] = match_att_res_data
		db_data['stats_def'] = match_def_res_data

		
		inser_db_result = db.matches.insert_one(db_data)
		print inser_db_result

		#print json.dumps(db_data, indent=4, separators=(',', ': '), ensure_ascii=False, encoding="utf-8")

		

if __name__ == '__main__':
	myCrawler = CBCrawler("http://data.champdas.com/match/scheduleDetail-1-2016-1.html")
	myCrawler.getRoundLink()
	for rnd in myCrawler.round_list:
		rnd_games_list = myCrawler.getGameLink(rnd)
		for game in rnd_games_list:
			myCrawler.getGameDetail(game)
			



	#Get players in each team and save players' data to mongodb   
	#myCrawler.getTeamLink()
	#myCrawler.getTeamPlayer()
