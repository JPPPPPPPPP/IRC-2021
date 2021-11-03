#!/bin/python3
import socket, sys, threading
from threading import RLock

Max_Message_Size = 1024
Max_Activity_Count = 20
MAX_NUM_CLIENTS = 50

bind_ip = '127.0.0.2'
bind_port = 9993

"""
Comandos de Responsavel de local
	REGISTERSITE <nome> <lotação> <tempoPermanencia> <saldo>
	-Regista um local

	SALDO <identificador de local>
	-Retorna o saldo

	UNREGISTERSITE <identificador de local>
	-Desregista um local

	CREATEACTIVITY <local> <tipo> <destinatário> <lotação> <duração> <pontuação> <custo>
	-Cria uma atividade para um local

	MODIFYACTIVITY <identificador> <campo a modificar> <novo valor de campo>
	-Modifica uma atividade de um local

	REMOVEACTIVITY <identificador de atividade>
	-Remove uma atividade de um local
"""

#to ensure the identifiers are unique i use a whole number. it is set always to 1 more than the highest numbered identifier so it is always different
nextSiteIdentifier = 1
nextActiIdentifier = 1

#Lists to hold data
allSites = []
allActivities = []
allUsers = []
allWarnings = []

#Constants for filenames
ACTIVITY_FILE_NAME			=		"atividades.txt"
SITE_FILE_NAME 				=		"locais.txt"
USER_FILE_NAME 				=		"utentes.txt"
WARNING_FILE_NAME 			=		"avisos.txt"

#OK Messages
SiteRegisterSuccess 		= 		'OK: {} Site registered successfully'
SiteRemoveSuccess 			= 		'OK: 1 Site has been removed successfully'
GetSaldo					= 		'OK: The current balance is: {}'
ActivityCreatedSuccess 		= 		'OK: {} Activity created successfully'
ActivityModifiedSuccess 	= 		'OK: 1 Activity modified successfully'
ActivityRemovedSuccess 		= 		'OK: 1 Activity removed successfully'

#ERROR Messages
InvalidCommand 				= 		'ERROR: Invalid command'
SaldoUnsucBadParam			=		'ERROR: 0 Saldo not displayed. Parameters incorrect or missing'
ActiRegUnsucNoSite			=		'ERROR: 0 Activity not created. No site was found with that name'
SaldoUnsucNoSiteFound		=		'ERROR: 0 Saldo not displayed. No site found with that identifier'
SiteRegUnsucBadParam 		= 		'ERROR: 0 Site not registered. Parameters incorrect or missing'
SiteRegUnsucNameInUse 		= 		'ERROR: 0 Site not registered. Name already in use'
SiteRemUnsucBadParam		=		'ERROR: 0 Site not removed. Parameters incorrect or missing'
SiteRemUnsucBadId 			= 		'ERROR: 0 Site not removed. No site found with that identifier'
ActiRegUnsucBadParam 		= 		'ERROR: 0 Activity not created. Parameters incorrect or missing'
ActiRegUnsucTypeInUse 		= 		'ERROR: 0 Activity not created. Activity type already in use'
ActiRegUnsucMaxActi 		= 		'ERROR: 0 Activity not created. Maximum number of activities reached'
ActiModUnsucBadId 			= 		'ERROR: 0 Activity not modified. No activity found with that identifier'
ActiModUnsucBadParam 		= 		'ERROR: 0 Activity not modified. Parameters incorrect or missing'
ActiModUnsucActiRunning 	=		'ERROR: 0 Activity not modified. Activity is still running'
ActiRemUnsucBadParam		= 		'ERROR: 0 Activity not removed. Parameters incorrect or missing'
ActiRemUnsucBadId 			=		'ERROR: 0 Activity not removed. No activity found with that identifier'
ActiRemUnsucActiRunning		=		'ERROR: 0 Activity not removed. Activity is still running'

allSocks = []
lock = RLock()

#This funciton loads in the data in the activity file
def loadActivities():
	global allActivities
	actiFile = open(ACTIVITY_FILE_NAME, 'r')
	for x in actiFile:
		allActivities.append(x)
	actiFile.close()
#func end

