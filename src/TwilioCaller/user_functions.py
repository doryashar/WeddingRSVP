import logging
import asyncio
import json
import os, base64, sys
import requests, urllib3, urllib
          
from datetime import datetime
from pyngrok import ngrok as ng

logging.basicConfig(
    level=logging.DEBUG, 
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt='%d-%b-%y %H:%M:%S',
    handlers=[logging.FileHandler('ofir_voice.log')] #, logging.StreamHandler()]
    )


logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
#Set the format:
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
#Set the handler:
# logger.addHandler(logging.FileHandler('ofir_voice.log'))
logger.addHandler(logging.StreamHandler())
#Format the output:
logger.handlers[0].setFormatter(formatter)


from flask import Flask, request, Response, redirect
from flask import send_from_directory
from flask_sock import Sock, ConnectionClosed

from twilio.twiml.voice_response import VoiceResponse, Gather
from twilio.rest import Client
import threading, multiprocessing

from dotenv import load_dotenv
load_dotenv()

import db_interface as db
import gs_interface as gs

import multiprocessing        
import signal
import psutil
import atexit

def im_dead(*args, **kwargs):
    print('goodbye')
atexit.register(im_dead)
    
app = Flask(__name__)
HTTP_SERVER_PORT = os.environ.get("HTTP_SERVER_PORT", 5050)
public_url = ng.connect(HTTP_SERVER_PORT, bind_tls=True).public_url

num_of_concurrent_calls = 1
sem = threading.BoundedSemaphore(num_of_concurrent_calls)
ownpid = os.getpid()

welcome_message = 'i am here, what is the magic number?' # 'שלום! אני מתקשר בקשר לחתונה של אופיר וקובי ב20 לחודש. יש להקיש כמה אנשים יגיעו. אם לא תגיעו יש להקיש 0.'
posted_message = 'say what!?' #'המערכת לא זיהתה את תשובתכם. נא להקיש מספר ככמות האורחים אשר יגיעו לחתונה.'
too_bad = 'too bad, goodbye' #'חבל מאוד. נתראה באירוע הבא. להתראות'
great_goodbye= 'great! goodbye' #'נהדר! עדכנתי את המערכת. שיהיה המשך יום נעים.'

@app.route('/gather', methods=['GET', 'POST'])
def gather():
    """Processes results from the <Gather> prompt in /voice"""
    # Start our TwiML response
    resp = VoiceResponse()
    if 'Digits' in request.values:
        logger.debug(f"Gather: {request.values}")
        choice = request.values['Digits']
        # row = db.get_row(phone=request.values['From'])' #msgid=request.values['CallSid'], 
        if choice == '9':
            logger.info(f"phone {request.values['To']} requested callback")
            resp.redirect('/callback') #, 'https://wedding.yashar.us/calls/incoming')
            return str(resp)
        logger.info(f"phone {request.values['To']} answered with {choice}")
        gs.update_row(phone=request.values['To'].replace('+',''), timestamp=str(datetime.now()), state='answered', confirmed=choice)
        res = asyncio.run(db.update_row(phone=request.values['To'].replace('+',''), timestamp=str(datetime.now()), state='answered', confirmed=choice))        
        if not res:
            logger.error(f"Couldnt update phone: {request.values['To']} choice: {choice} --> request.values: {request.values}")
        if choice == '0':
            resp.play(f'{public_url}/voice_notes/too_bad.mp3') #resp.say(too_bad) #, language='hebrew')
            resp.hangup()
            return str(resp)
        else:
            gather = Gather(num_digits=1, timeout=5, action='/special_request')
            gather.play(f'{public_url}/voice_notes/great_goodbye.mp3') 
            resp.append(gather)
            resp.hangup()
            return str(resp)
    resp.redirect('/again')
    return str(resp)

@app.route('/callback', methods=['GET', 'POST'])
def callback():
    resp = VoiceResponse()
    to_phone = request.values['To']
    
    gs.update_row(phone=request.values['To'].replace('+',''), timestamp=str(datetime.now()), state='called', notes=f"callback to: {to_phone}")
    res = asyncio.run(db.update_row(phone=request.values['To'].replace('+',''), timestamp=str(datetime.now()), state='called', notes=f"callback to: {to_phone}"))        
    if not res:
        logger.error(f"Couldnt update phone: {request.values['To']} callback request --> request.values: {request.values}")
    resp.play(f'{public_url}/voice_notes/will_get_back.mp3')
    resp.hangup()
    return str(resp)

