#!/usr/bin/env python
# -*- coding:utf-8 -*-
import copy
import hashlib
import json
import os
import subprocess
import sys
import urllib.request
import zipfile
import shutil
import threading
import datetime
from dateutil.parser import parse

from threading import Timer

import wx

from fileIO import ifExist
import time

import platform
import ctypes

import PySimpleGUI as sg
from urllib import request

# ---------------------------------------
# Author   : KingKa Wu
# Date	 : 2020-10-16
# Function : update json file process
# ---------------------------------------

check_update_time = 7200.0  # 定义自动检查更新时间间隔
url_get_timeout = 10.0  # 定义从服务器拉取文件超时时间
main_program_flag = 0  # 定义是否主程序重启flag
version_current_get = "1.4"  #定义当前工具版本
update_messageCount = 0  #定义弹窗提示次数
###########################################################################################
# Add by Kingka 2020.12.2 for update progress bar

global_filename = ""  # 定义当前升级文件名字
global_percent = 0  # 定义升级进度的百分比
bg = '#F0F0F0'
sg.SetOptions(background_color=bg, )
progressbar = [
	[sg.ProgressBar(100, orientation='h', size=(40, 20), key='progressbar', bar_color=('#008B00', '#DCDCDC'))]
]
outputwin = [
	[sg.Output(size=(40, 10))]
]
layout = [
	[sg.Frame('当前文件更新进度', title_color="#000000", layout=progressbar, background_color=bg)],
	[sg.Frame('', title_color="#000000", layout=outputwin, background_color=bg)],
]
window = sg.Window('软件更新进度', layout, no_titlebar=True, keep_on_top=False, element_justification='center')
progress_bar = window['progressbar']

'''
# 更新提示窗口
def updateWindow():
	global window
	while True:
		event, values = window.read(timeout=10)
		while 0 < global_percent < 100:
			print("\r", '>>>> Downloading   [%s]   %.1f%%\r' % (global_filename, global_percent))
			progress_bar.UpdateBar(global_percent)
			time.sleep(0.1)
	# window.close()
'''
update_lock = 0


# 更新提示窗口
def updateWindow():
	global window, global_percent, update_lock
	while True:
		event, values = window.read(timeout=10)
		while 0 < global_percent <= 100:
			if update_lock == 0 and global_percent != 100:
				print("\r")
				print("\r", '[%s] 资源包更新中，请勿操作...   ' % (global_filename))
				update_lock = update_lock + 1
			elif update_lock == 0 and global_percent == 100:
				global_percent = 0
			if update_lock != 0 and global_percent == 100:
				global_percent = 0
				update_lock = 0
				print("\r", '[%s] 资源包更新完成。' % (global_filename))
				time.sleep(3)
			progress_bar.UpdateBar(global_percent)
			time.sleep(0.1)
	# window.close()


# 定义网络请求包回调函数
def fun(blocknum, blocksize, totalsize):
	global global_percent
	global_percent = blocknum * blocksize / totalsize
	if global_percent > 1.0:
		global_percent = 1.0
	global_percent = global_percent * 100


# 检查网络连通性
def check_net(fileurl):
	try:
		request.urlopen(url=fileurl, timeout=url_get_timeout)
	except:
		return False
	return True


######################################################################################################

def cut(obj, sec):
	"""
	切割函数
	"""
	return [obj[i:i + sec] for i in range(0, len(obj), sec)]


def getLocalSpace(folder):
	"""
	获取磁盘剩余空间
	:param folder: 磁盘路径 例如 E:\\qpythontools
	:return: 剩余空间 单位 MB
	"""
	folderTemp = folder
	if not os.path.exists(folderTemp):
		folderTemp = os.getcwd()
	if platform.system() == 'Windows':
		free_bytes = ctypes.c_ulonglong(0)
		ctypes.windll.kernel32.GetDiskFreeSpaceExW(ctypes.c_wchar_p(folderTemp), None, None, ctypes.pointer(free_bytes))
		return free_bytes.value / 1024 / 1024  # / 1024  MB
	else:
		st = os.statvfs(folderTemp)
		return st.f_bavail * st.f_frsize / 1024 / 1024


def get_file_md5(file_name):
	"""
	Calculate the MD5 for the file
	:param file_name:
	:return:
	"""
	m = hashlib.md5()  # 创建md5对象
	with open(file_name, 'rb') as fobj:
		while True:
			data = fobj.read(4096)
			if not data:
				break
			m.update(data)  # 更新md5对象
	return m.hexdigest()  # 返回md5对象


def get_str_md5(content):
	"""
	Calculate the MD5 for the str file
	:param content:
	:return:
	"""
	m = hashlib.md5(content)  # 创建md5对象
	return m.hexdigest()


def restart_program():
	"""
	Restart main program
	:return:
	"""
	print("restart main exe...")
	python = sys.executable
	os.execl(python, python, *sys.argv)


# 删除目录
def rmDir(Path):
	if os.path.exists(Path):
		try:
			shutil.rmtree(Path)
			while True:
				time.sleep(0.1)
				if not ifExist(Path):
					break
			return True
		except:
			info = sys.exc_info()
			print("remove Dir error.")
			print(info[0], info[1])
			return False
	else:
		return True


# 删除文件
def rmFile(File):
	if os.path.exists(File):
		try:
			os.remove(File)
			return True
		except:
			info = sys.exc_info()
			print("remove file error.")
			print(info[0], info[1])
			return False
	else:
		return True


def delete_file(filepath):
	"""
	删除文件或者文件夹
	"""
	print("delete_file begin...")
	if filepath[0] == '{':  # 代表此路径为相对路径
		str = filepath.replace('{}', '')
		path = os.getcwd() + str
		if not os.path.exists(path):
			print("%s 文件/文件夹路径不存在!" % (path))
			return True
		else:
			if os.path.isdir(path):  # 是否是文件夹目录
				return rmDir(path)
			elif os.path.isfile(path):  # 是否是文件路径
				return rmFile(path)

	else:  # 代表此路径为绝对路径
		if not os.path.exists(filepath):
			print("%s 文件/文件夹路径不存在!" % (filepath))
			return True
		else:
			if os.path.isdir(filepath):  # 是否是文件夹目录
				return rmDir(filepath)
			elif os.path.isfile(filepath):  # 是否是文件路径
				return rmFile(filepath)


def override_file(fileurl, filepath, filemd5):
	print("override_file begin...")
	if getLocalSpace(os.getcwd()) < 500:  # 磁盘空间小于500MB
		wx.MessageDialog(None, "磁盘空间不足!", u"提醒", wx.OK).ShowModal()
		return False
	else:
		if filepath[0] == '{':  # 代表此路径为相对路径
			str = filepath.replace('{}', '')
			path = os.getcwd() + str
			delete_file(path)
			try:
				if check_net(fileurl):
					urllib.request.urlretrieve(fileurl, path, fun)
				else:
					print("服务器连接异常!")
					wx.MessageDialog(None, "服务器连接异常！", u"提醒", wx.OK).ShowModal()
			except Exception as e:
				print("出现异常:" + str(e))
			# md5校验判断
			if get_file_md5(path) == filemd5:
				print("%s md5下载文件校验通过!" % (path))
				return True
			else:
				print("%s md5下载文件校验失败!" % (path))
				return False
		else:  # 代表此路径为绝对路径
			delete_file(filepath)
			try:
				if check_net(fileurl):
					urllib.request.urlretrieve(fileurl, filepath, fun)
				else:
					print("服务器连接异常!")
					wx.MessageDialog(None, "服务器连接异常！", u"提醒", wx.OK).ShowModal()
			except Exception as e:
				print("出现异常:" + str(e))
			# md5校验判断
			if get_file_md5(filepath) == filemd5:
				print("%s md5下载文件校验通过!" % (filepath))
				return True
			else:
				print("%s md5下载文件校验失败!" % (filepath))
				return False


