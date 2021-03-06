#!/usr/bin/python
# -*- coding: utf-8 -*-
from tokens import *
import matplotlib
matplotlib.use("Agg") # has to be before any other matplotlibs imports to set a "headless" backend
import matplotlib.pyplot as plt
import psutil
from datetime import datetime
from subprocess import Popen, PIPE, STDOUT
import operator
import collections
import os
import sys
import time
import telepot


memorythreshold = 85  # If memory usage more this %
poll = 300  # seconds

shellexecution = []
timelist = []
memlist = []
xaxis = []
settingmemth = []
setpolling = []
graphstart = datetime.now()

stopmarkup = {'keyboard': [['✋停止']]}
hide_keyboard = {'hide_keyboard': True}

def bytes2human(n):
	symbols = ('K', 'M', 'G', 'T', 'P', 'E', 'Z', 'Y')
	prefix = {}
	for i, s in enumerate(symbols):
		prefix[s] = 1 << (i + 1) * 10
	for s in reversed(symbols):
		if n >= prefix[s]:
			value = float(n) / prefix[s]
			return '%.1f%s' % (value, s)
	return "%sB" % n

def clearall(chat_id):
	if chat_id in shellexecution:
		shellexecution.remove(chat_id)
	if chat_id in settingmemth:
		settingmemth.remove(chat_id)
	if chat_id in setpolling:
		setpolling.remove(chat_id)

def plotmemgraph(memlist, xaxis, tmperiod):
	# print(memlist)
	# print(xaxis)
	plt.xlabel(tmperiod)
	plt.ylabel('% Used')
	plt.title('Memory Usage Graph')
	plt.text(0.1*len(xaxis), memorythreshold+2, 'Threshold: '+str(memorythreshold)+ ' %')
	memthresholdarr = []
	for xas in xaxis:
		memthresholdarr.append(memorythreshold)
	plt.plot(xaxis, memlist, 'b-', xaxis, memthresholdarr, 'r--')
	plt.axis([0, len(xaxis)-1, 0, 100])
	plt.savefig('/tmp/graph.png')
	plt.close()
	f = open('/tmp/graph.png', 'rb')  # some file on local disk
	return f