@app.route('/special_request', methods=['GET', 'POST'])
def get_request():
    resp = VoiceResponse()
    logger.debug(f"special_request: {request.values}")
    if 'Digits' in request.values:
        choice = request.values['Digits']
        if choice == '1':
            resp.play(f'{public_url}/voice_notes/ask_record.mp3')
            resp.record(
                action='/got_voice_request',
                # transcribe=True, transcribe_callback='/got_transcribe_request',
                method='GET',
                max_length=20,
                finish_on_key='*'
            )
            # response.say('I did not receive a recording')
    # resp.play(f'{public_url}/voice_notes/goodbye.mp3')
    resp.hangup()
    return str(resp)
    
@app.route('/got_voice_request', methods=['GET', 'POST'])
def got_voice_request():
    resp = VoiceResponse()
    logger.debug(f"got_voice_request: {request.values}")
    to_phone = request.values['To'].replace('+','')
    table, uid, row = asyncio.run(db.get_row(phone=to_phone))
    if uid is None:
        logger.error(f"got_voice_request: Couldnt find phone: {to_phone}")
        resp.hangup()
        return str(resp)
        
    request_history=row['requests']
    request_history = f"{request_history},\nrecorded request: {request.values['RecordingUrl']}" if request_history else f"recorded request: {request.values['RecordingUrl']}"
    logger.info(f"Updating request_history for {row['name']} to: {request_history}")
    gs.update_row(phone=to_phone, timestamp=str(datetime.now()), requests=request_history)
    res = asyncio.run(db.update_row(phone=to_phone, requests=request_history))
    if not res:
        logger.error(f"Couldnt update phone: {to_phone}")
    resp.hangup()
    return str(resp)

@app.route('/got_transcribe_request', methods=['GET', 'POST'])
def got_transcribe_request():
    resp = VoiceResponse()
    logger.info(f"got_transcribe_request: {request.values}")
    return "Success"

@app.route('/endcall', methods=['GET', 'POST'])
def endcall():
    """Processes results from call"""
    logger.info(f"call ended to {request.values['To']} with status: {request.values['CallStatus']}")
    logger.debug(f"call ended to {request.values['To']}: {request.values}")
    filename = f"recordings/{request.values['To']}_{request.values['CallSid']}.wav".replace('+','')
    to_phone = request.values['To'].replace('+','')
    try:
        if request.values['CallStatus'] == 'completed':
            logger.debug(f"Downloading {request.values['RecordingUrl']} to {filename}")
            
            response = requests.get(request.values["RecordingUrl"], stream=True)
            with open(filename,'wb') as output:
                output.write(response.content)
            # logger.info(f"Result for download: {res}")
    except Exception as exp:
        logger.error(f"Couldnt download recording: {exp}")
    
    table, uid, row = asyncio.run(db.get_row(phone=to_phone))
    if uid is None:
        logger.error(f"endcall: Couldnt find phone: {to_phone}")
        history=None
    else:
        history = f"Called, {request.values['CallStatus']}, {datetime.now()}"
        history=f"{row['history']}\n{history}" if row['history'] else history
    gs.update_row(phone=request.values['To'].replace('+',''), timestamp=str(datetime.now()), status="call_" + request.values['CallStatus'], history=history)
    res = asyncio.run(db.update_row(phone=request.values['To'].replace('+',''), timestamp=str(datetime.now()), status="call_" + request.values['CallStatus'], history=history))
    if not res:
        logger.error(f"Couldnt update phone: {request.values['To']}")
    
    # res = urllib.request.urlretrieve(request.values["RecordingUrl"], filename)
    # resp = urllib3.request('GET', 'http://www.example.com/sound.mp3', preload_content=False, headers={'User-Agent': 'Customer User Agent If Needed'})
    # with open('sound.mp3', 'wb') as f:
    #     for chunk in resp.stream(65536):
    #         f.write(chunk)
    # response = requests.get(URL, stream=True)
    # with open(outfile,'wb') as output:
    #   output.write(response.content)
    
    sem.release()
    return "Success"

@app.route('/voice_notes/<path:name>', methods=['GET'])
def voice_note_send(name):
    return send_from_directory('public', name)

@app.route("/again", methods=['GET', 'POST'])
def again():
    resp = VoiceResponse()
    gather = Gather(num_digits=1, timeout=5, action='/gather')
    gather.play(f'{public_url}/voice_notes/again.mp3') #say(welcome_message) #, language='hebrew')    gather.say(posted_message) #, language='hebrew')
    resp.append(gather)
    resp.hangup()
    return str(resp)

@app.route('/voice_welcome', methods=['GET'])
def voice_welcome():
    """Respond to incoming phone calls with a menu of options"""
    # Start our TwiML response
    resp = VoiceResponse()
    gather = Gather(num_digits=1, action='/gather')
    gather.play(f'{public_url}/voice_notes/welcome.mp3') #say(welcome_message) #, language='hebrew')
    resp.append(gather)
    resp.redirect('/again')
    return str(resp)