def download_file(fileurl, filepath, filemd5):
	print("download_file begin...")
	if getLocalSpace(os.getcwd()) < 500:  # 空间小于500MB
		wx.MessageDialog(None, "磁盘空间不足!", u"提醒", wx.OK).ShowModal()
		return False
	else:
		if filepath[0] == '{':  # 代表此路径为相对路径
			str = filepath.replace('{}', '')
			path = os.getcwd() + str
			pathTemp = path
			(path, tempfilename) = os.path.split(path)
			if os.path.exists(path):
				print("%s 下载路径存在!" % (path))
				if os.access(path, os.W_OK):
					print("%s 下载路径可以访问!" % (path))
					try:
						try:
							if check_net(fileurl):
								urllib.request.urlretrieve(fileurl, pathTemp, fun)
							else:
								print("服务器连接异常!")
								wx.MessageDialog(None, "服务器连接异常！", u"提醒", wx.OK).ShowModal()
						except Exception as e:
							print("出现异常:" + str(e))
						# md5校验判断
						if get_file_md5(pathTemp) == filemd5:
							print("%s md5下载文件校验通过!" % (pathTemp))
							return True
						else:
							print("%s md5下载文件校验失败!" % (pathTemp))
							return False
					except:
						return False
				else:
					print("% 下载路径无法访问" % (path))
					return False
			else:
				print("%s 下载路径不存在则创建" % (path))
				os.makedirs(path)
				if os.path.exists(path):
					if os.access(path, os.W_OK):
						print("%s 下载路径可以访问" % (path))
						try:
							try:
								if check_net(fileurl):
									urllib.request.urlretrieve(fileurl, pathTemp, fun)
								else:
									print("服务器连接异常!")
									wx.MessageDialog(None, "服务器连接异常！", u"提醒", wx.OK).ShowModal()
							except Exception as e:
								print("出现异常:" + str(e))
							# md5校验判断
							if get_file_md5(pathTemp) == filemd5:
								print("%s md5下载文件校验通过!" % (pathTemp))
								return True
							else:
								print("%s md5下载文件校验失败!" % (pathTemp))
								return False
						except:
							print("%s 没有权限访问!" % (path))
							return False
					else:
						print("%s 无法访问" % (path))
						return False
				else:
					print("%s 目录创建失败" % (path))
					return False
		else:  # 代表此路径为绝对路径
			filepathTemp = filepath
			(filepath, tempfilename) = os.path.split(filepath)
			if os.path.exists(filepath):
				print("%s 下载路径存在!" % (filepath))
				if os.access(filepath, os.W_OK):
					print("%s 下载路径可以访问" % (filepath))
					try:
						try:
							if check_net(fileurl):
								urllib.request.urlretrieve(fileurl, filepathTemp, fun)
							else:
								print("服务器连接异常!")
								wx.MessageDialog(None, "服务器连接异常！", u"提醒", wx.OK).ShowModal()
						except Exception as e:
							print("出现异常:" + str(e))
						# md5校验判断
						if get_file_md5(filepathTemp) == filemd5:
							print("%s md5下载文件校验通过!" % (filepathTemp))
							return True
						else:
							print("%s md5下载文件校验失败!" % (filepathTemp))
							return False
					except:
						print("%s 没有权限访问!" % (filepath))
						return False
				else:
					print("%s 下载路径无法访问" % (filepath))
					return False
			else:
				print("%s 下载路径不存在则创建!" % (filepath))
				os.makedirs(filepath)
				if os.path.exists(filepath):
					if os.access(filepath, os.W_OK):
						print("%s 下载路径可以访问!" % (filepath))
						try:
							try:
								if check_net(fileurl):
									urllib.request.urlretrieve(fileurl, filepathTemp, fun)
								else:
									print("服务器连接异常!")
									wx.MessageDialog(None, "服务器连接异常！", u"提醒", wx.OK).ShowModal()
							except Exception as e:
								print("出现异常:" + str(e))
							# md5校验判断
							if get_file_md5(filepathTemp) == filemd5:
								print("%s md5下载文件校验通过!" % (filepathTemp))
								return True
							else:
								print("%s md5下载文件校验失败!" % (filepathTemp))
								return False
						except:
							print("%s 没有权限访问!" % (filepath))
							return False
					else:
						print("%s 下载路径无法访问！" % (filepath))
						return False
				else:
					print("%s 下载路径目录创建失败！" % (filepath))
					return False


def unzip_file(zip_src, dst_dir):
	"""
	zip_src: zip文件的全路径
	dst_dir: 要解压到的目录文件夹
	"""
	r = zipfile.is_zipfile(zip_src)
	if r:
		fz = zipfile.ZipFile(zip_src, 'r')
		for file in fz.namelist():
			fz.extract(file, dst_dir)
	else:
		print('This is not zip')


