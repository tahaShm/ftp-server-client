from _thread import *
import threading
from datetime import datetime 
import select
import socket
from socket import *
import sys
import queue
import json
import os
import shutil
import base64
import time
import ssl

def getLastSlashIndex(path) :
  index = -1
  for i in range(0, len(path)): 
      if path[i] == '/': 
          index = i 
  return index       

def joinPathes(direct, fileName) : 
  if (direct[-1] == '/'):
    direct = direct[:-1]
  while (fileName[0:3] == "../") : 
    dirLastSlash = getLastSlashIndex(direct)
    direct = direct[0:dirLastSlash]
    fileName = fileName[3:]
  if (fileName[0:2] == './') :
    fileName = fileName[2:]
  return direct + '/' + fileName

def isAdminFile(direct, fileName, adminFiles) :
  path = joinPathes(direct, fileName)
  if path in adminFiles :
    return True
  return False
  
def find_in_users(username):
  user = {}
  user['password'] = ""
  user['email'] = ""
  user['alert'] = False
  user['accounting'] = False
  user['type'] = "normal"
  for i in config_data['users']:
    if (i['user'] == username):
      user['password'] = i['password']
      for u in config_data['accounting']['users']:
          if (u['user'] == username):
            user['accounting'] = True
            user['email'] = u['email']  
            user['alert'] = u['alert'] 
      for u in config_data['authorization']['admins']:
          if (u == username):
            user['type'] = "admin" 
  return user

def code_for_send(message):
  return message.encode('ascii')

def decode_for_rec(message):
  return message.decode("utf-8")

def handle_client_log(log_file, message):
  now = datetime.now() 
  now_string = now.strftime("%d/%m/%Y %H:%M:%S")
  now_string = now_string + ": " + message + "\n"
  log_file.write(now_string)


def find_user_in_accounting(username):
  for i in config_data['accounting']['users']:
    if(i['user'] == username):
      return True
  return False

def find_user_traffic(username):
  for i in config_data['accounting']['users']:
    if(i['user'] == username):
      return int(i['size'])
    
def sendThresholdEmail(receiverEmail) :
    print("Sending email...")
    msg = "\r\n You reached the threshold!"
    endmsg = "\r\n.\r\n"
    mailserver = ("mail.ut.ac.ir", 25)
    clientSocket = socket(AF_INET, SOCK_STREAM)
    clientSocket.connect(mailserver)
    recv = clientSocket.recv(1024)
    recv = recv.decode()
    # print("Message after connection request:" + recv)
    # if recv[:3] != '220':
    #     print('220 reply not received from server.')
    heloCommand = 'HELO Taha_Hooman\r\n'
    clientSocket.send(heloCommand.encode())
    recv1 = clientSocket.recv(1024)
    recv1 = recv1.decode()
    # print("Message after HELO command:" + recv1)
    # if recv1[:3] != '250':
    #     print('250 reply not received from server.')


    mailFrom = "MAIL FROM: <taha.shabani@ut.ac.ir>\r\n"
    clientSocket.send(mailFrom.encode())
    recv2 = clientSocket.recv(1024)
    recv2 = recv2.decode()
    # print("After MAIL FROM command: "+recv2)

    username = "dGFoYS5zaGFiYW5p\r\n".encode()
    password = "VGFoYTEzNzg=\r\n".encode()

    authMsg = "AUTH LOGIN\r\n".encode()
    clientSocket.send(authMsg)
    recv_auth = clientSocket.recv(1024)
    # print(recv_auth.decode())

    clientSocket.send(username)
    recv_auth = clientSocket.recv(1024)
    # print(recv_auth.decode())

    clientSocket.send(password)
    recv_auth = clientSocket.recv(1024)
    # print(recv_auth.decode())

    rcptTo = "RCPT TO:<" + receiverEmail  + ">\r\n"
    clientSocket.send(rcptTo.encode())
    recv3 = clientSocket.recv(1024)
    recv3 = recv3.decode()
    # print("After RCPT TO command: "+recv3)
    data = "DATA\r\n"
    clientSocket.send(data.encode())
    recv4 = clientSocket.recv(1024)
    recv4 = recv4.decode()
    # print("After DATA command: "+recv4)
    subject = "Subject: testing my client\r\n\r\n" 
    clientSocket.send(subject.encode())
    date = time.strftime("%a, %d %b %Y %H:%M:%S +0000", time.gmtime())
    date = date + "\r\n\r\n"
    clientSocket.send(date.encode())
    clientSocket.send(msg.encode())
    clientSocket.send(endmsg.encode())
    recv_msg = clientSocket.recv(1024)
    # print("Response after sending message body:"+recv_msg.decode())
    quit = "QUIT\r\n"
    clientSocket.send(quit.encode())
    recv5 = clientSocket.recv(1024)
    # print(recv5.decode())
    clientSocket.close()
    print("Email sent.")
    
