#!/usr/bin/python

import xml.etree.ElementTree as ET
import random
import smtplib
import ssl
import operator
from User import User
from Credentials import cred_password
from email.mime.multipart import MIMEMultipart
from email.mime.application import MIMEApplication
from email.mime.text import MIMEText
from email.mime.image import MIMEImage
from os.path import exists

def parse_xml(input):
	temp = []
	for user in input.iter('User'):
		fname = user[0].text
		lname = user[1].text
		email = user[2].text
		luser = User(fname,lname,email)
		temp.append(luser)
	return temp

def send_mail(strTo,strFrom,subject,body,files=[]):
	msgRoot = MIMEMultipart('related')
	msgRoot['Subject'] = subject
	msgRoot['From'] = strFrom
	msgRoot['To'] = strTo

	#Create alternative message with images using Multipart
	msgAlternative = MIMEMultipart('alternative')
	msgRoot.attach(msgAlternative)

	msgText = MIMEText( body, 'html')
	msgAlternative.attach(msgText)

	fp = open('SecretSanta.jpg', 'rb')
	msgImage = MIMEImage(fp.read())
	fp.close()

	msgImage.add_header('Content-ID', '<image1>')
	msgRoot.attach(msgImage)

	#if the backup file doesn't exist then we won't try attaching it'
	if(exists(files)):
		part = MIMEApplication(open(files, 'rb').read())
		# After the file is closed
		part['Content-Disposition'] = 'attachment; filename="backup_master.xml"'
		msgRoot.attach(part)

	#The below code is the new way to login to Gmail.
	#We now need to use AppPasswords for Gmail
	#ref -> https://www.abstractapi.com/guides/sending-email-with-python
	password = cred_password # <- this is the new AppPassword
	ctx = ssl.create_default_context()

	with smtplib.SMTP_SSL("smtp.gmail.com", port=465, context=ctx) as server:
		server.login(strFrom,password)
		server.sendmail(strFrom, strTo, msgRoot.as_string())
		server.quit()

def sortfullname(e):
	#First we need to generate the fullname by concatenating fname + lname
	fullname = e[0].first_name + e[0].last_name
	return fullname

#The oldlistfile is the default backup xml. It should be included in the location of the script
def check_repeats(oldlistfile,newlist):
	#we are going to compare the old list with the new list and see if we get any repeats
	#if we find a repeat we will return TRUE else FALSE
	newlist.sort(key = sortfullname)

	#if the backup file doesn't exist then there are no repeats
	if(not exists(oldlistfile)):
		return False

	#Parse the oldlistfile and convert it into the same format as new list
	#List<User,User>
	oldroot = ET.parse(oldlistfile).getroot()
	oldlist = []

	#Pull the gift buyers f/l names and enter in child[0]. Repeat for gift receivers in child[1]
	for exchange in oldroot.iter('Exchange'):
		buyer = exchange.find('GiftBuyer')
		buyerfname = buyer[0].text
		buyerlname = buyer[1].text
		buyeremail = 'test@email.com' #we don't need the email for comp
		buyeruser = User(buyerfname,buyerlname,buyeremail)
		receiver = exchange.find('GiftReceiver')
		receiverfname = receiver[0].text
		receiverlname = receiver[1].text
		receiveremail = 'test@email.com' #we don't need the email for comp
		receiveruser = User(receiverfname,receiverlname,receiveremail)
		templist = []
		templist.append(buyeruser)
		templist.append(receiveruser)
		oldlist.append(templist)

	index = 0
	oldlist.sort(key=sortfullname)

	#if we get a match from last years list return true
	for x in oldlist:
		if ((x[0].first_name == newlist[index][0].first_name) &
			(x[0].last_name == newlist[index][0].last_name)   &
			(x[1].first_name == newlist[index][1].first_name) &
			(x[1].last_name == newlist[index][1].last_name)):
				return True
		else:
			index=index+1

	return False

#Globals
inputFile = 'inputDataFile.xml' # <- Need to add as an argument for UI eventually
year = '2022'
#Get the list of users from xml file
finput = ET.parse(inputFile).getroot()
senders = parse_xml(finput)
receivers = list(senders)
#print(senders.__str__)
#print(receivers.__str__)
distinct = False
while (distinct == False):
	random.shuffle(receivers)
	check = list(zip(receivers,senders))
	for x in check:
		#If we get a matching pair, try again
		if((x[0] == x[1]) | 
			#exclude the previous years recipient
			(check_repeats('backup_master.xml',check))):
				distinct = False
				break
		else:
			distinct = True

import xml.etree.cElementTree as master_list_xml
root = master_list_xml.Element("Backup")
master_list = ""
#master_list_array
#<Backup>
#	<Exchange>
#		<GiftBuyer>
#			<FirstName>User1FirstName</FirstName>
#			<LastName>User1LastName</LastName>
#		</GiftBuyer>
#		<GiftReceiver>
#			<FirstName>User1FirstName</FirstName>
#			<LastName>User1LastName</LastName>
#		</GiftReceiver>
#	</Exchange>
for pair in check:
	#Create an xml representation of the list pairs instead of string
	exchange = master_list_xml.SubElement(root,"Exchange")

	#Add GiftBuyer
	gift_buyer = master_list_xml.SubElement(exchange,"GiftBuyer")
	master_list_xml.SubElement(gift_buyer, "FirstName").text = pair[0].first_name
	master_list_xml.SubElement(gift_buyer, "LastName").text = pair[0].last_name

	#Add GiftReceiver
	gift_receiver = master_list_xml.SubElement(exchange,"GiftReceiver")
	master_list_xml.SubElement(gift_receiver, "FirstName").text = pair[1].first_name
	master_list_xml.SubElement(gift_receiver, "LastName").text = pair[1].last_name

	#print(pair[0].first_name + " " + pair[0].last_name + " : " + pair[1].first_name + " " + pair[1].last_name)
	master_list += pair[0].first_name + " " + pair[0].last_name + " : " + pair[1].first_name + " " + pair[1].last_name + "\n"

#Finish writing the backup xml file
tree = ET.ElementTree(root)
tree.write("backup_master.xml")

#email code
#send list of everyone to me
strFrom = 'your email address'
strTo = 'your email address'
subject = 'Secret Santa Master List ' + year
body = """<br>
		    <b>Merry Christmas everyone!</b>
			<br>
			<p>Secret Santa is back by popular demand.</p>
			<b>This is the master list for all participants. Don't share this with anyone!</b>
			<br>
			""" + str(master_list) + """
			<img src="cid:image1">
			<br> """

send_mail(strTo,strFrom,subject,body,"backup_master.xml")

#send to everyone who their secret santa is
for user in check:
	strFrom = 'your email address'
	strTo = user[0].email
	subject = str(user[0].fname) + ' Secret Santa ' + year

	body = """<br>
			    <b>Merry Christmas everyone!</b>
				<br>
				<p>Secret Santa is back by popular demand.</p>
				<p>This year, you will give a gift to:<b> """ + user[1].first_name + """ """ + user[1].last_name + """</b></p>
				<p>I'm looking forward to seeing you all again soon!</p>
				<img src="cid:image1">
				<br> """

	send_mail(strTo,strFrom,subject,body)
