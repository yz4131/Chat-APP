import socket
import sys
from collections import defaultdict
import select
import time
import threading


def server():
    class Client:
        def __init__(self, ipAdd, portNum, user_name, status):
            self.ipAdd = ipAdd
            self.portNum = portNum
            self.user_name = user_name
            self.status = status

    # initialize clients table
    all_clients = {}
    # initialize table to store users' off-line messages
    message_store = defaultdict(list)

    # input check
    if len(sys.argv) != 3:
        print("[Correct Usage: python3 server.py -s <port>]")
        exit()

    sPortNum = int(sys.argv[2])
    # input check
    if sPortNum > 65535 or sPortNum < 1024:
        print("[try a different port #]")
        exit()

    # preparing server
    sSocket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sSocket.bind(('', sPortNum))
    print('server is ready')

    # start
    while True:
        # listen
        message,cAdd = sSocket.recvfrom(2048)
        message = message.decode()
        message = message.split()

        if message[0] == "register":
            client_reg = Client(cAdd[0],int(cAdd[1]),message[1],'on')

            # check duplicate
            if message[1] in all_clients:
                sSocket.sendto('please_signin [Please sign in.]'.encode(),cAdd)
                continue

            all_clients[message[1]] = client_reg
            sSocket.sendto('registered [Welcome, You are registered.]'.encode(),cAdd)
            # print(all_clients)

            # broadcast
            for u,c in all_clients.items():
                if u != message[1]:
                    bmsg1 = "system_broadcast " + message[1] + " " + c.ipAdd + " " + str(client_reg.portNum)
                    bmsg2 = "system_broadcast " + u + " " + c.ipAdd + " " + str(c.portNum)
                    # broadcast to others
                    sSocket.sendto(bmsg1.encode(), (c.ipAdd, c.portNum))
                    # broadcast to new user
                    sSocket.sendto(bmsg2.encode(), cAdd)

        # notified leave
        if message[0] == 'signout':
            all_clients[message[1]].status = 'off'

            # ack
            ack = "dereg_suc [You are Offline. Bye.]"
            sSocket.sendto(ack.encode(), cAdd)
            # print('check')

            # broadcast
            for u,c in all_clients.items():
                if u != message[1]:
                    sSocket.sendto(("offline " + message[1]).encode(), (c.ipAdd, c.portNum))

        # sign back
        if message[0] == 'reg':
            all_clients[message[1]].status = 'on'
            for u,c in all_clients.items():
                if u != message[1]:
                    sSocket.sendto(("online" + " " + message[1]).encode(), (c.ipAdd, c.portNum))
            # send off-line messages
            if message_store[message[1]]:
                sSocket.sendto("offline_message [You have messages]".encode(), cAdd)
                for m in message_store[message[1]]:
                    m = m.split()
                    s = m[0]
                    t = m[1:6]
                    c = m[6:]
                    sSocket.sendto(("offline_message" + " " + s + ": " + " ".join(t) + " " + " ".join(c)).encode(), cAdd)
                del message_store[message[1]]
            continue

        # save off-line messages
        if message[0] == 'save_message':
            # check status
            if all_clients[message[2]].status == 'on':
                response = "Error [Client" + " " + message[2] + " " + "exits!!!]"
                sSocket.sendto(response.encode(), cAdd)
                continue

            sender = message[1]
            receiver = message[2]
            date = message[3:8]
            content = message[8:]

            message_store[receiver].append(sender + ' ' + ' '.join(date) + ' ' + ' '.join(content))
            # print(message_store)
            sSocket.sendto("ack_off [Messages received by the server and saved]".encode(), cAdd)

        # group chat
        if message[0] == 'send_all':
            # extract group message
            group_sender = message[-1]
            group_content = "Channel-Message " + group_sender + ": " + " ".join(message[1:-1])
            sSocket.sendto("ack_group [Message received by Server.]".encode(), cAdd)
            for u,c in all_clients.items():
                if c.status == 'on' and u != group_sender:
                    sSocket.sendto(group_content.encode(), (c.ipAdd, c.portNum))

                    # wait
                    wait = select.select([sSocket], [], [], 0.5)
                    if len(wait) == 0:
                        c.status = 'off'
                        # store
                        message_store[u].append(("Channel-Message " + group_sender + ": "
                                                 + time.strftime("%c") + " " + " ".join(message[1:-1])))
                        # broadcast
                        for i,j in all_clients.items():
                            if i != u:
                                sSocket.sendto(("offline " + u).encode(), (j.ipAdd, j.portNum))
                        continue
                    continue

                # offline
                if c.status == 'off' and u != group_sender:
                    message_store[u].append(("Channel-Message " + group_sender + ": "
                                             + time.strftime("%c") + " " + " ".join(message[1:-1])))