def decompress_file(fileurl, filepath, filemd5):
	print("decompress_file begin...")
	if getLocalSpace(os.getcwd()) < 500:  # 磁盘空间小于500M
		wx.MessageDialog(None, "磁盘空间不足！", u"提醒", wx.OK).ShowModal()
		return False
	else:
		if filepath[0] == '{':  # 代表此路径为相对路径
			str = filepath.replace('{}', '')
			path = os.getcwd() + str
			pathTemp = path
			(path, tempfilename) = os.path.split(path)
			if os.path.exists(path):
				print("%s 解压路径存在!" % (path))
				if os.access(path, os.W_OK):
					print("%s 解压路径可以访问!" % (path))
					# md5校验判断
					if get_file_md5(pathTemp) == filemd5:
						print("%s md5下载文件校验通过!" % (pathTemp))
						decompresspath, tmpfilename = os.path.split(pathTemp)
						unzip_file(pathTemp, decompresspath)
						return True
					else:
						print("%s md5下载文件校验失败!" % (pathTemp))
						return False
				else:
					print("%s 解压路径无法访问" % (path))
					return False
			else:
				print("%s 解压路径不存在则创建" % (path))
				os.makedirs(path)
				if os.path.exists(path):
					if os.access(path, os.W_OK):
						print("%s 解压路径可以访问" % (path))
						try:
							try:
								if check_net(fileurl):
									urllib.request.urlretrieve(fileurl, pathTemp, fun)
								else:
									print("服务器连接异常!")
									wx.MessageDialog(None, "服务器连接异常！", u"提醒", wx.OK).ShowModal()
							except Exception as e:
								print("出现异常:" + str(e))
							# md5校验判断
							if get_file_md5(pathTemp) == filemd5:
								print("%s md5下载文件校验通过!" % (pathTemp))
								decompresspath, tmpfilename = os.path.split(pathTemp)
								unzip_file(pathTemp, decompresspath)
								return True
							else:
								print("%s md5下载文件校验失败!" % (pathTemp))
								return False
						except:
							print("%s 没有权限访问!" % (path))
							return False
					else:
						print("%s 无法访问" % (path))
						return False
				else:
					print("%s 目录创建失败" % (path))
					return False
		else:  # 代表此路径为绝对路径
			filepathTemp = filepath
			(filepath, tempfilename) = os.path.split(filepath)
			if os.path.exists(filepath):
				print("%s 解压路径存在!" % (filepath))
				if os.access(filepath, os.W_OK):
					print("%s 解压路径可以访问" % (filepath))
					# md5校验判断
					if get_file_md5(filepathTemp) == filemd5:
						print("%s md5下载文件校验通过!" % (filepathTemp))
						decompresspath, tmpfilename = os.path.split(filepathTemp)
						unzip_file(filepathTemp, decompresspath)
						return True
					else:
						print("%s md5下载文件校验失败!" % (filepathTemp))
						return False
				else:
					print("%s 解压路径无法访问" % (filepath))
					return False
			else:
				print("%s 解压路径不存在则创建!" % (filepath))
				os.makedirs(filepath)
				if os.path.exists(filepath):
					if os.access(filepath, os.W_OK):
						print("%s 解压路径可以访问!" % (filepath))
						try:
							try:
								if check_net(fileurl):
									urllib.request.urlretrieve(fileurl, filepathTemp, fun)
								else:
									print("服务器连接异常!")
									wx.MessageDialog(None, "服务器连接异常！", u"提醒", wx.OK).ShowModal()
							except Exception as e:
								print("出现异常:" + str(e))
							# md5校验判断
							if get_file_md5(filepathTemp) == filemd5:
								print("%s md5下载文件校验通过!" % (filepathTemp))
								decompresspath, tmpfilename = os.path.split(filepathTemp)
								unzip_file(filepathTemp, decompresspath)
								return True
							else:
								print("%s md5下载文件校验失败!" % (filepathTemp))
								return False
						except:
							print("%s 没有权限访问!" % (filepath))
							return False
					else:
						print("%s 解压路径无法访问！" % (filepath))
						return False
				else:
					print("%s 解压路径目录创建失败！" % (filepath))
					return False


def exec_file(filepath):
	print("exec_file")
	if filepath[0] == '{':  # 代表此路径为相对路径
		str = filepath.replace('{}', '')
		path = os.getcwd() + str
		if os.path.exists(path):
			if os.access(path, os.X_OK):
				os.system('python %s' % path)
				return True
			else:
				print("%s 文件执行无法访问" % (path))
				return False
		else:
			print("%s 文件执行失败!" % (path))
			wx.MessageDialog(None, "文件不存在，执行失败!", u"提醒", wx.OK).ShowModal()
			return False
	else:  # 代表此路径为绝对路径
		if os.path.exists(filepath):
			if os.access(filepath, os.X_OK):
				os.system('python %s' % filepath)
				return True
			else:
				print("%s 文件执行无法访问" % (filepath))
				return False
		else:
			wx.MessageDialog(None, "文件不存在，执行失败!", u"提醒", wx.OK).ShowModal()
			return False


def file_deal(filename, fileurl, filepath, filemd5, fileopera):
	"""
	File opera in different mode
	:return:
	"""
	global global_filename
	global_filename = filename

	if "main_program.zip" in filename:
		global main_program_flag
		main_program_flag = 1

	if fileopera == "override":  # 覆盖该文件
		return override_file(fileurl, filepath, filemd5)

	if fileopera == "download":
		return download_file(fileurl, filepath, filemd5)

	if fileopera == "delete":
		return delete_file(filepath)

	if fileopera == "decompress":
		return decompress_file(fileurl, filepath, filemd5)

	if fileopera == "exec":
		return exec_file(filepath)


def cloud_conf_get(filename):
	"""
	Get cloud conf json file
	:return:
	"""
	file_url_get_cloud_json = 'http://qpy.quectel.com/qpytools/' + filename  # 定义服务器升级URL
	# filename = 'cloud_conf.json'
	filepath = os.getcwd() + '\\' + filename
	if os.path.exists(filepath):
		print("删除旧配置文件...")
		os.remove(filepath)
	else:
		print('no such file:%s' % filepath)
	try:
		if check_net(file_url_get_cloud_json):
			urllib.request.urlretrieve(file_url_get_cloud_json, filepath, fun)
			return True
		else:
			print("服务器连接异常!")
			# wx.MessageDialog(None, "服务器连接异常!", u"提醒", wx.OK).ShowModal()
			return False
	except Exception as e:
		print("出现异常:" + str(e))
		# wx.MessageDialog(None, "服务器连接异常!", u"提醒", wx.OK).ShowModal()
		return False


def cloud_version_newst_get():
	cloud_conf_get('cloud_conf.json')
	list_cloud_file_ver_dictionary = {}
	dict_cloud_str = json.load(open(os.getcwd() + '\\' + 'cloud_conf.json', encoding="utf8"))
	count_local = dict_cloud_str["totalcount"]
	for i in range(count_local):
		list_cloud_file_ver_dictionary.setdefault(dict_cloud_str["filelist"][i]["file"], []).append(
			dict_cloud_str["filelist"][i]["ver"])  # 获取本地文件及其对应版本号
	versionCloudGet = list_cloud_file_ver_dictionary['main_program.zip'][0]
	return versionCloudGet


