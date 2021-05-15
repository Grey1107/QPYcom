import zipfile,zlib
import chardet
import shutil
import string
import time
import sys
import os
import hashlib
import json
import re
import tempfile
import socket,requests
import platform
# for subprocesses
import subprocess



# List drive
def getDrivers():
	available_drives = ['%s:' % d for d in string.ascii_uppercase if os.path.exists('%s:' % d)]
	return available_drives


# Determine if a file/directory exists
def ifExist(Path):
	return os.path.exists(Path)

	
	
def isFile(Path):
	return os.path.isfile(Path)



def isDir(Path):
	return os.path.isdir(Path)
	

def fileAccessPremssion(path, mode=os.F_OK):
	# OS.f_OK: Test if path exists
	# OS.r_OK: Test whether the path is readable
	# OS.w_OK: Test if path is writable
	# OS.x_OK: Test whether the path is executable
	if ifExist(path):
		return os.access(path, mode)
	else:
		return False

		
		
def fileReadAccesPremission(path):
	try:
		f=open(path)
		f.close()
		return True
	except:
		return False

		
		
def fatherDir(Path):
	# Gets the directory where the current file is located, the parent directory
	return os.path.dirname(Path)
	
	
def extractFileName(Path):
	return Path.split("\\")[-1]
	
	


def writeFile(filePath, Content="", Mode = "w", Encoding = "utf-8"):
	'''	
		R can only read
		R + readable and writable does not create files that do not exist writing from the top will overwrite the previous content at this location
		W + readable and writable If the file exists it overrides the entire file and is not created
		W can only be written to overwrite the entire file if it does not exist
		A can only be created by adding content from the bottom of the file if it does not exist
		A + Readable writable read from the top of the file add from the bottom of the file if it doesn't exist create 
	'''
	if Mode == "r" or Mode == "r+":
		Mode = "w"
	
	try:
		f = open(filePath, Mode, encoding = Encoding)
		f.write(Content)
		f.close()
		return True
	except:
		info = sys.exc_info()
		print("write file error.")
		print(info[0], info[1])
		return False


		
# Read the file
def readFile(filePath, Mode = "r", Encoding = "default"):
	'''	
		R can only read
		R + readable and writable does not create files that do not exist writing from the top will overwrite the previous content at this location
		W + readable and writable If the file exists it overrides the entire file and is not created
		W can only be written to overwrite the entire file if it does not exist
		A can only be created by adding content from the bottom of the file if it does not exist
		A + Readable writable read from the top of the file add from the bottom of the file if it doesn't exist create 
	'''
	if Mode == "w" or Mode == "a":
		Mode = "r"
		
	if Encoding == "default":
		 f = open(filePath, "rb")
		 data = f.read()
		 Encoding = chardet.detect(data)['encoding']
		
	
	try:
		f = open(filePath, Mode, encoding = Encoding)
		content = f.read()
		f.close()
		return content
	except:
		info = sys.exc_info()
		print("read file error.")
		print(info[0], info[1])
		return False	
		
		

# Create folder
# Create multiple levels of directories
def makeDir(Dir):
	if os.path.exists(Dir) == False:
		try:
			os.makedirs(Dir)
			return True
		except:
			info = sys.exc_info()
			print("make Dir error.")
			print(info[0], info[1])
			return False	
	else:
		return True
		
		

# Get file size
def getFileSize(Path):
	return os.stat(Path).st_size



# Get the file modification time (return timestamp)
def getFileMTime(Path):
	return os.stat(Path).st_mtime
	
	

# Gets a list of files in a folder/directory
def getFileList(Path):
	for i in os.walk(Path):	
		return i[2]
		break		#["xxx", "yyy", "zzz"]
def getFileList2(Path):
	tmpFileList = []
	if Path[:-2]!="\\": Path=Path+"\\"
	for i in os.walk(Path):
		for y in i[2]:
			tmpFileList.append({"name":y, "size":getFileSize(Path+y), "mtime":getFileMTime(Path+y)})
		return tmpFileList
		break
# print(getFileList2("c:"))

# Sort by file ascending
# Print (" List sorted by AGE ascending: ")
# print(sorted(getFileList2("c:"), key = lambda i: i['name']) )
# Sort by name, then by size
# print (sorted(getFileList2("c:"), key = lambda i: (i['name'], i['size'])) )
# sort descending by time
# print (sorted(getFileList2("c:"), key = lambda i: i['mtime'],reverse=True) )
	
		

# Create a clean folder		
def makeCleanDir(Dir):
	if os.path.exists(Dir) == False:
		try:
			os.makedirs(Dir)
			return True
		except:
			info = sys.exc_info()
			print("make clean Dir error0.")
			print(info[0], info[1])
			return False
	else:
		try:
			shutil.rmtree(Dir)
			while True:
				time.sleep(0.1)
				if ifExist(Dir) == False:
					break
			os.makedirs(Dir)
			return True		
		except:
			info = sys.exc_info()
			print("make clean Dir error1.")
			print(info[0], info[1])
			return False
			
			
			