#this function loads in the data in the site file
def loadSites():
	global allSites
	siteFile = open(SITE_FILE_NAME, 'r')
	for x in siteFile:
		allSites.append(x)
	siteFile.close()
#func end

#this function loads in the data in the utente file
def loadUtentes():
	global allUsers
	userFile = open(USER_FILE_NAME, 'r')
	for x in userFile:
		allUsers.append(x)
	userFile.close()
#func end

#this function runs the load functions
def loadFiles():
	global allSites
	global allActivities
	global allUsers
	
	#sets arrays to empty so they can be loaded in again
	allSites = []
	allActivities = []
	allUsers = []

	loadActivities()
	loadSites()
	loadUtentes()
#func end

#this function saves the site data to the site file
def saveSites():
	global allSites
	siteFile = open(SITE_FILE_NAME, 'w')
	for site in allSites:
		siteFile.write(site)
	siteFile.close()
#func end

#this function saves the activity data to the activity file 
def saveActivities():
	global allActivities
	actiFile = open(ACTIVITY_FILE_NAME, 'w')
	for activity in allActivities:
		actiFile.write(activity)
	actiFile.close()
#func end

#this function saves the warning data to the warning file 
def saveWarnings():
	global allWarnings
	warnFile = open(WARNING_FILE_NAME, 'w')
	for warning in allWarnings:
		warnFile.write(warning)
	warnFile.close()
#func end

#this function runs the save functions
def saveFiles():
	saveSites()
	saveActivities()
	saveWarnings()
#func end

#this function sets next identifier values
def setIdentifiers():
	global nextSiteIdentifier
	global nextActiIdentifier
	maxSite = 1
	maxActi = 1
	if(allSites != []):
		for x in allSites:
			temp = x.split('|')
			if int(temp[0]) > int(maxSite):
				maxSite = temp[0]
		nextSiteIdentifier = int(maxSite) + 1

	if(allActivities != []):	
		for x in allActivities:
			temp = x.split('|')
			if int(temp[0]) > int(maxActi):
				maxActi = temp[0]
		nextActiIdentifier = int(maxActi) + 1
#func end

#this funciton handles the REGISTERSITE command
def REGISTERSITE(message):
	global nextSiteIdentifier
	global allSites
	duplicateName = False
	msg = message.upper()
	msg = msg[:-1:]
	msg = msg.split(" ")
	#checks quantity of parameters is correct
	if(len(msg) != 5):
		return SiteRegUnsucBadParam
	#checks if the parameters values are valid
	try:
		thing = int(msg[2])
		thing = int(msg[3])
		thing = int(msg[4])
	except ValueError:
		return SiteRegUnsucBadParam
	#checks for name in use
	for site in allSites:
		temp = site.split("|")
		if(msg[1] == temp[1].upper()):
			duplicateName = True
	if(duplicateName):
		return SiteRegUnsucNameInUse
	else:
		#actually adds the site
		temp = message.split(" ")
		temp = str(nextSiteIdentifier) + "|" + temp[1] + "|" +  temp[2] + "|" +  temp[3] + "|" +  temp[4]
		allSites.append(temp)
		nextSiteIdentifier += 1
		return SiteRegisterSuccess.format(nextSiteIdentifier - 1)
#func end

def UNREGISTERSITE_aux_WARNING(site):
	global allUsers
	global allWarnings
	site = site.split("|")
	for user in allUsers:
		temp = user.split("|")
		if(site[0].upper() == temp[1].upper()):
			allWarnings.append(temp[0] + "|" + site[1] + "\n")
#func end

#this funciton handles the UNREGISTERSITE command
def UNREGISTERSITE(message):
	global allSites
	invalidId = True
	msg = message.upper()
	msg = msg[:-1:]
	msg = msg.split(" ")
	#checks parameter count
	if(len(msg) != 2):
		return SiteRemUnsucBadParam
	#send warning to users at the site
	#checks if identifier is valid
	for site in allSites:
		temp = site.split("|")
		if(msg[1] == temp[0]):
			#removes site if id is valid since all other checks passed
			UNREGISTERSITE_aux_WARNING(site)
			allSites.remove(site)
			invalidId = False
	if(invalidId):
		return SiteRemUnsucBadId
			
	return SiteRemoveSuccess