class YourBot(telepot.Bot):
	def __init__(self, *args, **kwargs):
		super(YourBot, self).__init__(*args, **kwargs)
		self._answerer = telepot.helper.Answerer(self)
		self._message_with_inline_keyboard = None

	def on_chat_message(self, msg):
		content_type, chat_type, chat_id = telepot.glance(msg)
		user_id = msg['from']['id']
		# Do your stuff according to `content_type` ...
		try:
			username = msg['from']['first_name'] +' '+ msg['from']['last_name']
		except:
			username = msg['from']['first_name']
		for part in psutil.disk_partitions(all=False):
			if os.name == 'nt':
				if 'cdrom' in part.opts or part.fstype == '':
					# skip cd-rom drives with no disk in it; they may raise
					# ENOENT, pop-up a Windows GUI error for a non-ready
					# partition or just hang.
					#cdrom or cant identify will be hang.
					continue
		if content_type == 'text':
			content = str(username.encode('utf-8'))+'('+str(user_id)+')'+'說：'+str(msg['text'].encode('utf-8'))
			if msg['text'].startswith('/stats') and chat_id not in shellexecution:
				bot.sendChatAction(chat_id, 'typing')
				memory = psutil.virtual_memory()
				disk = psutil.disk_usage('/')
				disk2 = psutil.disk_usage('/data')
				boottime = datetime.fromtimestamp(psutil.boot_time())
				now = datetime.now()
				timedif = "運作時間: %.1f 小時" % (((now - boottime).total_seconds()) / 3600)
				memtotal = "總記憶體: %.2f GB " % (memory.total / 1000000000)
				memavail = "可用記憶體: %.2f GB" % (memory.available / 1000000000)
				memuseperc = "已使用: " + str(memory.percent) + " %"
				diskused = "硬碟掛載1 (/): " + str(bytes2human(disk.free)) + " (" +str(disk.percent) + "%)"
				diskused2 = "硬碟掛載2 ("+ str(part.mountpoint)+"): " + str(bytes2human(disk2.free)) + " (" +str(disk2.percent) + "%)"
				pids = psutil.pids()
				pidsreply = ''
				procs = {}
				for pid in pids:
					p = psutil.Process(pid)
					try:
						pmem = p.memory_percent()
						if pmem > 0.5:
							if p.name() in procs:
								procs[p.name()] += pmem
							else:
								procs[p.name()] = pmem
					except:
						continue
				sortedprocs = sorted(procs.items(), key=operator.itemgetter(1), reverse=True)
				for proc in sortedprocs:
					pidsreply += proc[0] + " " + ("%.2f" % proc[1]) + " %\n"
				reply = timedif + "\n" + \
						memtotal + "\n" + \
						memavail + "\n" + \
						memuseperc + "\n" + \
						diskused + "\n" + \
						diskused2 + "\n\n" + \
						"CPU使用率:\n" + \
						pidsreply
				bot.sendMessage(chat_id, reply, disable_web_page_preview=True)
			elif msg['text'].startswith("/about"):
				bot.sendMessage(chat_id, 'v1.2\nGithub:\nhttps://github.com/tasi788/ServerStatsBot\nChange log:\nEnhance log\n\nToDo:\n-add Network Speed')
			elif user_id in adminchatid:  # Store adminchatid variable in tokens.py
				if msg['text'].startswith("Stop") or msg['text'] == u"✋停止":
					clearall(chat_id)
					bot.sendMessage(chat_id, "終止操作", reply_markup=hide_keyboard)
				elif msg['text'] == '/setpoll' and chat_id not in setpolling:
					bot.sendChatAction(chat_id, 'typing')
					setpolling.append(chat_id)
					bot.sendMessage(chat_id, "輸入新的更新時間，且數字必須大於10", reply_markup=stopmarkup)
				elif chat_id in setpolling:
					bot.sendChatAction(chat_id, 'typing')
					try:
						global poll
						poll = int(msg['text'])
						if poll > 10:
							bot.sendMessage(chat_id, "搞定！")
							clearall(chat_id)
						else:
							1/0
					except:
						bot.sendMessage(chat_id, "請傳送正確的數字啦，而且要大於10")
				elif msg['text'] == "/shell" and chat_id not in shellexecution:
					bot.sendMessage(chat_id, "bash shell模式", reply_markup=stopmarkup)
					shellexecution.append(chat_id)
				elif msg['text'] == "/setmem" and chat_id not in settingmemth:
					bot.sendChatAction(chat_id, 'typing')
					settingmemth.append(chat_id)
					bot.sendMessage(chat_id, "輸入記憶體警報", reply_markup=stopmarkup)
				elif chat_id in settingmemth:
					bot.sendChatAction(chat_id, 'typing')
					try:
						global memorythreshold
						memorythreshold = int(msg['text'])
						if memorythreshold < 100:
							bot.sendMessage(chat_id, "搞定！")
							clearall(chat_id)
						else:
							1/0
					except:
						bot.sendMessage(chat_id, "請傳送正確的數字啦，而且要小於100")

				elif chat_id in shellexecution:
					bot.sendChatAction(chat_id, 'typing')
					p = Popen(msg['text'], shell=True, stdin=PIPE, stdout=PIPE, stderr=STDOUT, close_fds=True)
					output = p.stdout.read()
					if output != b'':
						bot.sendMessage(chat_id, output, disable_web_page_preview=True)
					else:
						bot.sendMessage(chat_id, "沒有輸出m(._.)m", disable_web_page_preview=True)
				elif msg['text'].startswith('/memgraph'):
					bot.sendChatAction(chat_id, 'typing')
					tmperiod = "Last %.2f hours" % ((datetime.now() - graphstart).total_seconds() / 3600)
					bot.sendPhoto(chat_id, plotmemgraph(memlist, xaxis, tmperiod))
				elif content_type == 'document':
					if '.torrent' not in msg['document']['file_name']:
						content = str(username.encode('utf-8'))+'send file '+str(msg['document']['file_name'])
						bot.sendMessage(chat_id, "咪(´･_･`) 這不是種子檔吧？")
					else :
						bot.sendChatAction(chat_id, 'typing')
						bot.sendMessage(chat_id, "下載中...")
						content = str(username.encode('utf-8'))+'send file '+str(msg['document']['file_name'])
						bot.download_file(msg['document']['file_id'], '/data/download/torrent/'+str(msg['document']['file_name']))
						bot.sendChatAction(chat_id, 'typing')
						bot.sendMessage(chat_id, "已添加至下載列")
		else:
			content = str(username.encode('utf-8'))+'send file '+str(msg['document']['file_name'])
		log = '['+str(time.strftime("%Y-%m-%d %I:%M:%S"))+'] '+content+'\n'
		f = open('ServerStatsBot.txt', 'a')
		f.write(log)
		print log
		f.close()

TOKEN = telegrambot

bot = YourBot(TOKEN)
bot.message_loop()
tr = 0
xx = 0
# Keep the program running.
while 1:
	if tr == poll:
		tr = 0
		timenow = datetime.now()
		memck = psutil.virtual_memory()
		mempercent = memck.percent
		if len(memlist) > 300:
			memq = collections.deque(memlist)
			memq.append(mempercent)
			memq.popleft()
			memlist = memq
			memlist = list(memlist)
		else:
			xaxis.append(xx)
			xx += 1
			memlist.append(mempercent)
		memfree = memck.available / 1000000
		if mempercent > memorythreshold:
			memavail = "Available memory: %.2f GB" % (memck.available / 1000000000)
			graphend = datetime.now()
			tmperiod = "Last %.2f hours" % ((graphend - graphstart).total_seconds() / 3600)
			for adminid in adminchatid:
				bot.sendMessage(adminid, "警告！ 記憶體過低！\n" + memavail)
				bot.sendPhoto(adminid, plotmemgraph(memlist, xaxis, tmperiod))
	time.sleep(10)  # 10 seconds
	tr += 10
