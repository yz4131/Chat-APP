# Virtual Chat App

Name: Yuqin Zhao
UNI: yz4131

Running Instructions:
+ 1. Run Server:
  python3 ChatApp.py -s <portNum>
+ 2. Run Client:
  python3 ChatApp.py -c <user_name> '' <server_portNum> <client_portNum>
  ('' is <server_ip>)
+ 3. Chat:
  send <name> <message>
+ 4. Sign Out:
  dereg <user_name>
+ 5. Sign Back:
  reg <user_name>
+ 6. Group Chat:
  send_all <message>

Features:
+ 1. Capable of 1 to 1 Chat
+ 2. Capable of Group-Chat
+ 3. Capable of Login and Sign out
+ 4. Capable of storing offline messages when Signed out

Algorithms:
+ 1. Multithreading: React to user's input and listen to incoming messages at the same time
+ 2. 1 <-> 1 chat: When a user is registered, he/she send his/her information to the server and server broadcast to all users.
Besides, the server also broadcast all the other user's information to the new user. All users use server's broadcast to update
their own local table, which record all the other users' basic information. When send message to another user, he/she will first
look up the local table and find the receiver's ip and send the message.
+ 3. Group Chat: Assume that every user belongs to a same single group. When a user want to send group messages, he/she send the message
directly to the server and server send the group messages to all users except the sender.
+ 4. Dereg/Reg: When a user wants to dereg, he/she sends request to the server. After receiving the ack from server, he/she can log out.
If not, after retrying 5 times, he/she automatically log out. After the server receives the dereg request, it will first ack this request, and broadcast this information to all users. When a user regs, he/she send request to the server and after receiving the ack,
he/she signs in. Server will broadcast this information to all users and send off-line messages temporarily stored in server to this
user, which will be discussed later.
+ 5. Offline Messages: When a user is offline, he/she cannot receive any messages. So if a sender sends a message directly to a user, if ack is not received, the sender will send this message to the server instead and require the server to store it. When it comes to group messages, the server will check all the other users' status and store the messages for users who are currently offline.

Data Structure:
+ 1. Python Dictionary
+ 2. Defaultdict from Collections
+ 3. Python List

Known Bugs:
+ 1. If use wrong <server_portNum> or <server_ip> when running client, program will stuck