def json_process_handle(id):
	"""
	Json file process main entrance
	:return:
	"""
	cloud_conf_get('cloud_conf.json')
	try:
		json.load(open(os.getcwd() + '\\' + 'cloud_conf.json', encoding="utf8"))
		json.load(open(os.getcwd() + '\\' + 'local_conf.json', encoding="utf8"))
		json.load(open(os.getcwd() + '\\' + 'update_message.json', encoding="utf8"))
	except Exception as e:
		print("json load error!")
		print(e)
		result = wx.MessageDialog(None, "本地配置文件加载错误，选择 [是] 重新从服务器拉取.", u"提示", wx.YES_NO).ShowModal()
		if result == wx.ID_NO:
			return
		elif result == wx.ID_YES:
			r = cloud_conf_get('local_conf.json')
			if r is False:
				return

	dict_cloud_str = json.load(open(os.getcwd() + '\\' + 'cloud_conf.json', encoding="utf8"))
	dict_local_str = json.load(open(os.getcwd() + '\\' + 'local_conf.json', encoding="utf8"))
	dict_update_str = json.load(open(os.getcwd() + '\\' + 'update_message.json', encoding="utf8"))
	

	count_cloud = dict_cloud_str["totalcount"]
	count_local = dict_local_str["totalcount"]

	list_local_file = []  # 定义本地配置文件中所有文件列表
	list_cloud_file = []  # 定义云端配置文件中所有文件列表
	list_cloud_update_mode_unexit_file_dictionary = {}  # 定义云端配置文件在本地不存在时升级模式字典
	list_cloud_restart_unexit_file_dictionary = {}  # 定义云端配置文件本地不存在时重启应用程序字典
	list_cloud_update_mode_file_dictionary = {}  # 定义云端配置文件升级模式字典
	list_cloud_restart_file_dictionary = {}  # 定义云端配置文件重启应用程序字典

	list_cloud_file_unexit_dictionary = {}  # 定义云端升级文件在本地不存在的字典
	list_cloud_file_dictionary = {}  # 定义筛选后的需要升级云端配置文件字典  （云端总配置字典 ）
	list_local_unexit_file_dictionary = {}  # 定义云端文件在本地配置文件不存时,本地配置文件字典
	list_local_file_dictionary = {}  # 定义本地配置文件字典,用于更新升级后的本地配置文件 （本地总配置字典）

	list_local_file_ver_dictionary = {}  # 定义本地配置文件版本号字典

	restart_flag = 0  # 定义主程序是否重启操作标志
	# exit_flag = 0  # 定义主程序是否退出标志
	update_fail_flag = 0  # 定义本次升级是否成功标志
	update_select_flag = 0  # 定义用户选择升级标志
	global window  # 定义全局提示窗口属性
	# 本地文件配置属性
	for i in range(count_local):
		list_local_file.append(dict_local_str["filelist"][i]["file"])  # 获取本地文件列表
		list_local_file_ver_dictionary.setdefault(dict_local_str["filelist"][i]["file"], []).append(
			dict_local_str["filelist"][i]["ver"])  # 获取本地文件及其对应版本号
		# 创建本地配置文件属性字典
		list_local_file_dictionary.setdefault(dict_local_str["filelist"][i]["file"], []).append(dict_local_str["filelist"][i]["md5"])
		list_local_file_dictionary.setdefault(dict_local_str["filelist"][i]["file"], []).append(dict_local_str["filelist"][i]["ver"])
		list_local_file_dictionary.setdefault(dict_local_str["filelist"][i]["file"], []).append(dict_local_str["filelist"][i]["updatemode"])
		list_local_file_dictionary.setdefault(dict_local_str["filelist"][i]["file"], []).append(dict_local_str["filelist"][i]["ignore"])
		list_local_file_dictionary.setdefault(dict_local_str["filelist"][i]["file"], []).append(dict_local_str["filelist"][i]["url"])
		list_local_file_dictionary.setdefault(dict_local_str["filelist"][i]["file"], []).append(dict_local_str["filelist"][i]["updatedesp"])
		list_local_file_dictionary.setdefault(dict_local_str["filelist"][i]["file"], []).append(dict_local_str["filelist"][i]["path"])
		list_local_file_dictionary.setdefault(dict_local_str["filelist"][i]["file"], []).append(dict_local_str["filelist"][i]["opera"])
		list_local_file_dictionary.setdefault(dict_local_str["filelist"][i]["file"], []).append(dict_local_str["filelist"][i]["restart"])

	# 云端文件列表
	for i in range(count_cloud):
		list_cloud_file.append(dict_cloud_str["filelist"][i]["file"])

	list_local_file = list(set(list_local_file))  # 去除文件列表中重复文件
	list_cloud_file = list(set(list_cloud_file))  # 去除文件列表中重复文件

	# 当本地文件在云端不存在时 删除对应本地文件及相关字典
	inter = [i for i in list_local_file if i not in list_cloud_file]
	for file_process in inter:
		delete_file(list_local_file_dictionary[file_process][6])
		list_local_file.remove(file_process)
		del list_local_file_dictionary[file_process]
		del list_local_file_ver_dictionary[file_process]
		count_local = count_local - 1

	# 遍历云端的每个文件
	for i in range(count_cloud):
		if dict_cloud_str["filelist"][i]["file"] in list_local_file:
			ver_cloud = dict_cloud_str["filelist"][i]["ver"].split('*')
			ver_local = list_local_file_ver_dictionary[dict_cloud_str["filelist"][i]["file"]]
			if ver_cloud > ver_local:  # 云端文件在本地存在时，判断对应文件版本号是否不一致
				list_cloud_update_mode_file_dictionary.setdefault(dict_cloud_str["filelist"][i]["file"], []).append(
					dict_cloud_str["filelist"][i]["updatemode"])
				list_cloud_restart_file_dictionary.setdefault(dict_cloud_str["filelist"][i]["file"], []).append(dict_cloud_str["filelist"][i]["restart"])
				# 重新构建新的要升级字典  [该字典顺序不要改动]
				list_cloud_file_dictionary.setdefault(dict_cloud_str["filelist"][i]["file"], []).append(dict_cloud_str["filelist"][i]["updatemode"])
				list_cloud_file_dictionary.setdefault(dict_cloud_str["filelist"][i]["file"], []).append(dict_cloud_str["filelist"][i]["updatedesp"])
				list_cloud_file_dictionary.setdefault(dict_cloud_str["filelist"][i]["file"], []).append(dict_cloud_str["filelist"][i]["ver"])
				list_cloud_file_dictionary.setdefault(dict_cloud_str["filelist"][i]["file"], []).append(dict_cloud_str["filelist"][i]["opera"])
				list_cloud_file_dictionary.setdefault(dict_cloud_str["filelist"][i]["file"], []).append(dict_cloud_str["filelist"][i]["url"])
				list_cloud_file_dictionary.setdefault(dict_cloud_str["filelist"][i]["file"], []).append(dict_cloud_str["filelist"][i]["restart"])
				list_cloud_file_dictionary.setdefault(dict_cloud_str["filelist"][i]["file"], []).append(dict_cloud_str["filelist"][i]["path"])
				list_cloud_file_dictionary.setdefault(dict_cloud_str["filelist"][i]["file"], []).append(dict_cloud_str["filelist"][i]["md5"])
				# 更新本地配置文件字典
				list_local_file_dictionary[dict_cloud_str["filelist"][i]["file"]][0] = dict_cloud_str["filelist"][i]["md5"]
				list_local_file_dictionary[dict_cloud_str["filelist"][i]["file"]][1] = dict_cloud_str["filelist"][i]["ver"]
				if dict_cloud_str["filelist"][i]["updatemode"] == 1:
					list_local_file_dictionary[dict_cloud_str["filelist"][i]["file"]][2] = 0  # 可永久忽略
				elif dict_cloud_str["filelist"][i]["updatemode"] == 2:
					list_local_file_dictionary[dict_cloud_str["filelist"][i]["file"]][2] = 1  # 可本次忽略
				elif dict_cloud_str["filelist"][i]["updatemode"] == 3:
					list_local_file_dictionary[dict_cloud_str["filelist"][i]["file"]][2] = 2  # 强制升级
				elif dict_cloud_str["filelist"][i]["updatemode"] == 0:
					list_local_file_dictionary[dict_cloud_str["filelist"][i]["file"]][2] = 3  # 静默升级
				list_local_file_dictionary[dict_cloud_str["filelist"][i]["file"]][3] = 0  # ignore
				list_local_file_dictionary[dict_cloud_str["filelist"][i]["file"]][4] = dict_cloud_str["filelist"][i]["url"]
				list_local_file_dictionary[dict_cloud_str["filelist"][i]["file"]][5] = dict_cloud_str["filelist"][i]["updatedesp"]
				list_local_file_dictionary[dict_cloud_str["filelist"][i]["file"]][6] = dict_cloud_str["filelist"][i]["path"]
				list_local_file_dictionary[dict_cloud_str["filelist"][i]["file"]][7] = dict_cloud_str["filelist"][i]["opera"]
				list_local_file_dictionary[dict_cloud_str["filelist"][i]["file"]][8] = dict_cloud_str["filelist"][i]["restart"]
		else:  # 云端文件在本地不存在 存在全新下载文件
			list_cloud_update_mode_unexit_file_dictionary.setdefault(dict_cloud_str["filelist"][i]["file"], []).append(
				dict_cloud_str["filelist"][i]["updatemode"])
			list_cloud_restart_unexit_file_dictionary.setdefault(dict_cloud_str["filelist"][i]["file"], []).append(
				dict_cloud_str["filelist"][i]["restart"])
			# 构建本地不存在的文件字典  [该字典顺序不要改动]
			list_cloud_file_unexit_dictionary.setdefault(dict_cloud_str["filelist"][i]["file"], []).append(dict_cloud_str["filelist"][i]["updatemode"])
			list_cloud_file_unexit_dictionary.setdefault(dict_cloud_str["filelist"][i]["file"], []).append(dict_cloud_str["filelist"][i]["updatedesp"])
			list_cloud_file_unexit_dictionary.setdefault(dict_cloud_str["filelist"][i]["file"], []).append(dict_cloud_str["filelist"][i]["ver"])
			list_cloud_file_unexit_dictionary.setdefault(dict_cloud_str["filelist"][i]["file"], []).append(dict_cloud_str["filelist"][i]["opera"])
			list_cloud_file_unexit_dictionary.setdefault(dict_cloud_str["filelist"][i]["file"], []).append(dict_cloud_str["filelist"][i]["url"])
			list_cloud_file_unexit_dictionary.setdefault(dict_cloud_str["filelist"][i]["file"], []).append(dict_cloud_str["filelist"][i]["restart"])
			list_cloud_file_unexit_dictionary.setdefault(dict_cloud_str["filelist"][i]["file"], []).append(dict_cloud_str["filelist"][i]["path"])
			list_cloud_file_unexit_dictionary.setdefault(dict_cloud_str["filelist"][i]["file"], []).append(dict_cloud_str["filelist"][i]["md5"])

			# 追加更新本地配置文件字典
			list_local_unexit_file_dictionary.setdefault(dict_cloud_str["filelist"][i]["file"], []).append(dict_cloud_str["filelist"][i]["md5"])
			list_local_unexit_file_dictionary.setdefault(dict_cloud_str["filelist"][i]["file"], []).append(dict_cloud_str["filelist"][i]["ver"])
			if dict_cloud_str["filelist"][i]["updatemode"] == 1:
				list_local_unexit_file_dictionary.setdefault(dict_cloud_str["filelist"][i]["file"], []).append(0)
			elif dict_cloud_str["filelist"][i]["updatemode"] == 2:
				list_local_unexit_file_dictionary.setdefault(dict_cloud_str["filelist"][i]["file"], []).append(1)
			elif dict_cloud_str["filelist"][i]["updatemode"] == 3:
				list_local_unexit_file_dictionary.setdefault(dict_cloud_str["filelist"][i]["file"], []).append(2)
			elif dict_cloud_str["filelist"][i]["updatemode"] == 0:
				list_local_unexit_file_dictionary.setdefault(dict_cloud_str["filelist"][i]["file"], []).append(3)
			list_local_unexit_file_dictionary.setdefault(dict_cloud_str["filelist"][i]["file"], []).append(0)  # ignore 默认为0  无操作
			list_local_unexit_file_dictionary.setdefault(dict_cloud_str["filelist"][i]["file"], []).append(dict_cloud_str["filelist"][i]["url"])
			list_local_unexit_file_dictionary.setdefault(dict_cloud_str["filelist"][i]["file"], []).append(dict_cloud_str["filelist"][i]["updatedesp"])
			list_local_unexit_file_dictionary.setdefault(dict_cloud_str["filelist"][i]["file"], []).append(dict_cloud_str["filelist"][i]["path"])
			list_local_unexit_file_dictionary.setdefault(dict_cloud_str["filelist"][i]["file"], []).append(dict_cloud_str["filelist"][i]["opera"])
			list_local_unexit_file_dictionary.setdefault(dict_cloud_str["filelist"][i]["file"], []).append(dict_cloud_str["filelist"][i]["restart"])
	# 合并云端的两个字典(云端在本地存在文件字典和云端在本地不存在文件字典)
	list_cloud_update_mode_file_dictionary.update(list_cloud_update_mode_unexit_file_dictionary)
	list_cloud_restart_file_dictionary.update(list_cloud_restart_unexit_file_dictionary)
	list_cloud_file_dictionary.update(list_cloud_file_unexit_dictionary)
	list_local_file_dictionary.update(list_local_unexit_file_dictionary)

	#########################################################################
	# -------------------------------------------------------------------
	# 判断value长度是不是超过正常
	# 超过时从字典中取出来存到一个新的字典里，并从原来字典中删除
	# 与之前字典合并 ,该算法以[适应组合升级时(下载、解压、删除时)，字典key唯一情况]
	# 请不要改动该部分内容
	# -------------------------------------------------------------------
	multiple_cloud_temp = copy.deepcopy(list_cloud_file_dictionary)
	multiple_local_temp = copy.deepcopy(list_local_file_dictionary)
	temp_cloud = {}
	temp_local = {}
	for file_process in list_local_file_dictionary.items():
		if len(file_process[1]) > 9:
			del multiple_local_temp[file_process[0]]
			r = cut([i for i in file_process[1]], 9)
			for i in range(int(len(file_process[1]) / 9)):
				for j in range(9):
					temp_local.setdefault(file_process[0] + '#' + str(i), []).append(r[i][j])
	for file_process in list_cloud_file_dictionary.items():
		if len(file_process[1]) > 8:
			del multiple_cloud_temp[file_process[0]]
			if file_process[0] in multiple_local_temp.keys():
				del multiple_local_temp[file_process[0]]
			r = cut([i for i in file_process[1]], 8)
			for i in range(int(len(file_process[1]) / 8)):
				for j in range(8):
					temp_cloud.setdefault(file_process[0] + '#' + str(i), []).append(r[i][j])
				temp_local.setdefault(file_process[0] + '#' + str(i), []).append(r[i][7])  # md5
				temp_local.setdefault(file_process[0] + '#' + str(i), []).append(r[i][2])  # ver
				if r[i][0] == 1:
					temp_local.setdefault(file_process[0] + '#' + str(i), []).append(0)  # updatemode
				elif r[i][0] == 2:
					temp_local.setdefault(file_process[0] + '#' + str(i), []).append(1)  # updatemode
				elif r[i][0] == 3:
					temp_local.setdefault(file_process[0] + '#' + str(i), []).append(2)  # updatemode
				elif r[i][0] == 0:
					temp_local.setdefault(file_process[0] + '#' + str(i), []).append(3)  # updatemode
				temp_local.setdefault(file_process[0] + '#' + str(i), []).append(0)  # ignore
				temp_local.setdefault(file_process[0] + '#' + str(i), []).append(r[i][4])  # url
				temp_local.setdefault(file_process[0] + '#' + str(i), []).append(r[i][1])  # updatedesp
				temp_local.setdefault(file_process[0] + '#' + str(i), []).append(r[i][6])  # path
				temp_local.setdefault(file_process[0] + '#' + str(i), []).append(r[i][3])  # opera
				temp_local.setdefault(file_process[0] + '#' + str(i), []).append(r[i][5])  # restart
	multiple_cloud_temp.update(temp_cloud)
	multiple_local_temp.update(temp_local)
	list_cloud_file_dictionary = copy.deepcopy(multiple_cloud_temp)
	list_local_file_dictionary = copy.deepcopy(multiple_local_temp)
	#########################################################################
	if not list_cloud_file_dictionary and cloud_version_newst_get() == version_current_get:  # 比对后比对后为空则表示无新升级内容
		print("比对后无新升级文件!")
		list_alarm = []  # 定义提示列表
		list_dictionary = {}  # 定义提示更新的文件字典
		for i in list_local_file_dictionary.items():
			if (i[1][2] == 0 and i[1][3] == 0) or (i[1][2] != 0 and i[1][2] != 3 and i[1][3] != 1):
				# 存放到可永久忽略提示字典中
				list_alarm.append(i[0])
		if list_alarm:
			# 把所有要提示的文件存放到字典中
			for fileprocess in list_alarm:
				list_dictionary.setdefault(fileprocess, []).append(list_local_file_dictionary[fileprocess][0])  # md5
				list_dictionary.setdefault(fileprocess, []).append(list_local_file_dictionary[fileprocess][1])  # ver
				list_dictionary.setdefault(fileprocess, []).append(list_local_file_dictionary[fileprocess][2])  # updatemode
				list_dictionary.setdefault(fileprocess, []).append(list_local_file_dictionary[fileprocess][3])  # ignore
				list_dictionary.setdefault(fileprocess, []).append(list_local_file_dictionary[fileprocess][4])  # url
				list_dictionary.setdefault(fileprocess, []).append(list_local_file_dictionary[fileprocess][5])  # updatedesp
				list_dictionary.setdefault(fileprocess, []).append(list_local_file_dictionary[fileprocess][6])  # path
				list_dictionary.setdefault(fileprocess, []).append(list_local_file_dictionary[fileprocess][7])  # opera
				list_dictionary.setdefault(fileprocess, []).append(list_local_file_dictionary[fileprocess][8])  # restart
		if list_dictionary:
			ifUpdateForce = 0
			# 是否有强制升级
			for file_process in list_dictionary.items():
				if file_process[1][2] == 2:
					ifUpdateForce = 1
					break

			if ifUpdateForce:
				# 提示用户更新文件及信息，版本号
				update_show_text = {}  # 定义给用户提示的内容字典  提示内容包括[文件名 文件版本号  升级内容]
				for i in list_dictionary.items():
					update_show_text.setdefault(i[0], []).append(i[1][5])
					update_show_text.setdefault(i[0], []).append(i[1][1])
				s1 = update_show_text.items()
				# lst = []
				for key, value in s1:
					s3 = "更新文件：%s	更新内容：%s	更新版本：V%s" % (key, value[0], value[1])
					# lst.append('\n' + s3)
				# result = wx.MessageDialog(None, '	  '.join(lst), u"强制升级提醒", wx.YES_NO).ShowModal()
				# result = wx.MessageDialog(None, "有新的更新可用,请点击 [是] 进行更新,更新过程中请勿操作！", u"更新提示(非强制)", wx.YES_NO).ShowModal()
				# result.SetMessage(dict_update_str["update-message"])
				# result.ShowModal()
				result = wx.MessageDialog(None, dict_update_str["update-message"], u"更新提示(非强制)", wx.YES_NO).ShowModal()
				if result == wx.ID_YES:
					autoUpdataProgressBar()
					update_select_flag = 1
					for file_process in list_dictionary.items():
						if file_deal(file_process[0], file_process[1][4], file_process[1][6], file_process[1][0], file_process[1][7]) is False:
							update_fail_flag = 1
							list_local_file_dictionary[file_process[0]][3] = 0
						else:
							list_local_file_dictionary[file_process[0]][3] = 1
						if file_process[1][8] == 1:
							restart_flag = 1  # 重启程序
				elif result == wx.ID_NO:
					print("用户选择不升级，继续运行主应用程序!")
					for file_process in list_dictionary.items():
						list_local_file_dictionary[file_process[0]][3] = 0
					# exit_flag = 1
					# os.system('taskkill /f /im QPYcom.exe')
					autoMessageBar(dict_update_str)
			else:  # 只存在忽略模式
				# 提示用户更新文件及信息，版本号
				update_show_text = {}  # 定义给用户提示的内容字典  提示内容包括[文件名 文件版本号  升级内容]
				for i in list_dictionary.items():
					update_show_text.setdefault(i[0], []).append(i[1][5])
					update_show_text.setdefault(i[0], []).append(i[1][1])
				s1 = update_show_text.items()
				# lst = []
				for key, value in s1:
					s3 = "更新文件：%s	更新内容：%s	更新版本：V%s" % (key, value[0], value[1])
					# lst.append('\n' + s3)
				# result = wx.MessageDialog(None, '	  '.join(lst), u"可忽略升级提醒", wx.YES_NO | wx.CANCEL).ShowModal()
				result = wx.MessageDialog(None, "有新的更新可用,请点击 [是] 进行更新,更新过程中请勿操作！", u"可忽略升级提醒", wx.YES_NO | wx.CANCEL).ShowModal()
				if result == wx.ID_YES:
					autoUpdataProgressBar()
					update_select_flag = 1
					for file_process in list_dictionary.items():
						if file_deal(file_process[0], file_process[1][4], file_process[1][6], file_process[1][0], file_process[1][7]) is False:
							update_fail_flag = 1
							list_local_file_dictionary[file_process[0]][3] = 0
						else:
							list_local_file_dictionary[file_process[0]][3] = 1
						if file_process[1][8] == 1:
							restart_flag = 1  # 重启程序
				elif result == wx.ID_NO:
					for file_process in list_dictionary.items():
						list_local_file_dictionary[file_process[0]][3] = 2
				elif result == wx.ID_CANCEL:
					for file_process in list_dictionary.items():
						list_local_file_dictionary[file_process[0]][3] = 0
		else:
			if id == 1:
				print("手动检查无更新，窗口提示!")
				wx.MessageDialog(None, "已经是最新版本，无新升级内容", u"提醒", wx.OK).ShowModal()
			else:
				print("定时检查无更新，不窗口提示!")
				autoMessageBar(dict_update_str)
				
	else:
		# 兼容组合拳升级操作模式写法
		list_update_mode = []
		list_restart_mode = []
		for list_value_update in list_cloud_update_mode_file_dictionary.values():
			for value in list_value_update:
				list_update_mode.append(value)
		for list_value_restart in list_cloud_restart_file_dictionary.values():
			for value in list_value_restart:
				list_restart_mode.append(value)

		# 根据需要升级文件列表的[升级模式]  提示用户对应的操作
		if 3 in list_update_mode:  # 存在强制升级模式
			print("本次升级模式存在强制升级文件")
			list_cloud_file_dictionary_temp = copy.deepcopy(list_cloud_file_dictionary)
			for file_process in list_cloud_file_dictionary.items():
				if file_process[1][0] == 0:  # 静默升级文件
					del list_cloud_file_dictionary_temp[file_process[0]]
					if file_deal(file_process[0], file_process[1][4], file_process[1][6], file_process[1][7], file_process[1][3]) is False:
						update_fail_flag = 1
			if list_cloud_file_dictionary_temp:  # 剔除静默升级文件后
				sorted_dictionary = sorted(list_cloud_file_dictionary_temp.items(),
										   key=lambda list_cloud_file_dictionary: list_cloud_file_dictionary[1],
										   reverse=True)
				update_show_text = {}  # 定义给用户提示的内容字典  降序提示内容包括[文件名 文件版本号  升级内容]
				for i in sorted_dictionary:
					update_show_text.setdefault(i[0], []).append(i[1][1])
					update_show_text.setdefault(i[0], []).append(i[1][2])
				s1 = update_show_text.items()
				# lst = []
				for key, value in s1:
					s3 = "更新文件：%s	更新内容：%s	更新版本：V%s" % (key, value[0], value[1])
					# lst.append('\n' + s3)
				# result = wx.MessageDialog(None, '	  '.join(lst), u"强制升级提醒", wx.YES_NO).ShowModal()
				# result = wx.MessageDialog(None, "有新的更新可用,请点击 [是] 进行更新,更新过程中请勿操作!", u"强制升级提醒", wx.YES_NO).ShowModal()
				# result = wx.MessageDialog(None, "有新的更新可用,请点击 [是] 进行更新,更新过程中请勿操作！", u"更新提示(非强制)", wx.YES_NO)、
				result = wx.MessageDialog(None, dict_update_str["update-message"], u"更新提示(非强制)", wx.YES_NO).ShowModal()
				if result == wx.ID_YES:  # 当用户点击确认升级操作后
					autoUpdataProgressBar()
					update_select_flag = 1
					for file_process in list_cloud_file_dictionary_temp.items():
						# 只要存在强制升级则对字典中的每一个文件执行升级，判断对应文件的opera操作模式
						if file_deal(file_process[0], file_process[1][4], file_process[1][6], file_process[1][7], file_process[1][3]) is False:
							update_fail_flag = 1
							list_local_file_dictionary[file_process[0]][3] = 0
						else:
							list_local_file_dictionary[file_process[0]][3] = 1
				elif result == wx.ID_NO:  # 用户选择不升级 则直接退出主应用程序
					print("用户选择不升级，直接退出主应用程序!")
					for file_process in list_cloud_file_dictionary_temp.items():
						list_local_file_dictionary[file_process[0]][3] = 0
					# os.system('taskkill /f /im QPYcom.exe')
					# exit_flag = 1
					autoMessageBar(dict_update_str)
					return 
			#  待所有文件操作模式执行完成后判断是否有需要重启的文件   一旦有则重启主程序  否则为热更新
			if 1 in list_restart_mode:  # 存在重启主程序操作
				wx.MessageDialog(None, "程序检测到有更新,需要重启完成", u"提醒", wx.OK).ShowModal()
				restart_flag = 1
		# 找出所有静默升级的文件进行升级，同时从升级文件字典中剔除，剩余忽略模式文件  静默模式存在 0 0 0和 0 1 2这种格式
		elif 0 in list_update_mode:  # 存在静默升级模式
			print("本次升级包含静默升级文件!")
			list_cloud_file_dictionary_temp = copy.deepcopy(list_cloud_file_dictionary)
			for file_process in list_cloud_file_dictionary.items():
				if file_process[1][0] == 0:
					del list_cloud_file_dictionary_temp[file_process[0]]
					if file_deal(file_process[0], file_process[1][4], file_process[1][6], file_process[1][7], file_process[1][3]) is False:
						update_fail_flag = 1
			if list_cloud_file_dictionary_temp:  # 判断剔除静默模式后的字典是否为空,不空则提示用户有升级信息（只包含1和2两种）
				print("字典不空，既包含静默升级文件，也包含忽略升级模式文件!")
				sorted_dictionary = sorted(list_cloud_file_dictionary_temp.items(),
										   key=lambda list_cloud_file_dictionary: list_cloud_file_dictionary[1],
										   reverse=True)
				update_show_text = {}  # 定义给用户提示的内容字典  提示内容包括[文件名 文件版本号  升级内容]
				for i in sorted_dictionary:
					update_show_text.setdefault(i[0], []).append(i[1][1])
					update_show_text.setdefault(i[0], []).append(i[1][2])
				s1 = update_show_text.items()
				# lst = []
				for key, value in s1:
					s3 = "更新文件：%s	更新内容：%s	更新版本：V%s" % (key, value[0], value[1])
					# lst.append('\n' + s3)
				# result = wx.MessageDialog(None, '	  '.join(lst), u"升级提醒", wx.YES_NO | wx.CANCEL).ShowModal()
				result = wx.MessageDialog(None, "有新的更新可用,请点击 [是] 进行更新,更新过程中请勿操作!", u"升级提醒", wx.YES_NO | wx.CANCEL).ShowModal()
				if result == wx.ID_YES:  # 当用户点击确认升级操作后
					autoUpdataProgressBar()
					update_select_flag = 1
					for file_process in list_cloud_file_dictionary_temp.items():
						if file_deal(file_process[0], file_process[1][4], file_process[1][6], file_process[1][7], file_process[1][3]) is False:
							update_fail_flag = 1
							list_local_file_dictionary[file_process[0]][3] = 0
						else:
							list_local_file_dictionary[file_process[0]][3] = 1
				elif result == wx.ID_NO:  # 当用户点击忽略操作后
					print("用户选择忽略升级!")
					for file_process in list_cloud_file_dictionary_temp.items():
						list_local_file_dictionary[file_process[0]][3] = 2
				elif result == wx.ID_CANCEL:
					print("用户选择无操作!")
					for file_process in list_cloud_file_dictionary_temp.items():
						list_local_file_dictionary[file_process[0]][3] = 0
			else:
				print("字典为空，只包含全0静默升级文件!")
			#  待所有文件操作模式完成后判断是否有需要重启的文件   一旦有则重启整个应用程序  否则为热更新
			if 1 in list_restart_mode:  # 存在重启程序操作
				# wx.MessageDialog(None, "程序检测到有更新,需要重启完成", u"提醒", wx.OK).ShowModal()
				restart_flag = 1  # 程序重启标志位

		# 剩下的文件均是可忽略升级模式（只包含永久忽略和本次忽略） [1,1,1] [2,2,2] [1,2,1]
		else:
			print("本次升级只包含可忽略的文件")
			sorted_dictionary = sorted(list_cloud_file_dictionary.items(),
									   key=lambda list_cloud_file_dictionary: list_cloud_file_dictionary[1],
									   reverse=True)
			update_show_text = {}  # 定义给用户提示的内容字典  提示内容包括[文件名 文件版本号  升级内容]
			for i in sorted_dictionary:
				update_show_text.setdefault(i[0], []).append(i[1][1])
				update_show_text.setdefault(i[0], []).append(i[1][2])
			s1 = update_show_text.items()
			# lst = []
			for key, value in s1:
				s3 = "更新文件：%s	更新内容：%s	更新版本：V%s" % (key, value[0], value[1])
				# lst.append('\n' + s3)
			# result = wx.MessageDialog(None, '	  '.join(lst), u"升级-可忽略升级", wx.YES_NO | wx.CANCEL).ShowModal()
			result = wx.MessageDialog(None, "有新的更新可用,请点击 [是] 进行更新,更新过程中请勿操作!", u"可忽略升级提醒", wx.YES_NO | wx.CANCEL).ShowModal()
			if result == wx.ID_YES:  # 当用户点击升级操作后
				autoUpdataProgressBar()
				update_select_flag = 1
				for file_process in list_cloud_file_dictionary.items():
					if file_deal(file_process[0], file_process[1][4], file_process[1][6], file_process[1][7], file_process[1][3]) is False:
						update_fail_flag = 1
						list_local_file_dictionary[file_process[0]][3] = 0
					else:
						list_local_file_dictionary[file_process[0]][3] = 1
				#  待所有文件操作模式执行完成后判断是否有需要重启的文件   一旦有则重启主程序  否则为热更新
				if 1 in list_restart_mode:  # 存在重启程序操作
					wx.MessageDialog(None, "程序检查有更新需要重启", u"提醒", wx.OK).ShowModal()
					restart_flag = 1
			elif result == wx.ID_NO:  # 用户选择不升级 [1,1,1] [2,2,2] [1,2,1]
				print("用户选择忽略升级!")
				for file_process in list_cloud_file_dictionary.items():
					list_local_file_dictionary[file_process[0]][3] = 2
			elif result == wx.ID_CANCEL:  # 用户没有操作
				print("用户无操作!")
				for file_process in list_cloud_file_dictionary.items():
					list_local_file_dictionary[file_process[0]][3] = 0

	# 保存最新的本地配置文件字典到本地json配置文件
	local_json = {"filelist": []}
	for k in list_local_file_dictionary.keys():
		if '#' in k:  # 组合升级情况
			temp_str = k.split('#')[0]
		else:
			temp_str = k
		local_json["filelist"].append({'file': temp_str,
									   'md5': list_local_file_dictionary[k][0],
									   'ver': list_local_file_dictionary[k][1],
									   'updatemode': list_local_file_dictionary[k][2],
									   'ignore': list_local_file_dictionary[k][3],
									   'url': list_local_file_dictionary[k][4],
									   'updatedesp': list_local_file_dictionary[k][5],
									   'path': list_local_file_dictionary[k][6],
									   'opera': list_local_file_dictionary[k][7],
									   'restart': list_local_file_dictionary[k][8]},
									  )
	# local_json_over = {"totalcount": len(list(set(list_cloud_file + list_local_file)))}  # count 为合并本地云端，剔除重复元素后的长度
	local_json_over = {"totalcount": len(list_local_file_dictionary.keys())}
	local_json_over.update(local_json)
	json_str = json.dumps(local_json_over, indent=4)
	local_json_path = os.getcwd() + "\\" + "local_conf.json"
	with open(local_json_path, 'w') as json_file:
		json_file.write(json_str)

	if update_fail_flag == 1 and update_select_flag == 1:
		print("本次升级失败!")
		window.close()
		wx.MessageDialog(None, "软件更新失败! 请前往官网下载工具新版本。", u"提醒", wx.OK).ShowModal()
	elif update_fail_flag == 0 and update_select_flag == 1:
		print("本次升级成功!")
		window.close()
		wx.MessageDialog(None, "软件更新成功!", u"提醒", wx.OK).ShowModal()
	
	if restart_flag == 0:  # 应用程序是否重启操作,通过restart_flag标志来确保操作完成后才重启(这种情况代表正常启动)
		pass
	elif main_program_flag == 1 and update_fail_flag == 0:
		DETACHED_PROCESS = 0x08000000
		subprocess.call('restart.bat', creationflags=DETACHED_PROCESS)  # 执行restart.bat
	else:
		restart_program()
	'''
	if exit_flag == 0:  # 应用程序是否退出,通过exit_flag标志来确保操作完成后才重启
		pass
	else:
		os.system('taskkill /f /im QPYcom.exe.exe')
	'''