def client():
    class Client:
        def __init__(self, ipAdd, portNum, user_name, status):
            self.ipAdd = ipAdd
            self.portNum = portNum
            self.user_name = user_name
            self.status = status

    # thread
    def thread(client, local_table, cSocket):
        # start
        while True:
            message, cAdd = cSocket.recvfrom(2048)
            message = message.decode()
            message = message.split()
            # print(message)

            # error
            if message[0] == "Error":
                local_table[message[2]].status = 'on'
                print(" ".join(message[1:]))
                sys.stdout.write(">>> ")
                sys.stdout.flush()

            # update table
            if message[0] == "system_broadcast":
                local_table[message[1]] = Client(message[2], int(message[3]), message[1], 'on')
                if client.status == 'on':
                    print("[client table updated.]")
                    sys.stdout.write(">>> ")
                    sys.stdout.flush()

            if message[0] == "dereg_suc":
                sys.stdout.write(">>> ")
                sys.stdout.flush()
                client.status = 'off'
                print(" ".join(message[1:]))
                sys.stdout.write(">>> ")
                sys.stdout.flush()

            if message[0] == "send" and client.status == 'on':
                sender = message[-1]
                receiver = message[1]
                content = message[2:-1]
                print(sender + ": " + " ".join(content))
                sys.stdout.write(">>> ")
                sys.stdout.flush()
                ack = "ack_on [Message received by " + receiver + "]"
                cSocket.sendto(ack.encode(), cAdd)

            if message[0] == "Channel-Message" and client.status == 'on':
                resp = "ack_channel [Message received by " + user_name + "]"
                cSocket.sendto(resp.encode(), cAdd)
                print(" ".join(message))
                sys.stdout.write(">>> ")
                sys.stdout.flush()

            if message[0] == "ack_on":
                sys.stdout.write(">>> ")
                sys.stdout.flush()
                print(" ".join(message[1:]))
                sys.stdout.write(">>> ")
                sys.stdout.flush()

            if message[0] == "ack_off":
                sys.stdout.write(">>> ")
                sys.stdout.flush()
                print(" ".join(message[1:]))
                sys.stdout.write(">>> ")
                sys.stdout.flush()

            if message[0] == "ack_group":
                sys.stdout.write(">>> ")
                sys.stdout.flush()
                print(" ".join(message[1:]))
                sys.stdout.write(">>> ")
                sys.stdout.flush()

            if message[0] == "offline_message":
                print(" ".join(message[1:]))
                sys.stdout.write(">>> ")
                sys.stdout.flush()

            if message[0] == "online":
                local_table[message[1]].status = 'on'
                if client.status == 'on':
                    print("[client table updated.]")
                    sys.stdout.write(">>> ")
                    sys.stdout.flush()

            if message[0] == "offline":
                local_table[message[1]].status = 'off'
                if client.status == 'on':
                    print("[client table updated.]")
                    sys.stdout.write(">>> ")
                    sys.stdout.flush()
    # main
    local_table = {}
    # input check
    if len(sys.argv) != 6:
        print("[Correct Usage: python3 client.py -c <name> "
              "<server-ip> <server-port> <client-port>]")
        sys.exit()

    user_name, sIP, sPortNum, cPortNum = \
        sys.argv[2], sys.argv[3], int(sys.argv[4]), int(sys.argv[5])

    if sPortNum < 1024 or sPortNum > 65535 or cPortNum < 1024 or cPortNum > 65535:
        print("[try a different port #]")
        sys.exit()

    # correct and prompt
    sys.stdout.write(">>> ")
    sys.stdout.flush()

    # notify server
    cSocket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    send = "register " + user_name
    cSocket.sendto(send.encode(), (sIP, sPortNum))

    # receive message from server
    message, sAdd = cSocket.recvfrom(2048)
    message = message.decode()
    message = message.split()

    if message[0] == "registered":
        print(" ".join(message[1:]))
        sys.stdout.write(">>> ")
        sys.stdout.flush()

    elif message[0] == 'please_signin':
        print(" ".join(message[1:]))
        sys.stdout.write(">>> ")
        sys.stdout.flush()
    else:
        print('error')
        sys.exit()

    # thread
    client = Client(socket.gethostbyname(socket.gethostname()), cPortNum, user_name, 'on')
    threading.Thread(target=thread, args=(client, local_table, cSocket)).start()

    while True:
        input_message = input().split()

        if client.status == 'off':
            if input_message[0] == 'reg':

                # input check
                if len(input_message) != 2:
                    print("[Correct Usage: reg <name>]")
                    sys.stdout.write(">>> ")
                    sys.stdout.flush()
                    continue

                # input check
                if input_message[1] != user_name:
                    print("[Wrong Name]")
                    sys.stdout.write(">>> ")
                    sys.stdout.flush()
                    continue

                # going online and inform server
                client.status = 'on'
                reg = " ".join(input_message)
                cSocket.sendto(reg.encode(), (sIP, sPortNum))
                sys.stdout.write(">>> ")
                sys.stdout.flush()
                print('[Welcome Back]')
                sys.stdout.write(">>> ")
                sys.stdout.flush()
                continue

            else:
                print("[Wrong Input]")
                sys.stdout.write(">>> ")
                sys.stdout.flush()
                continue

        if client.status == 'on':

            if input_message[0] == 'send':

                if len(input_message) < 3:
                    print("[Correct Usage: send <name> <content>]")
                    sys.stdout.write(">>> ")
                    sys.stdout.flush()
                    continue

                else:
                    # look up receiver's ip
                    if input_message[1] not in local_table:

                        print("[Couldn't find " + input_message[1] + "]")
                        sys.stdout.write(">>> ")
                        sys.stdout.flush()
                        continue

                    # elif local_table[input_message[1]].status == 'off':
                        # print("[Receiver is currently offline]")
                        # sys.stdout.write(">>> ")
                        # sys.stdout.flush()
                        # offline_message = "save_message " + user_name + " " + input_message[1] \
                                          # + " " + time.strftime("%c") + " " + " ".join(input_message[2:])
                        #cSock et.sendto(offline_message.encode(), (sIP, sPortNum))
                        # continue

                    else:
                        rIP = local_table[input_message[1]].ipAdd
                        rPortNum = local_table[input_message[1]].portNum
                        send_message = " ".join(input_message) + " " + user_name
                        cSocket.sendto(send_message.encode(), (rIP, rPortNum))

                        # wait for ack for 500 msec
                        wait = select.select([cSocket], [], [], 0.5)
                        if len(wait[0]) == 0:
                            sys.stdout.write(">>> ")
                            sys.stdout.flush()
                            print("[No ACK from " + input_message[1] + ", message sent to server. ]")
                            sys.stdout.write(">>> ")
                            sys.stdout.flush()
                            offline_message = "save_message " + user_name + " " + input_message[1] \
                                              + " " + time.strftime("%c") + " " + " ".join(input_message[2:])
                            retry = 5
                            while retry > 0:
                                cSocket.sendto(offline_message.encode(), (sIP, sPortNum))
                                wait = select.select([cSocket], [], [], 0.5)
                                if len(wait[0]) == 0:
                                    retry -= 1
                                else:
                                    break
                            # failed
                            if retry == 0:
                                # time out
                                print("[Server not responding]")
                                sys.stdout.write(">>> ")
                                sys.stdout.flush()
                                print("[Existing]")
                                client.status = 'off'
                                sys.stdout.write(">>> ")
                                sys.stdout.flush()
                                sys.exit()

            elif input_message[0] == 'dereg':

                # input check
                if len(input_message) != 2:
                    print("[Correct Usage: dereg <name>]")
                    sys.stdout.write(">>> ")
                    sys.stdout.flush()
                    continue

                else:
                    # input check
                    if input_message[1] != user_name:
                        print("[Wrong User_name]")
                        sys.stdout.write(">>> ")
                        sys.stdout.flush()
                        continue
                    else:
                        client.status = 'off'
                        signout_msg = "signout" + " " + input_message[1]
                        retry = 5
                        while retry > 0:
                            cSocket.sendto(signout_msg.encode(), (sIP, sPortNum))
                            wait = select.select([cSocket], [], [], 0.5)
                            if len(wait[0]) == 0:
                                retry -= 1
                            else:
                                break
                        # failed
                        if retry == 0:
                            # time out
                            print("[Server not responding]")
                            print("[Existing]")
                            client.status = 'off'
                            sys.stdout.write(">>> ")
                            sys.stdout.flush()
                            continue
            # group channel
            elif input_message[0] == 'send_all':
                # input check
                if len(input_message) < 2:
                    print("[Correct Usage: send_all <content>]")
                    sys.stdout.write(">>> ")
                    sys.stdout.flush()
                    continue

                else:
                    group_message = " ".join(input_message) + " " + user_name
                    retry = 5
                    while retry > 0:
                        cSocket.sendto(group_message.encode(), (sIP, sPortNum))
                        wait = select.select([cSocket], [], [], 0.5)
                        if len(wait[0]) == 0:
                            retry -= 1
                        else:
                            break

                    if retry == 0:
                        # time out
                        print("[Server not responding.]")
                        sys.stdout.write(">>> ")
                        sys.stdout.flush()
                        sys.exit()
            else:
                print("[Wrong Input]")
                sys.stdout.write(">>> ")
                sys.stdout.flush()
                continue


if __name__ == "__main__":
    if sys.argv[1] == '-s':
        server()
    elif sys.argv[1] == '-c':
        client()
    else:
        print("[Correct Usage: python3 ChatApp.py -s <port> / python3 ChatApp.py "
              "-c <name> <server-ip> <server-port> <client-port>]")