def changeConfigFile(configData, username, userSize) :
  for user in configData['accounting']['users'] :
        if user['user'] == username :
              user['size'] = userSize
  with open('config.json', 'w') as fp:
    json.dump(configData, fp)
    


# thread function
def threaded(client, d_client, log_needed):

  is_logged_in = False
  check_user_download = False
  download_remaining = 0
  username = ""
  userPass = ""
  userEmail = ""
  userAlert = ""
  userAccounting = False
  userType = "normal"
  base_directory = os.getcwd()

  # init logging file for client actions.
  if(log_needed):
    logging_info = config_data['logging']
    if(logging_info['enable'] == True):
      log_needed = True
      log_path = logging_info['path']
      log_file = open(log_path,"a")
      
  help_message = """214\n
    USER [name]: The argument would be user for user authentication\n
    PASS [password]: This command must be followed after USER [name] and cannot be used alone\n
    PWD: This command has no arguments and is used to get the current working directory\n
    MKD (-i) [name]: Used for making a directory or file, -i tag would be used for file creation
    and directory creation is tagless\n
    RMD (-f) [name]: Used for deleting a directory or file, -f tag would be used for file creation
    and directory deletion is tagless\n
    LIST: Used for getting all the files in the current directory\n
    CWD [path]: Used for switching between directores, typing .. after CWD means goto
    last directory and not having a path means going to base directory\n
    DL [name]: download a file from server\n
    QUIT: exit the program\n"""
    
  while True:
    raw_data = client.recv(1024)

    # client is disconnected!
    if not raw_data:
      print("client disconnected. Adios!")
      break

    data = decode_for_rec(raw_data)
    data = data.split('-')
    current_path = os.path.dirname(os.path.realpath(__file__))

    ########################################## USER LOGIN ########################################## 
    if(data[0] == "USER"):
      if(len(data) != 2):
        client.send(code_for_send("501 Syntax error in parameters or arguments."))
      else:
        userInfo = find_in_users(data[1])
        password = userInfo['password']
        if (password == ""):
          client.send(code_for_send("430 Invalid username or password."))
        else:
          client.send(code_for_send("331 User name okay, need password."))
          new_raw_data = client.recv(1024)
          new_data = decode_for_rec(new_raw_data)
          new_data = new_data.split('-')
          
          if(new_data[0] != "PASS"):
            client.send(code_for_send("500 Error."))
          elif(len(new_data) != 2):
            client.send(code_for_send("501 Syntax error in parameters or arguments."))
          else:
            if (new_data[1] != password):
              client.send(code_for_send("430 Invalid username or password."))
            else:
              is_logged_in = True
              username = data[1]
              password = userPass
              userEmail = userInfo['email']
              userAlert = userInfo['alert']
              userAccounting = userInfo['accounting']
              userType = userInfo['type']
              
              if(config_data['accounting']['enable']):
                check_user_download = find_user_in_accounting(username)
                download_remaining = find_user_traffic(username)
                
              client.send(code_for_send("230 User logged in, proceed."))
              if(log_needed):
                log_info = "User " + username + " Logged In."
                handle_client_log(log_file, log_info)

  
    elif(data[0] == "PASS"):
      client.send(code_for_send("503 Bad sequence of commands."))

    ########################################## CURRENT DIRECTORY ########################################## 
    elif(data[0] == "PWD"):
      if(is_logged_in):
        if(len(data) > 1):
          client.send(code_for_send("501 Syntax error in parameters or arguments."))
        else: 
          dir_path = os.path.dirname(os.path.realpath(__file__))
          client.send(code_for_send("257 " + dir_path))
          if(log_needed):
            log_info = "User " + username + " visited working directory."
            handle_client_log(log_file, log_info)
      else:
        client.send(code_for_send("332 Need account for login."))

    ########################################## MAKE DIRECTORY ##########################################
    elif(data[0] == "MKD"):
      if (is_logged_in):
        if(len(data) == 2):
          dir = data[1]
          os.mkdir(os.path.join(current_path, dir))
          client.send(code_for_send("257 " + dir + " created."))
          
          if(log_needed):
            log_info = "User " + username + " created " + dir
            handle_client_log(log_file, log_info)
                
        elif(len(data) == 4):
          if (data[2] != "i"):
            client.send(code_for_send("501 Syntax error in parameters or arguments."))
          else:
            if (userType == 'admin' or isAdminFile(current_path, data[3], adminFiles) == False) :
              name = data[3]
              f = open(name, "x")
              client.send(code_for_send("257 " + data[3] + " created."))
              
              if(log_needed):
                log_info = "User " + username + " created " + name + " file."
                handle_client_log(log_file, log_info)
            else:
              client.send(code_for_send("550 File unavailable."))
              
        else:
          client.send(code_for_send("501 Syntax error in parameters or arguments."))   

      else:
        client.send(code_for_send("332 Need account for login."))
    

    ########################################## DELETE DIRECTORY ##########################################
    elif(data[0] == "RMD"):
      if (is_logged_in):
        if(len(data) == 2):
          name = data[1]
          if os.path.exists(name):
            if (userType == 'admin' or isAdminFile(current_path, data[1], adminFiles) == False) :
              os.remove(name)
              client.send(code_for_send("250 " + data[1] + " deleted."))
              
              if(log_needed):
                log_info = "User " + username + " deleted " + name + " file."
                handle_client_log(log_file, log_info)
            else:
                client.send(code_for_send("550 File unavailable."))
          else:
            client.send(code_for_send("500 Error."))    
            
        elif(len(data) == 4):
          if (data[2] != "f"):
            client.send(code_for_send("501 Syntax error in parameters or arguments."))
          else:
            dir = data[3]
            shutil.rmtree(os.path.join(current_path, dir))
            client.send(code_for_send("250 " + dir + " deleted."))
            
            if(log_needed):
              log_info = "User " + username + " deleted " + dir
              handle_client_log(log_file, log_info)
              
        else:
          client.send(code_for_send("501 Syntax error in parameters or arguments."))
      else:
        client.send(code_for_send("332 Need account for login."))

    ########################################## LIST ########################################## 
    elif(data[0] == "LIST"):
      if(is_logged_in):
        if(len(data) != 1):
          d_client.send(b'\x00')
          client.send(code_for_send("501 Syntax error in parameters or arguments."))
        else:
          files = [f for f in os.listdir('.') if os.path.isfile(f)]
          response = ""
          for f in files:
            response = response + f + "\n"
          d_client.send(code_for_send(response))
          client.send(code_for_send("226 List transfer done."))
          
          if(log_needed):
            log_info = "User " + username + " visited list of files."
            handle_client_log(log_file, log_info)
      else:
        d_client.send(b'\x00')
        client.send(code_for_send("332 Need account for login."))

    ########################################## CHANGE DIRECTORY ##########################################
    elif(data[0] == "CWD"):
      if (is_logged_in):
        if(len(data) == 2):
          if(data[1] == ".."):
            os.chdir("..")
            client.send(code_for_send("250 Successful Change.")) 
          else:
            os.chdir(os.path.join(current_path, data[1]))
            client.send(code_for_send("250 Successful Change."))
            
            if(log_needed):
              log_info = "User " + username + " changed directory."
              handle_client_log(log_file, log_info)   
              
        else:
          os.chdir(base_directory)
          client.send(code_for_send("250 Successful Change.")) 
          
          if(log_needed):
              log_info = "User " + username + " changed directory."
              handle_client_log(log_file, log_info)

      else:
        client.send(code_for_send("332 Need account for login."))

    ########################################## DOWNLOAD ########################################## 
    elif(data[0] == "DL"):
      if(is_logged_in):
        if(len(data) != 2):
          d_client.send(b'\x00')
          client.send(code_for_send("501 Syntax error in parameters or arguments."))
        else:
          if (userType == 'admin' or isAdminFile(current_path, data[1], adminFiles) == False) :
            file_size = os.stat(data[1]).st_size
            if(check_user_download):
              if(download_remaining < file_size):
                d_client.send(b'\x00')
                client.send(code_for_send("425 Can't open data connection"))
              else:
                download_remaining = download_remaining - file_size
                f = open(data[1],'rb')
                l = f.read(1024)
                while (l):
                  d_client.send(l)
                  l = f.read(1024)
                d_client.send(b'\x00') #specifies the end of data transmission
                f.close()
                
                client.send(code_for_send("226 Successful Download."))
                
                if(log_needed):
                  log_info = "User " + username + " downloaded " + data[1]
                  handle_client_log(log_file, log_info)
                  
                if (download_remaining < threshold and userAlert) :
                  sendThresholdEmail(userEmail)
                # print(download_remaining)  
                
            else:
              f = open(data[1],'rb')
              l = f.read(1024)
              while (l):
                d_client.send(l)
                l = f.read(1024)
              d_client.send(b'\x00')
              f.close()
              
              client.send(code_for_send("226 Successful Download."))
              
              if(log_needed):
                log_info = "User " + username + " downloaded " + data[1]
                handle_client_log(log_file, log_info)
          else:
            d_client.send(b'\x00')
            client.send(code_for_send("550 File unavailable."))       
      else:
        d_client.send(b'\x00')
        client.send(code_for_send("332 Need account for login."))


    ########################################## HELP ########################################## 
    elif(data[0] == "HELP"):
      if (len(data) == 1) :
        client.send(code_for_send(help_message))
        
        if(log_needed):
          log_info = "Help command requested."
          handle_client_log(log_file, log_info)
      else:
        client.send(code_for_send("501 Syntax error in parameters or arguments."))

    ########################################## USER QUIT ########################################## 
    elif(data[0] == "QUIT"):
      if (len(data) == 1) :
        if(is_logged_in):
          if (config_data['accounting']['enable'] and userAccounting) :
            changeConfigFile(config_data, username, download_remaining)
          
          client.send(code_for_send("221 Successful Quit."))
          
          if(log_needed):
            log_info = "User " + username + " exited."
            handle_client_log(log_file, log_info)
            
          is_logged_in = False
          check_user_download = False
          download_remaining = 0
          username = ""
          userPass = ""
          userEmail = ""
          userAlert = ""
          userAccounting = False
          userType = "normal"
        else: 
          client.send(code_for_send("332 Need account for login."))
      else:
        client.send(code_for_send("501 Syntax error in parameters or arguments."))
      
    ########################################## ELSE ##########################################
    else: 
      client.send(code_for_send("500 Error."))
      

    

  client.close()
  d_client.close()
  if(log_needed):
    log_file.close()