# 手动检查是否有更新   被主程序引用
def thread_process_handle():
	t = threading.Thread(target=json_process_handle, args=(1,))
	t.start()


class RepeatingTimer(Timer):
	def run(self):
		while not self.finished.is_set():
			self.function(*self.args, **self.kwargs)
			self.finished.wait(self.interval)


# 定时检查是否有更新   被主程序引用  时间为两小时
def repeat_update_check():
	global check_update_time
	t = RepeatingTimer(check_update_time, json_process_handle, args=(0,))
	t.start()


# 定义软件升级提醒窗口
def autoUpdataProgressBar():
	t1 = threading.Thread(target=updateWindow)
	t1.start()

# 定义提示窗口
def autoMessageBar(json_str):
	# global update_messageCount 
	try:
		force_read = json_str["force-read"] # 强制阅读模式
		avail_data = json_str["avail-data"] # 弹窗显示开始时间
		expire_data = json_str["expire-data"] # 弹窗显示结束时间
		payload = json_str["payload"] # 需要弹窗显示的信息
		pop_mode = json_str["pop-mode"] # 弹窗显示模式
		if int(pop_mode) > 0:
			if force_read == "0": #强制阅读模式"
				if parse(avail_data) < datetime.datetime.now() < parse(expire_data): #在有效时间内
					wx.MessageDialog(None, payload, u"更新信息提示", wx.OK).ShowModal()
					# update_message = wx.MessageBox(None, dict_update_str["payload"], u"更新信息提示", wx.YES_DEFAULT | wx.ICON_INFORMATION).ShowModal(
					json_str["pop-mode"] = int(json_str["pop-mode"]) - 1
					# print(json_str)
					with open(os.getcwd() + '\\' + 'update_message.json', 'w',encoding='utf-8') as f:
						json.dump(json_str, f, ensure_ascii=False, indent=2)					
		else:
			print("弹窗提示显示指定次数已完成")
	except:
		print("update-message配置文件加载失败")
	
	

if __name__ == '__main__':
	thread_process_handle()
	# repeat_update_check()
	# autoUpdataProgressBar()