def get_existing_number(twilio_client):
    # Use an existing number
    numbers = twilio_client.incoming_phone_numbers.list()
    phone = numbers[0] if len(numbers) > 0 else None
    return phone
    

def register_number(twilio_client, location='IL', type='local'):
    # Register a new number
    numbers = twilio_client.available_phone_numbers(location).fetch()
    numbers = numbers.local if type == 'local' else numbers.mobile
    number = numbers.list()[0]
    phone_number = number.phone_number
    phone = twilio_client.incoming_phone_numbers.create(phone_number=phone_number)
    return phone

  
def filter_df(df, priority=1, state='None', status=None, days=None):
    cond = lambda k:k['phone'] != '' and (priority is None or k['priority'] == priority) and (state is None or k['state'] == state) and (status is None or k['status'] == status) and (days is None or k['timestamp'] == '' or (datetime.now() - datetime.fromisoformat(k['timestamp'])).days > days)
    df = df[df.apply(cond, axis=1)]
    return df


def kill_process_and_children(pid: int, sig: int = 15):
    try:
        proc = psutil.Process(pid)
    except psutil.NoSuchProcess as e:
        # Maybe log something here
        return
    for child_process in proc.children(recursive=True):
        logger.info('b) Terminating child process: %s', child_process)
        child_process.send_signal(sig)
    proc.send_signal(sig)
    
def main():
    import time
    # Find your Account SID and Auth Token at twilio.com/console
    # and set the environment variables. See http://twil.io/secure
    account_sid = os.environ['TWILIO_ACCOUNT_SID']
    auth_token = os.environ['TWILIO_AUTH_TOKEN']
    client = Client(account_sid, auth_token)

    number = get_existing_number(client)
    if number is None:
        logger.info("Creating new number")
        time.sleep(5)
        number = register_number(client)
        logger.info("got new number: {}".format(number))
    # number.update(voice_url='https://wedding.yashar.us/calls/incoming')
    
    own_number = number.phone_number
    
    # Get numbers to call
    import pandas as pd
    dataframe = pd.DataFrame(gs.wks.get_all_records())
    df = filter_df(dataframe, priority=None, status='call_busy', state='remind', days=-5) #'remind'
    numbers_to_call = list(df['phone'])
    logger.info(f"Numbers to call: {numbers_to_call}")
    time.sleep(4)

    # time.sleep(60*60)
    # numbers_to_call = ['972548826569']
    
    # ToDo:
    # Call Remind + invite every day with days<0.9
    # Call no_answer / busy one hour after
    
    count_numbers_called = 0
    limit_numbers_count = -1
    force_call = True
    
    for to_number in numbers_to_call:
        # Verify we can call the number:
        table, uid, row = asyncio.run(db.get_row(phone=to_number))
        logger.debug(row)
        # sys.exit(1)
        if uid is None:
            logger.error("Cannot call: {} : {}".format(to_number, row))
            continue
        elif row['state'] not in ['remind', 'invite'] and force_call is False:
            logger.error(f"Cannot call: {to_number} because state is {row['state']}")
            continue
        elif not str(to_number).startswith('972'):
            logger.error(f"Cannot call: {to_number} because not israeli number")
            continue
            
        sem.acquire()
        logger.info("\nCalling {}".format(to_number))
        call = client.calls.create(
                                method='GET',
                                status_callback=f'{public_url}/endcall',
                                status_callback_method='POST',
                                # recording_status_callback_event=f'{public_url}/endcall',
                                record=True,
                                recording_channels='both',
                                # twiml=
                                url=f'{public_url}/voice_welcome',
                                to=to_number,
                                from_=own_number
                            )

        logger.debug(call.sid)
        count_numbers_called += 1
        if count_numbers_called == limit_numbers_count:
            logger.info("Reached limit of numbers to call")
            break
    for i in range(num_of_concurrent_calls):
        sem.acquire()
        
    logger.info("\nDone calling {} numbers. Closing app and exiting".format(count_numbers_called))
    ng.disconnect(public_url)
    for child in multiprocessing.active_children():
        print('a) Terminating', child)
        child.terminate()
        time.sleep(0.5)
    kill_process_and_children(ownpid)
    os.kill(ownpid, signal.SIGINT)
    
if __name__ == "__main__":
    # app.run(debug=True, host="0.0.0.0", port=HTTP_SERVER_PORT, threaded=True)
    thread_app = threading.Thread(target=main)
    thread_app.start(
        # threaded=True
    )
    app.run(debug=False, host='0.0.0.0', port=HTTP_SERVER_PORT, threaded=False, use_reloader=False)
    thread_app.join()
    # Close app and exit:
    
    
    # a = input("What to do?")
    # print(a)