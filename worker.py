import websocket
import thread
import time
import os
from firebase import firebase

PROCESSES = []
# SOCKET = "ws://localhost:4080/"
SOCKET = "wss://smartify-core.azurewebsites.net:4080/"

# socket connection is open
def opened(ws):
    print "web socket connection is open!"

    def run(*args):
        for i in range(3):
            time.sleep(1)
        ws.close()
        print "thread terminating..."
        thread.start_new_thread(run, ())

# socket connection is closed
def closed(code, reason=None):
    print "socket is closed", code, reason

def on_error(ws, error):
    print error

# a message is received
def received_message(ws, m):
    print "socket message received!"

    # m always has '#' as its first character

    # input: 6#uber PHONE|MESSAGE

    # parse app name and phone number
    code = codeName(m)
    job = jobName(m)
    phone = phoneName(m)

    # terminate program if terminate command
    if 'terminate' in m:
        delete_process(m[10:])
    else:
        handle_process(code, job, phone)

# handle the process
def handle_process(code, job, phone):
    global PROCESSES

    # compute the process_id
    process_id = getProcessID(job, phone)

    # start process if the program isn't already running
    if not process_exist(process_id):
        start_process(code, job, phone, process_id)
    else:
        print("process already running")

# this function starts a process
def start_process(code, job, phone, process_id):
    global PROCESSES
    # download the py file


    PROCESSES.append(process_id)

    # delete old file
    os.system('rm ' + job[1:] + '.py')

    print("updating " + job[1:] + ".py from the Firebase cloud...")

    db = firebase.FirebaseApplication('https://smartify.firebaseio.com/apps', None)
    result = db.get('/', None)
    source = result['apps'][job[1:]]['code']

    app_file = open(job[1:] + '.py', 'w')
    app_file.write(source)
    app_file.close()
    print('ARG1: "' + code + '"')
    print('ARG2: "' + job[1:] + '"')
    print('ARG3: "' + phone + '"')

    print("weeee starting a process: " + job)
    command = '/usr/local/bin/python2.7 ' + job[1:] + '.py ' + code + ' ' + job[1:] + ' ' + phone

    # run the application
    try:
        os.system(command)
    except:
        pass


# this function deletes a process
def delete_process(process_id):
    global PROCESSES
    for i in range(len(PROCESSES)):
        if PROCESSES[i] == process_id:
            PROCESSES.remove(process_id)
            break

# this function checks if a process already exists
def process_exist(process_id):
    for i in range(len(PROCESSES)):
        if PROCESSES[i] == process_id:
            return True

    # process does not exist
    return False

def jobName(message):
    delim1 = message.index('#')
    delim2 = message.index(' ')
    return message[delim1:delim2]

def codeName(message):
    return message[0:1]

def phoneName(message):
    delim1 = message.index(' ')
    delim2 = message.index('|')
    return message[delim1+1:delim2]

def bodyName(message):
    delim = message.index('|')

    return message[delim+1:]

def getProcessID(job, phone):
    return '#' + job[:3] + str(abs(hash(phone)))[:4]

if __name__ == '__main__':

    websocket.enableTrace(True)
    ws = websocket.WebSocketApp(SOCKET,
    on_message = received_message,
    on_error = on_error,
    on_close = closed)
    ws.on_open = opened
    ws.run_forever()