def rmDir(Path):
	if os.path.exists(Path) == True:
		try:
			shutil.rmtree(Path)
			while True:
				time.sleep(0.1)
				if ifExist(Path) == False:
					break
			return True
		except:
			info = sys.exc_info()
			print("remove Dir error.")
			print(info[0], info[1])
			return False
	else:
		return True
		
		
		
def rmFile(File):
	if os.path.exists(File) == True:
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
		
		
		
# Human-friendly file sizes such as 203.3GiB
def sizeof_fmt(num, suffix='B'):
	for unit in ['','Ki','Mi','Gi','Ti','Pi','Ei','Zi']:
		if abs(num) < 1024.0:
			return "%3.1f %s%s" % (num, unit, suffix)
		num /= 1024.0
	return "%.1f %s%s" % (num, 'Yi', suffix)
	
	
	
def listDir(path):
	return os.listdir(path)
	
	
	
def listDirAll(path):
	'''	
		Top: The path to the directory to traverse
	Topdown: Optional, if True, first traverses the top directory, and every subdirectory under the top directory, otherwise first traverses the top subdirectory, the default is True
	Onerror: Optional, you need a callable object to call when walk is abnormal
	Followlinks: Optional; if True, it iterates over the directory shortcut (symbolic Link in Linux) that is actually referred to as the directory, which defaults to False
	Args: Contains a list of parameters that do not have a '-' or a '-'
	Return value: Triple (root, DIRs, Files)
	Root: Refers to the address of the directory you are currently traversing
	Dirs: List of all directory names in the current folder (excluding subdirectories)
	Files: All files in the current folder (excluding files in subdirectories)
	'''
	return os.walk(path, topdown=True, onerror=None, followlinks=False)

	
def fileNameSplit(filename):
	return os.path.splitext(filename)

	'''file = "file_test.txt"
	file_name = os.path.splitext(file)[0] # output：file_test
	file_suffix = os.path.splitext(file)[1] # output：.txt'''

# SLOBODAN ##

def copyFile(src, dst):
	shutil.copyfile(src, dst)

def unzipFile(src, dst):
	with zipfile.ZipFile(src, 'r') as zip_ref:
		zip_ref.extractall(dst)

def zipFile(src, dst):
	with zipfile.ZipFile(src, mode='w', compression=zipfile.ZIP_DEFLATED) as zip_ref:
		for file in dst:
			arcname = extractFileName(file)
			zip_ref.write(file, arcname)
	zip_ref.close()

def retrieve_file_paths(dirName):
  # setup file paths variable
	filePaths = []
  # Read all directory, subdirectories and file lists
	for root, directories, files in os.walk(dirName):
		for filename in files:
			# Create the full filepath by using os module.
			filePath = os.path.join(root, filename)
			filePaths.append(filePath)

	return filePaths

# SLOBODAN ##

#Rivern

keyTabStr = "`~!@#$%^&*()+-={}|[]\;’,/:”< >?"

# Gets the string before TAB completion
def getTabStr(tabStr):
    # Gets the last occurrence position of the specified character in a string
    lastCount = tabStr.rfind('.')
    # No. Or the last point is the first point, direct dir()
    if lastCount == -1 or lastCount == 0:
        return ''
    # Gets the character position in the last occurrence list
    for i, key in enumerate(tabStr[::-1]):
        #print(i,key)
        if key in keyTabStr:
            return (tabStr[len(tabStr) - i:lastCount])
    return (tabStr[len(tabStr)-i-1:lastCount])

#print(getTabStr(str))

# Gets the string to match after TAB completion
def setTabStr(tabStr):
    lastCount = tabStr.rfind('.')
    #print(lastCount)
    if lastCount  == -1:
        for i, key in enumerate(tabStr[::-1]):
            #print(i,key)
            if key in keyTabStr:
                return (tabStr[len(tabStr) - i:len(tabStr)])
        return (tabStr)
    else:
        return(tabStr[lastCount+1:len(tabStr)])

#print(setTabStr(str))

# Returns a TAB match
def tabListSelect(tabList,tabStr):
	
    while True:
        tabResList = []
        if tabStr.strip() == '':
            return tabList
        else:
            for i in tabList:
                if i.startswith(tabStr):
					#print(i)
                    tabResList.append(i)
            return tabResList


# Get the list information displayed after TAB completion
def getPrintInfo(tabList):
	getStr = ''
	next = 0
	tabStr = ''
	count = 0
	for i in tabList:
		lenStr = len(i)//16
		#print(lenStr)
		if lenStr == 0:
			#print(16 - len(i)%16)
			for j in range(16 - len(i)%16):
				tabStr += ' '
			#print(tabStr)
			getStr += i
			getStr += tabStr
			next += 1
			tabStr = ''
			if count == len(tabList)-1:
				continue
			if next % 4 == 0:
				getStr += '\r\n'
		if lenStr == 1:
			#print(16 - len(i) % 16)
			for j in range(16 - len(i) % 16):
				tabStr += ' '
				# print(tabStr)
			getStr += i
			getStr += tabStr
			tabStr = ''
			if next % 4 == 3:
				next += 1
			else:
				next += 2
			if count == len(tabList)-1:
				continue
			if next % 4 == 0:
				getStr += '\r\n'	
		if lenStr == 2:
			#print(16 - len(i) % 16)
			for j in range(16 - len(i) % 16):
				tabStr += ' '
				# print(tabStr)
			getStr += i
			getStr += tabStr
			tabStr = ''
			next += 3
			if count == len(tabList)-1:
				continue
			if next % 4 == 0:
				getStr += '\r\n'
		count += 1
	return getStr


