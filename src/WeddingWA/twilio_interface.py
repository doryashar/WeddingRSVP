from fastapi.responses import Response, RedirectResponse

def incoming():
    data = """<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Dial>972-548826569</Dial>
</Response>
    """ # <Redirect>http://www.foo.com/nextInstructions</Redirect>
    return Response(content=data, media_type="application/xml")    
    # return RedirectResponse(f"https://forms.fillout.com/t/xwYB5jKk1Gus?phone={phone}&name={name}", status_code=302)

# import logging
# import asyncio
# import json
# import os, base64

# logging.basicConfig(
#     level=logging.INFO, 
#     format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
#     datefmt='%d-%b-%y %H:%M:%S',
#     handlers=[logging.FileHandler('ofir_voice.log'), logging.StreamHandler()]
#     )

# from pyngrok import ngrok as ng

# from flask import Flask, request, Response, redirect
# from flask import send_from_directory
# from flask_sock import Sock, ConnectionClosed
# from twilio.twiml.voice_response import VoiceResponse, Gather
# from twilio.rest import Client
# import threading, multiprocessing


        
# welcome_message = 'i am here, what is the magic number?' # 'שלום! אני מתקשר בקשר לחתונה של אופיר וקובי ב20 לחודש. יש להקיש כמה אנשים יגיעו. אם לא תגיעו יש להקיש 0.'
# posted_message = 'say what!?' #'המערכת לא זיהתה את תשובתכם. נא להקיש מספר ככמות האורחים אשר יגיעו לחתונה.'
# too_bad = 'too bad, goodbye' #'חבל מאוד. נתראה באירוע הבא. להתראות'
# great_goodbye= 'great! goodbye' #'נהדר! עדכנתי את המערכת. שיהיה המשך יום נעים.'

# @app.route('/gather', methods=['GET', 'POST'])
# def gather():
#     """Processes results from the <Gather> prompt in /voice"""
#     # Start our TwiML response
#     resp = VoiceResponse()
#     if 'Digits' in request.values:
#         logging.info(f"{request.values}")
#         choice = request.values['Digits']
#         if choice == '0':
#             resp.play(f'{public_url}/voice_notes/too_bad.mp3') #resp.say(too_bad) #, language='hebrew')
#             resp.hangup()
#             return str(resp)
#         else:
#             resp.play(f'{public_url}/voice_notes/great_goodbye.mp3') #resp.say(great_goodbye) #, language='hebrew')
#             resp.hangup()
#             return str(resp)
#     resp.redirect('/again')
#     return str(resp)

# @app.route('/endcall', methods=['GET', 'POST'])
# def endcall():
#     """Processes results from call"""
#     logging.info(f"{request.values}")
#     logging.info(f"{request}")
#     return "Success"

# @app.route('/voice_notes/<path:name>', methods=['GET'])
# def voice_note_send(name):
#     return send_from_directory('public', name)

# @app.route("/again", methods=['GET'])
# def again():
#     resp = VoiceResponse()
#     gather = Gather(num_digits=1, timeout=5, action='/gather')
#     gather.play(f'{public_url}/voice_notes/again.mp3') #say(welcome_message) #, language='hebrew')    gather.say(posted_message) #, language='hebrew')
#     resp.append(gather)
#     resp.redirect('/again')
#     return str(resp)

# @app.route('/voice_welcome', methods=['GET'])
# def voice_welcome():
#     """Respond to incoming phone calls with a menu of options"""
#     # Start our TwiML response
#     resp = VoiceResponse()
#     gather = Gather(num_digits=1, action='/gather')
#     gather.play(f'{public_url}/voice_notes/welcome.mp3') #say(welcome_message) #, language='hebrew')
#     resp.append(gather)
#     resp.redirect('/again')
#     return str(resp)


# def get_existing_number(twilio_client):
#     # Use an existing number
#     numbers = twilio_client.incoming_phone_numbers.list()
#     phone = numbers[0] if len(numbers) > 0 else None
#     return phone
    

# def register_number(twilio_client, location='IL', type='local'):
#     # Register a new number
#     numbers = twilio_client.available_phone_numbers(location).fetch()
#     numbers = numbers.local if type == 'local' else numbers.mobile
#     number = numbers.list()[0]
#     phone_number = number.phone_number
#     phone = twilio_client.incoming_phone_numbers.create(phone_number=phone_number)
#     return phone

  
    
# if __name__ == "__main__":
#     app = Flask(__name__)

#     HTTP_SERVER_PORT = os.environ.get("HTTP_SERVER_PORT", 5000)
#     public_url = ng.connect(HTTP_SERVER_PORT, bind_tls=True).public_url
#     threading.Thread(target=app.run, kwargs={'host': '0.0.0.0', 'port': HTTP_SERVER_PORT}).start(
#         # threaded=True
#     )
    
#     from dotenv import load_dotenv
#     import time
#     load_dotenv()
#     # Find your Account SID and Auth Token at twilio.com/console
#     # and set the environment variables. See http://twil.io/secure
#     account_sid = os.environ['TWILIO_ACCOUNT_SID']
#     auth_token = os.environ['TWILIO_AUTH_TOKEN']
#     client = Client(account_sid, auth_token)

#     number = get_existing_number(client)
#     if number is None:
#         import time
#         app.logger.info("Creating new number")
#         time.sleep(5)
#         number = register_number(client)
#         app.logger.info("got new number: {}".format(number))
    
#     phone_number = number.phone_number
#     time.sleep(300)
#     call = client.calls.create(
#                             method='GET',
#                             status_callback=f'{public_url}/endcall',
#                             status_callback_method='POST',
#                             # recording_status_callback_event=f'{public_url}/endcall',
#                             record=True,
#                             recording_channels='both',
#                             # twiml=
#                             url=f'{public_url}/voice_welcome',
#                             to='+972528343166',
#                             from_=phone_number
#                         )

#     print(call.sid)
#     # a = input("What to do?")
#     # print(a)