#func end

#this funciton handles the SALDO command
def SALDO(message):
	msg = message.upper()
	msg = msg[:-1:]
	msg = msg.split(" ")
	#checks quantity of parameters is correct
	if(len(msg) != 2):
		return SaldoUnsucBadParam
	global allSites
	#cycles through all sites
	for site in allSites:
		temp = site.split("|")
		#if the right site is found then it returns the saldo
		if(temp[0] == msg[1]):
			return GetSaldo.format(temp[4])
	#if no site matches the id then there is no site with that id
	return SaldoUnsucNoSiteFound
#func end

#this funciton handles the CREATEACTIVITY command
def CREATEACTIVITY(message):
	global nextActiIdentifier
	global allActivities
	global allSites
	msg = message[:-1:]
	msg = msg.split(" ")
	siteFound = False
	#checks if activities are maxed out
	if(len(allActivities) >= Max_Activity_Count):
		return ActiRegUnsucMaxActi
	#checks parameter count
	if(len(msg) != 8):
		return ActiRegUnsucBadParam
	#checks if the parameters values are valid
	try:
		thing = int(msg[4])
		thing = int(msg[5])
		thing = int(msg[6])
		thing = int(msg[7])
	except ValueError:
		return ActiRemUnsucBadParam
	#checks if the site exists
	for site in allSites:
		temp = site.split("|")
		if(temp[1].upper() == msg[1].upper()):
			siteFound = True
	if(not siteFound):
		return ActiRegUnsucNoSite
	#checks if type is in use
	for activity in allActivities:
		temp = activity.split("|")
		if(temp[2] == msg[2]):
			return ActiRegUnsucTypeInUse
	#checks if maximum number of activities has been reached
	if(len(allActivities) >= Max_Activity_Count):
		return ActiRegUnsucMaxActi
	else:
		#if it makes it past the checks then it can be added
		tempy = str(nextActiIdentifier) + "|" + msg[1] + "|" +  msg[2] + "|" +  msg[3] + "|" +  msg[4] + "|" +  msg[5] + "|" +  msg[6] + "|" +  msg[7] + "\n"
		allActivities.append(tempy)
		nextActiIdentifier += 1
		return ActivityCreatedSuccess.format(nextActiIdentifier - 1)
#func end

#this funciton handles the REMOVEACTIVITY command
def REMOVEACTIVITY(message):
	global allActivities
	invalidId = True
	activityRunning = False
	msg = message.upper()
	msg = msg[:-1:]
	msg = msg.split(" ")
	#checks parameters
	if(len(msg) != 2):
		return ActiRemUnsucBadParam
	#checks if activity is running
	if(activityRunning):
		#cant check this yet
		return ActiRemUnsucActiRunning
	#checks if id is valid
	for activity in allActivities:
		temp = activity.split("|")
		if(msg[1] == temp[0]):
			#removes activity if id is valid since all other checks passed
			allActivities.remove(activity)
			invalidId = False
	if(invalidId):
		return ActiRemUnsucBadId
	#if it makes it past the checks then a success message is sent
	return ActivityRemovedSuccess
#func end

#this function is an auxilliary function to MODIFYACTIVITY that returns the string of the activity post modification
def MODIFYACTIVITY_Aux(message, acti):
	msg = message.upper()
	msg = msg[:-1:]
	msg = msg.split(" ")
	a = acti.split("|")
	response = ''
	x = 0
	#checks if the parameter is an int
	try:
		thing = int(msg[3])
	except ValueError:
		return 'bad param'
	#changes activity
	if(msg[2] == 'LOTACAO'):
		#sums up all elements into a string and only changing the lotacao
		for temp in a:
			if(x == 4):
				response += msg[3] + "|"
			else:
				response += temp + "|"
			x += 1
		return response[:-1:]
	elif(msg[2] == 'PONTUACAO'):
		#sums up all elements into a string and only changing the pontuacao
		for temp in a:
			if(x == 6):
				response += msg[3] + "|"
			else:
				response += temp + "|"
			x += 1
		return response[:-1:]
	elif(msg[2] == 'CUSTO'):
		#sums up all elements into a string and only changing the custo
		for temp in a:
			if(x == 7):
				response += msg[3] + "|"
			else:
				response += temp + "|"
			x += 1
		return response[:-1:]

	#if the value to change isnt one of the three then there are bad parameters
	return 'bad param'
