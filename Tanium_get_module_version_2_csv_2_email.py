# import the basic python packages we need
import os
import sys
import json
import binascii
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
from cryptography.fernet import Fernet
import requests 
import xmltodict
from openpyxl import Workbook
from openpyxl.styles import Font
import urllib3
from requests.auth import HTTPBasicAuth
requests.packages.urllib3.disable_warnings()


# setup path for excel file
excel_file = '<File_Path.xlsx>'

#empty variables for handling encryption and authentication
base_url = ""
username = ""
key = ""
uncipher_text = ""
cipher_suite = ""
encryptedpwd = ""

# function to authenticate and run code on each server
def get_module_info(servers):
	wb = Workbook()		#open workbook
	for server in servers:
		# establish our connection info for the Tanium Server
		if server == '<server1>':
			base_url = 'https://<server1>.com'
			username = '<base64_username>'
			key = '<base64_fernet_key>'
			cipher_suite = Fernet(key)
			with open('<path to cipher text file>', 'rb') as file_object1:
				for line in file_object1:
					encryptedpwd = line
			
		elif server == '<server2>': 
			base_url = 'https://<server2>.com'	
			username = 'base64_username'
			key = 'base64_fernet_key'
			cipher_suite = Fernet(key)
			with open('<path to cipher text file>', 'rb') as file_object2:
				for line in file_object2:
					encryptedpwd = line

		#authenticate to host and get a sessionid
		http = urllib3.PoolManager()
		handshake = HTTPBasicAuth(binascii.a2b_base64(username).strip(), binascii.a2b_base64((cipher_suite.decrypt(encryptedpwd))).strip())
		r = requests.post(base_url + '/auth',verify=False,auth=handshake)
		sessionid = r.content

		#use existing session to dump server_info json and load into python
		server_info = requests.get(base_url + '/api/v2/server_info',verify=False, headers={'session': sessionid})
		json_input = (json.dumps(server_info.json(), indent=4, sort_keys=True, ensure_ascii=False))
		json_load = json.loads(json_input)

		#parse through the JSON returning only the "Installed_Solutions" module, version, and last updated date and create lists for each one.
		
		module = []
		version = []
		last_updated = []

		for key,value in json_load["data"]["Diagnostics"]["Installed_Solutions"].items():
				module.append(key)
				for k,v in value.items():
					if k == "version":
						version.append(v)
					if k == "last_updated":	
						last_updated.append(v)

		

		#hit Tanium's site and parse the xml to get available module versions
		underscore_removed = []
		available_version = {}
		version_available = []
		url = ""

		#grab the platform version to hit the right URL
		platform_version = json_load["data"]["Diagnostics"]["Settings"]["Version"]

		#setup variable for Tanium's site that has the available versions
		if (str(platform_version).find("7.2.") != -1):
			url = 'https://content.tanium.com/files/initialcontent/72/manifest.xml'
		elif (str(platform_version).find("7.3.") != -1):
			url = 'https://content.tanium.com/files/initialcontent/73/manifest.xml'
		  
		# creating HTTP response object from given url 
		resp = requests.get(url) 

		#convert xml to a dictionary  
		xml2dict =  xmltodict.parse(resp.content)

		"""cycle through dict to get down to the module information, compare name of module for matches from the module list (after removing underscore from name), append to a new dictionary match hits and the availble module version (encoding in ascii to remove the u')
		""" 
		for k,v in xml2dict['content_manifest'].items():
			for list in v:
				for k,v in list.items():
					if k == 'name':
						for item in module:
							remove_underscore = item.replace('_', ' ')
							if remove_underscore == v:
								available_version[v] = (list['version'].encode('ascii'))

		"""
		cycle through the module list (removing underscore from name) and compare that to the dictionary key name, if a match is found append the value (version) to new list, otherwise append 'Not Found'.  Essenstially keeping the lists lined up.
		"""  					
		for name in module:
			removed_underscore = name.replace('_', ' ')
			if available_version.has_key(removed_underscore):
				version_available.append(available_version[removed_underscore])
			else:
				version_available.append('Not Found')

		combined = sorted(zip(module, last_updated, version, version_available))

		# write to excel file all the data, making first row bold
		bold_font = Font(bold = True)		#set bold font variable

		if server == '<server1>':
			sheet1 = wb.get_sheet_by_name('Sheet')
			sheet1.title = '<server1>'
			sheet1.append(["module", "last_updated", "current_version", "available_version"])
			for cell in sheet1["1:1"]:
				cell.font = bold_font
			for i in combined:
				sheet1.append(i) 
				
		elif server == '<server2>':
			sheet2 = wb.create_sheet('<server2>')
			sheet2.append(["module", "last_updated", "current_version", "available_version"])
			for cell in sheet2["1:1"]:
				cell.font = bold_font
			for i in combined:
				sheet2.append(i)
		
	wb.save(excel_file) 	#save workbook

			
get_module_info(['<server1>','<server2>'])

#email the spreadsheet off

recipient_list = ['user@domain.com']

for recipient in recipient_list:

	email_sender = 'tanium@domain.com'
	email_recipient = recipient

	subject = 'Tanium Module Versions'

	msg = MIMEMultipart()
	msg['From'] = email_sender
	msg['To'] = email_recipient
	msg['Subject'] = subject

	body = 'See attached module version report...'
	msg.attach(MIMEText(body,'plain'))

	filename = 'Module_Versions.xlsx'
	attachment  =open(excel_file,'rb')

	part = MIMEBase('application','octet-stream')
	part.set_payload((attachment).read())
	encoders.encode_base64(part)
	part.add_header('Content-Disposition',"attachment; filename= "+filename)

	msg.attach(part)
	text = msg.as_string()
	server = smtplib.SMTP('<mail_server>',25)
	server.starttls()
	server.login(email_user,email_password)


	server.sendmail(email_sender,email_recipient,text)
	server.quit()

#close file handles and remove files
attachment.close()
os.remove(excel_file)