def get_sha256(file_name):
    """
       Calculate the sha256 for the file
       :param file_name:
       :return:
       """
    s1 = hashlib.sha256()
    with open(file_name, 'rb') as f:
        while True:
            data = f.read(4096)
            if not data:
                break
            s1.update(data)
    return s1.hexdigest()
	
	
def get_crc32(filename):
	"""
       Calculate the crc32	for the file
       :param file_name:
       :return:
       """
	try:
		realCMD = "exes/aboot/crc32.exe " + '"' + filename + '"'
		realCMD = os.getcwd() + "\\" + realCMD.replace("/","\\")
		print(realCMD)
		p = subprocess.Popen(realCMD, shell=True, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
		out = p.stdout.read()
		print(out.decode(encoding='utf-8', errors='ignore'))
		return out.decode(encoding='utf-8', errors='ignore')
	except:
		print("Failed to get crc32 %s " % filename)


def checkSum(path_name_ls,path):
    '''
    generate checksun.json
    :param: list
    :return:
    '''
    jsonList = []
    for i in path_name_ls:
        jsonDict = {'name': "usr/" + extractFileName(i),'crc32': get_crc32(i)}
        jsonList.append(jsonDict)

    with open(path + 'checksum.json', 'w',encoding='utf-8') as f:
        json.dump(jsonList, f, ensure_ascii=False, indent=2)
		
		
		
		
def get_main_project_info(path):
	'''
    get project_info from main.py
    :param: str
    :return:str
    '''

	fw_main = readFile(path)
	
	if fw_main.find('PROJECT_NAME') == -1 or fw_main.find('PROJECT_VERSION') == -1:
		flag = -1
		return flag
	else:
		for i in fw_main.splitlines(False):
			# if 'PROJECT_NAME' in i:
				# PROJECT_NAME = i.split('=')[1].split("#")[0].strip()[1:-1]
			# if 'PROJECT_VERSION' in i:
				# PROJECT_VERSION = i.split('=')[1].split("#")[0].strip()[1:-1]
			if 'PROJECT_NAME' in i:
				str = i.split('=')[1].strip()
				PROJECT_NAME = eval(str)
				break
		for i in fw_main.splitlines(False):
			if 'PROJECT_VERSION' in i:
				str = i.split('=')[1].strip()
				PROJECT_VERSION = eval(str)
				break
	return PROJECT_NAME+"_"+PROJECT_VERSION
	
	

def remove_comments(filenameList):
	'''
	remove_comments and Generate the file with the comments removed
    :param: list
    :return: list
    '''
	remove_comments_list = []
	remove_list = []
	tmp_path = tempfile.mkdtemp()
	for i in filenameList:
		if extractFileName(i).endswith('.py'):
			source = re.sub(re.compile("#.*?\n"), "\n", open(i, 'r', encoding="utf-8").read() + '\n')
			outputFilename = tmp_path.replace("/","\\") + "\\" + extractFileName(i)
			remove_comments_list.append(outputFilename)
			remove_list.append(i)
			with open(outputFilename, "w+", encoding="utf-8") as f:
				f.write(source)
	#print(remove_list)
	#print(remove_comments_list)
	[filenameList.remove(j) for j in remove_list]
	filenameList.extend(remove_comments_list)
	return filenameList,tmp_path
    #shutil.rmtree(tmp_path)


### get info
def get_local_ip():
	s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
	try:
		s.connect(('8.8.8.8', 80))
		_ip = s.getsockname()[0]
	finally:
		s.close()
	return _ip

def get_public_ip():
	try:
		# TODO curl
		return (requests.get("http://ip.42.pl/raw").text)

	except:
		return ("0.0.0.0")

def get_platform_info():
	return(platform.platform())
###get info

###
def fifferenceFile(path,fileList):
	# filenames = ["aa.py", "cxylb.py", "main.py", "OTA.py", "test.py"]

	content = b""

	for filename in fileList:
		content += f"|start|filename|{filename}|filesize|{os.path.getsize(filename)}|filecontent|".encode()

		with open(filename, "rb") as f:
			content += f.read()
		content += b"|end|"

		data = zlib.compress(content)
		with open(path, "wb+") as f:
			f.write(data)
			
# .bin file to .zip file
def binToZip(filename):
	if filename[-3:].lower() == '.bin':
		return filename[:-3] + '.zip'
	else:
		return filename
		
		
def checkZipFile(filePath):
	for filename in os.listdir(filePath):
		if filename == 'customer_fs.bin':
			return True
	return False