#func end

#this function handles the MODIFYACTIVITY command
def MODIFYACTIVITY(message):
	global allActivities
	invalidId = True
	activityRunning = False
	msg = message.upper()
	msg = msg[:-1:]
	msg = msg.split(" ")
	if(len(msg) != 4):
		return ActiModUnsucBadParam
	if(activityRunning):
		#cant check this yet
		return ActiModUnsucActiRunning
	#checks for valid id
	for activity in allActivities:
		temp = activity.split("|")
		if(msg[1] == temp[0]):
			#tries to modify activity if id is valid
			thing = MODIFYACTIVITY_Aux(message, activity)
			maybeRemove = activity
			invalidId = False
	if(invalidId):
		return ActiModUnsucBadId
	#when the return is this then the parameters specified the element to change wrongly
	if(thing == 'bad param'):
		return ActiModUnsucBadParam
	#if it passes all the checks then the modification can go through
	allActivities.remove(maybeRemove)
	allActivities.append(thing)
	return ActivityModifiedSuccess

#func end

#this funciton processes the message in case it is from the responsavel do local
def process_message_responsavel(message):
	msg = message.upper()
	msg = msg[:-1:]
	msg = msg.split(" ")
	response = 'default response'
	if(msg[0] == 'REGISTERSITE'):
		response = REGISTERSITE(message)
	elif(msg[0] == 'UNREGISTERSITE'):
		response = UNREGISTERSITE(message)
	elif(msg[0] == 'SALDO'):
		response = SALDO(message)
	elif(msg[0] == 'CREATEACTIVITY'):
		response = CREATEACTIVITY(message)
	elif(msg[0] == 'MODIFYACTIVITY'):
		response = MODIFYACTIVITY(message)
	elif(msg[0] == 'REMOVEACTIVITY'):
		response = REMOVEACTIVITY(message)
	#save data after every command in case the server dies while running something
	saveFiles()
	return response
#func end

#this funciton handles the initial client input
def process_message(message):
	loadFiles()

	response = 'default response'
	msg = message.upper()
	msg = msg[:-1:]
	msg = msg.split(" ")

	#if elif chain when other clients are implemented
	response = process_message_responsavel(message)

	if(response == 'default response'):
		response = InvalidCommand
	
	return response
#func end

#this funciton handles the client connection
def handle_client_connection(client_socket):
	try:
	    with lock:
	    	allSocks.append(client_socket)

	    while True:
	    	message = ''
	    	
	    	while(message == '' or message[-1] != '\n'):
		    	msg_from_client = client_socket.recv(Max_Message_Size)
		    	
		    	if(not msg_from_client):
		    		raise socket.timeout()
		    	
		    	message += str(msg_from_client.decode())
		    	msg_to_client = process_message(message)
		    	print('Received {}'.format(message))
		    	
		    	with lock:
		    		client_socket.send(msg_to_client.encode())
	
	except socket.timeout:
		with lock:
			for i in range(len(allSocks)):
				if(allSocks[i]==client_socket):
					del(allSocks[i])
					break
		
		client_socket.close()
		print("Client has disconnected: {} ".format(client_socket))
		exit(0)
#func end

#main function
def main():
	global server
	server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
	server.bind((bind_ip, bind_port))
	server.listen(MAX_NUM_CLIENTS)  #to accomodate a high number of clients
	loadFiles()
	setIdentifiers()
	print ('Listening on {}:{}'.format(bind_ip, bind_port))
	while True:
	    client_sock, address = server.accept()
	    print ('Accepted connection from {}:{}'.format(address[0], address[1]))
	    client_handler = threading.Thread(
	        target = handle_client_connection,
	        args = (client_sock,)
	    )
	    client_handler.start()
#func end

if(__name__ == '__main__'):
	main()
#func end