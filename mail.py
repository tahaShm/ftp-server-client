from socket import *
import base64
import time

msg = "\r\n You reached the threshold!"
endmsg = "\r\n.\r\n"
mailserver = ("mail.ut.ac.ir", 25) #Fill in start #Fill in end
clientSocket = socket(AF_INET, SOCK_STREAM)
clientSocket.connect(mailserver)
recv = clientSocket.recv(1024)
recv = recv.decode()
print("Message after connection request:" + recv)
if recv[:3] != '220':
    print('220 reply not received from server.')
heloCommand = 'HELO Taha_Hooman\r\n'
clientSocket.send(heloCommand.encode())
recv1 = clientSocket.recv(1024)
recv1 = recv1.decode()
print("Message after HELO command:" + recv1)
if recv1[:3] != '250':
    print('250 reply not received from server.')


mailFrom = "MAIL FROM: <taha.shabani@ut.ac.ir>\r\n"
clientSocket.send(mailFrom.encode())
recv2 = clientSocket.recv(1024)
recv2 = recv2.decode()
print("After MAIL FROM command: "+recv2)



#Info for username and password
username = "dGFoYS5zaGFiYW5p\r\n".encode()
password = "VGFoYTEzNzg=\r\n".encode()

authMsg = "AUTH LOGIN\r\n".encode()
clientSocket.send(authMsg)
recv_auth = clientSocket.recv(1024)
print(recv_auth.decode())

clientSocket.send(username)
recv_auth = clientSocket.recv(1024)
print(recv_auth.decode())

clientSocket.send(password)
recv_auth = clientSocket.recv(1024)
print(recv_auth.decode())

rcptTo = "RCPT TO:<shabani_taha@yahoo.com>\r\n"
clientSocket.send(rcptTo.encode())
recv3 = clientSocket.recv(1024)
recv3 = recv3.decode()
print("After RCPT TO command: "+recv3)
data = "DATA\r\n"
clientSocket.send(data.encode())
recv4 = clientSocket.recv(1024)
recv4 = recv4.decode()
print("After DATA command: "+recv4)
subject = "Subject: testing my client\r\n\r\n" 
clientSocket.send(subject.encode())
date = time.strftime("%a, %d %b %Y %H:%M:%S +0000", time.gmtime())
date = date + "\r\n\r\n"
clientSocket.send(date.encode())
clientSocket.send(msg.encode())
clientSocket.send(endmsg.encode())
recv_msg = clientSocket.recv(1024)
print("Response after sending message body:"+recv_msg.decode())
quit = "QUIT\r\n"
clientSocket.send(quit.encode())
recv5 = clientSocket.recv(1024)
print(recv5.decode())
clientSocket.close()