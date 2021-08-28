import socket 


def code_for_send(message):
  return message.encode('ascii')

def decode_for_rec(message):
  return message.decode("utf-8")

def array_to_string(commands):
    return ('-'.join(commands))

def send_and_rec(commands):
    message = array_to_string(commands)
    command_socket.send(code_for_send(message))
    data = decode_for_rec(command_socket.recv(1024))
    return data

########################## Base code ##############################

host = ""
command_port = 8000
data_port = 8001

# creating and connecting command socket
command_socket = socket.socket(socket.AF_INET,socket.SOCK_STREAM) 
command_socket.connect((host,command_port)) 

# creating and connecting data socket
data_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM) 
data_socket.connect((host,data_port))


while True:
    commands = input().split()
    if(commands[0] == "USER"):
        data = send_and_rec(commands)
        splited_data = data.split(' ')
        if(splited_data[0] == "501" or splited_data[0] == "430"):
            print(data)
        else:
            print(data)
            new_commands = input().split()
            new_data = send_and_rec(new_commands)
            print(new_data)

    elif(commands[0] == "PASS"):
        print(send_and_rec(commands))

    elif(commands[0] == "PWD"):
        print(send_and_rec(commands))
         
    elif(commands[0] == "MKD"):
        print(send_and_rec(commands))
    
    elif(commands[0] == "RMD"):
        print(send_and_rec(commands))
    
    elif(commands[0] == "LIST"):
        message = array_to_string(commands)
        command_socket.send(code_for_send(message))
        response = decode_for_rec(data_socket.recv(1024))
        confirmation = decode_for_rec(command_socket.recv(1024))
        print(confirmation)
        print(response[:-1])
    
    elif(commands[0] == "CWD"):
        print(send_and_rec(commands))
    
    elif(commands[0] == "DL"):
        message = array_to_string(commands)
        command_socket.send(code_for_send(message))
        if (len(commands) == 2):
            f = open(commands[1],'wb')
            finish_message = False
            while(not finish_message):
                download_part = data_socket.recv(1024)
                f.write(download_part)
                finish_message = command_socket.recv(1024)
            f.close()
            print(decode_for_rec(finish_message))
        else:
            print(decode_for_rec(command_socket.recv(1024)))


    elif(commands[0] == "HELP"):
        print(send_and_rec(commands))

    elif(commands[0] == "QUIT"):
        print(send_and_rec(commands))
        break



command_socket.close()
data_socket.close() 