def get_time():
  now = datetime.now() 
  now_string = now.strftime("%d/%m/%Y %H:%M:%S")
  now_string = now_string + ": "
  return(now_string)

def log_message(log_file, message):
  log_data = get_time() + message + "\n"
  log_file.write(log_data)

########################## Base code ##############################

with open('config.json') as input_file:
  config_data = json.load(input_file)

#first inits
log_needed = False

# logging file handling
logging_info = config_data['logging']
if(logging_info['enable'] == True):
    log_needed = True
    log_path = logging_info['path']
    log_file = open(log_path,"a") 

# getting the ports
command_port = config_data['commandChannelPort']
data_port = config_data['dataChannelPort']

#get threshold
threshold = config_data['accounting']['threshold']

#get admin files
adminFileNames = config_data['authorization']['files'].copy()
current_path = os.path.dirname(os.path.realpath(__file__))
adminFiles = []
for i in range(len(adminFileNames)) :
  adminFiles.append(joinPathes(current_path, adminFileNames[i]))
print(adminFiles)  


# creating command socket
host = "" 
command_sock = socket(AF_INET, SOCK_STREAM) 
command_sock.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)
command_sock.bind((host, int(command_port)))
if(log_needed):
  log_message(log_file, "Command socket created!")
print("Command socket created!")

# creating data socket
data_socket = socket(AF_INET, SOCK_STREAM) 
data_socket.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)
data_socket.bind((host, int(data_port)))
if(log_needed):
  log_message(log_file, "Data socket created!")
print("Data socket created!")

#listening
command_sock.listen(5)
data_socket.listen(5)
print("Listening...")


# a forever loop until exit
while True:  
  c_client, addr = command_sock.accept()
  d_client, some = data_socket.accept() 
  connection_success = "Connected! host: " + str(addr[0]) + " port: " + str(addr[1])
  log_message(log_file, connection_success)
  print(connection_success)
  start_new_thread(threaded, (c_client, d_client, log_needed)) 

command_sock.close()
data_socket.close() 