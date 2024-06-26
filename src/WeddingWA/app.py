import logging
import os
from fastapi import BackgroundTasks, Request, Response, Query
from fastapi.responses import RedirectResponse

from . import db_interface as db
from . import gs_interface as gs
from . import wa_interface as wa
from . import twilio_interface as calls
from .message_templates import templates

from datetime import datetime
from .common_types import *

# from pyngrok import ngrok as ng
# HTTP_SERVER_PORT = 80
# public_url = ng.connect(HTTP_SERVER_PORT, bind_tls=True).public_url
# logging.info(f"Listening for connections on port {HTTP_SERVER_PORT} URL: {public_url}")
# =============================================================================== #

def verify_legal_send(template, wedding_row, invitee_row):
    template_id = template.split('-')[0]
    if invitee_row['phone'] is None:
        return "Cannot send invite to null phone: {}".format(invitee_row)
    elif template_id == 'invite' and invitee_row['state'] != 'waiting' and invitee_row['status'] in ['read', 'delivered']:
        return "Already sent invite to {}".format(invitee_row)
    elif template_id == 'reminder': 
        # if invitee_row['state'] in ['answered']:
        #     return f"Cannot send reminder to {invitee_row} (already answered)" #But not confirmed
        if invitee_row['confirmed'] is not None and invitee_row['confirmed'].isdigit() and invitee_row['confirmed'] != '0':
            return f"Cannot send reminder to {invitee_row}"
        elif invitee_row['state'] in ['remind', 'invite']:
            if invitee_row['status'] not in ['read', 'delivered', 'sent', 'accepted']:
                pass
            elif invitee_row['timestamp'] and (datetime.now() - datetime.fromisoformat(invitee_row['timestamp'])).seconds < ONE_HOUR_IN_SECONDS:
                return f"Too soon- Cannot send reminder to {invitee_row}"
        elif invitee_row['state'] not in ['invite', 'sent']: #TODO: remove the sent
            return f"Cannot send reminder to {invitee_row}"
    # elif template_id == 'wedding_day':
        # if invitee_row['state'] not in ['answered']:
        #     return f"Wedding day message only for answered invitee: {invitee_row}"
        # if invitee_row['confirmed']
    return None
    
def get_new_state(curr_row, message, status):
    # if we sent a template:
    curr_state, curr_status = curr_row['state'], curr_row['status']
    if status != 'received' and message in templates:
        template = message.split('-')[0]
        # state_from_sent_template_id
        res = {
            'invite':   'invite',
            'reminder': 'remind',
            'accepted': 'followup-guest-num',
            'maybe':  'remind',
            'filled': 'answered',
            'any_other': 'answered',
            'declined': 'answered',
            'wedding_day_declined': 'day-of-wedding-message',
            'wedding_day': 'wedding_day',
            'post-wedding-message': 'wedding_day',
            'post_wedding': 'post_wedding',
        }.get(template, None)
        if res:
            return res
    return curr_state
    
def get_new_message_id(row, message):
    curr_state = row['state']
    # if curr_state=='remind':
    if message == YES_ATTENDING:
        return 'accepted'
    elif message == NOT_ATTENDING and not (row['state'] == 'answered' and row['confirmed'] == '0'):
        return 'declined'
    elif message == MAYBE_ATTENDING:
        return 'maybe'
    # else:
    #     return None
        
    # else if message is digits:
    elif curr_state in ['followup-guest-num', 'remind', 'invite'] and message.isdigit(): #
        return 'filled'
    elif curr_state in ['followup-guest-num'] and not message.isdigit():
        return 'not-filled'
    elif curr_state in ['answered'] and message.isdigit():
        return 'updated'
    elif curr_state in ['answered']:
        return 'request_added'
    
    # elif curr_state=='followup-answered':
    #     return 'filled'
    return None
    
def convert_form_to_row(answers):
    return {
        'phone' : answers['Phone number'],
        'requests' : answers['הערות או בקשות'],
        'confirmed' : answers['מספר האורחים שיגיעו'] if answers['האם תגיעו לחתונה?'] == 'כן' else '0',
        'veggis' : answers['כמות צמחוניים\\טבעוניים'],
        'state' : 'answered',
    }
    
def update_fields(fields, message, curr_row): 
    # For incoming messages
    if  message == NOT_ATTENDING: #curr_state in ['invite', 'remind'] and
        # fields['state'] = 'answered'
        fields['confirmed'] = '0'
    elif message == YES_ATTENDING and curr_row['confirmed'] == '0':
        fields['confirmed'] = ''
    elif curr_row['state'] in ['invite', 'remind', 'followup-guest-num', 'answered'] and message.isdigit(): #message == YES_ATTENDING:
        fields['confirmed'] = message
    
    if curr_row['state'] in ['invite', 'remind', 'followup-guest-num', 'answered', 'post-wedding-message', 'wedding_day'] and not message.isdigit() and message not in [YES_ATTENDING, NOT_ATTENDING, MAYBE_ATTENDING]:
        fields['requests'] = curr_row['requests'] + '\n' + message if curr_row['requests'] else message
                
# =============================================================================== #

async def got_new_form_update(request: Request):
    path_params = request['path_params']
    params = request.query_params
    rj = await request.json()
    answers = {q['name']:str(q['value']).strip() for q in rj['submission']['questions']}
    answers = convert_form_to_row(answers)
    logging.info("Received update_row req with path_params: %s, query_params: %s, json: %s", path_params, params, rj)
    await gs.update_row_with_form_answer(answers)
    if not await db.update_row(**answers, tables=db.WEDDING_TABLE):
        return Response(status_code=404, content="Error occured")
    return Response(status_code=200, content="OK")
    
async def got_new_wa_delivery(delivery_status, msg_id, phone_number, timestamp):
    timestamp = str(datetime.now()) #TODO: remove
    bys = [("phone", phone_number), ("msgid", msg_id)]
    table, uid, row = await db.get_row_by(bys)
    if uid is None:
        errmsg = f"Got delivery status {delivery_status} from unknown phone: {phone_number} with msgid: {msg_id} ({row})"
        logging.error(errmsg)
        db.add_error(errmsg)
        return Response(status_code=500, content="Error occured")
    logging.info(f"Got delivery status {delivery_status} from phone: {phone_number} with msgid: {msg_id}")
    if not await db.update_row(tables=table, uid=uid, timestamp=timestamp, status=delivery_status):
        errmsg = f"Could not update db with delivery status {delivery_status} from phone: {phone_number} with msgid: {msg_id}"
        logging.error(errmsg)
        db.add_error(errmsg)
        return Response(status_code=500, content="Error occured")
    return Response(status_code=200, content="OK")
    
async def got_new_wa_message(msgid, phone_number, status="received", message=None, from_name=None, *arg, **kwargs):
    # get the row
    table, uid, row = await db.get_row(phone_number, tables=[db.WEDDING_TABLE])
    timestamp = str(datetime.now())
    if uid is None:
        db.add_message(phone_number, message, msgid)
        logging.info(f"Got message from unknown phone: {phone_number} ({row})")
        return Response(status_code=200, content="OK")
        
    fields = dict()
    # add to history
    fields['history'] = row['history'] + f"{(timestamp, msgid, message, status)}" if row['history'] else f"{(timestamp, msgid, message, status)}"
    
    # get the new fields
    curr_state = row['state']
    curr_status = row['status']
    wedding_id = row['wedding_id']
    update_fields(fields, message, row)
    
    # update the row
    gs.update_row(row.get('phone'), **fields)
    logging.debug(f"Updating db uid= {uid}, tables= {table}, fields= {fields}")
    res = await db.update_row(uid=uid, **fields, tables=table)
    if not res:
        logging.error("Error updating row with incoming wa message")
        
    # send new template
    followup_messagd_id = get_new_message_id(row, message)
    logging.info(f"Sending followup_messagd_id: {followup_messagd_id}")
    if followup_messagd_id:
        return await send_message_id(wedding_id, followup_messagd_id + '-0', phone_number)
    return Response(status_code=200, content="OK")

# =============================================================================== #
    

#TODO: merge send_message_id + send_template_id
# app.add_route("/send-message-id/{wedding_id}/{message}/{phone_number}", WeddingWA.send_message , ["GET"])
async def send_message_id(wedding_id, message_id, phone_number): 
    #get message by id, wedding by id and create a message
    wedding_row = await db.get_wedding_by_id(wedding_id) 
    _,uid, invitee_row = await db.get_row(phone_number, wedding_id=wedding_id, tables=[db.WEDDING_TABLE]) 
    if uid is None:
        return Response(status_code=404, content=f"Not found {uid}")
    message = templates.get(message_id, message_id).format(**wedding_row, **invitee_row)
    res = await wa.send_message(phone_number, message)
    status = "accepted" if res.status_code == 200 else "failed" #TODO: res['messages'][0]['message_status']?
    new_state = get_new_state(invitee_row, message_id, status)
    timestamp = str(datetime.now())
    msgid = res.id
    update_fields = {
        "history" : invitee_row['history'] + f"{(timestamp, msgid, message_id, status)}",
        "msgid"   : res.id,
        "message" : message_id,
        "status"  : status,
        "state"   : new_state,
        "timestamp": timestamp
    }
    invitee_row.update(update_fields)
    await db.update_row(**invitee_row)
    gs.update_row(**invitee_row)
    return res

# =============================================================================== #
    
# app.add_route("/send-message/{phone_number}/{message}", WeddingWA.send_message , ["GET"])
async def send_message(message, phone_number): 
    #get message by id, wedding by id and create a message
    _,uid, invitee_row = await db.get_row(phone_number, tables=[db.WEDDING_TABLE]) 
    if uid is None:
        return Response(status_code=404, content=f"Not found {uid}")
    res = await wa.send_message(phone_number, message)
    logging.info(f"Got response for send_message: {res}")
    status = "accepted" if res.status_code == 200 else "failed" #TODO: res['messages'][0]['message_status']?
    timestamp = str(datetime.now())
    update_fields = {
        "history" : invitee_row['history'] + f"{(timestamp, message, status)}",
        "timestamp": timestamp
    }
    invitee_row.update(update_fields)
    await db.update_row(**invitee_row)
    gs.update_row(**invitee_row)
    return res

# app.add_route("/send-template-id/{wedding_id}/{template_id}/{phone_number}", WeddingWA.send_template , ["GET"])
async def send_template_id(wedding_id, template_id, phone_number): 
    wedding_row = await db.get_wedding_by_id(wedding_id) 
    _,uid, invitee_row = await db.get_row(phone_number, wedding_id=wedding_id, tables=[db.WEDDING_TABLE]) 
    if uid is None:
        return Response(status_code=404, content=f"Not found {uid}")
    template = templates.get(template_id)(phone_number=phone_number, **wedding_row, **invitee_row)
    res = verify_legal_send(template_id, wedding_row, invitee_row)
    if res:
        #TODO: update in errors table
        return Response(status_code=400, content=f"Illegal condition for template sending: {res}")
    res = wa.messenger.send_template(**template)
    
    if res.get('error', None) != None:
        logging.error(res)
        status = "error"
        msgid = res['error']
        resp = Response(status_code=400, content="Error when trying to send the invite")
    else:
        logging.info(res)
        status = res['messages'][0]['message_status']
        msgid = res['messages'][0]['id']
        resp = Response(status_code=200, content="Success")
    new_state = get_new_state(invitee_row, template_id, status)
    timestamp = str(datetime.now())
    new_history = invitee_row['history'] + f"{(timestamp, msgid, template_id, status)}" if invitee_row['history'] else f"{(timestamp, msgid, template_id, status)}"
    invitee_row.update({
        "history" : new_history,
        "msgid"   : msgid,
        "message" : template_id,
        "status"  : status,
        "state"   : new_state,
        "timestamp": timestamp
    })
    gs.update_row(**invitee_row)
    await db.update_row(**invitee_row) # await update_tables_by(by=("uid", uid), status=state, id=res['messages'][0]['id'], phone=phone_number)
    return resp

# =============================================================================== #
    

# app.add_route("/rsvp/{code}", WeddingWA.rsvp, ["GET"])
#TODO: get sepcific rsvp per wedding
async def rsvp(request: Request):
    code = request['path_params']['code']
    logging.info("Received rsvp req: %s", code)
    uid = dec_phone(code)
    try:
        tables = [db.WEDDING_TABLE] #["messages"] if int(uid) < 477 else [db.WEDDING_TABLE]
        table, uid, row = await db.get_row(uid=uid, tables=tables) #supabase.table(WEDDING_TABLE).select("*").eq("uid", uid).execute()
        if uid is None:
            logging.error("Error getting rsvp for code=%s uid=%s, row=%s", code, uid, row)
            return Response(status_code=404, content=f"Not found")
        phone = row.get('phone')
        name = row.get('name')
        status = row.get('status')
        logging.info("%s %s was %s and now clicked", phone, name, status)
        gs.update_row(phone=phone, clicked=True)
        res = await db.update_row(wedding_id=0, uid=uid, tables=table, clicked=True) #  data = supabase.table(WEDDING_TABLE).update({"status": "clicked", "timestamp": str(time.time())}).eq("uid", uid).execute()
        if not res:
            errmsg = f"Error updating rsvp for code={code} uid={uid}"
            db.add_error(errmsg)
            logging.error(errmsg)
    except Exception as exp:
        errmsg = f"Exception caught in rsvp: {exp}"
        db.add_error(errmsg)
        logging.error(errmsg)
        return Response(status_code=500, content=exp)
    return RedirectResponse(f"https://forms.fillout.com/t/xwYB5jKk1Gus?phone={phone}&name={name}", status_code=302)

# =============================================================================== #

# app.add_route("/get_google_cal", WeddingWA.get_google_calendar, ["GET"]) #/{code}
async def get_google_calendar(request: Request):
    #TODO: get sepcific invite per wedding
    # code = request['path_params']['code']
    url = "https://calendar.google.com/calendar/event?action=TEMPLATE&tmeid=N2I4MmxmcG11aWNhdXI2ZWZwZnAwa3JiZGMgZDAzY2Y2Y2NjZDU5YTYzMGQ4NTQ0YTBkY2RjOTIwODA4NWM0MzQyN2IxNTU0Nzk1YTQwYTZkMzZmM2JlOTY4Y0Bn&tmsrc=d03cf6cccd59a630d8544a0dcdc9208085c43427b1554795a40a6d36f3be968c%40group.calendar.google.com"
    return RedirectResponse(url, status_code=302)

async def get_google_directions(request: Request):
    url = 'https://maps.app.goo.gl/brP6eifxmW6i9roB7' #"https://maps.app.goo.gl/9y8sgUUzNFgCapZk8" #
    return RedirectResponse(url, status_code=302)

async def get_waze_directions(request: Request):
    url = "https://www.waze.com/en/live-map/directions/il/center-district/%D7%A8%D7%90%D7%A9%D7%9C%D7%A6/duee-events-by-lago?place=ChIJm9qNsqmzAhURJysHnbI4yR0" #"https://waze.com/ul/hsv8tytzd0"
    return RedirectResponse(url, status_code=302)

async def get_gift(request: Request):
    url = "https://payboxapp.page.link/Z9Hn4FHkw7nu44eG9"
    return RedirectResponse(url, status_code=302)



# app.add_route("/send-invites/{phone_number}/{name}", WeddingWA.send_invite, ["GET"])
async def send_invite(phone_number, name):
    if phone_number == None or name == None:
        logging.error(f"Invalid invite: {phone_number}({name})")
        return Response(status_code=400, content="Invalid phone number")
    # TODO: clean phone number
    wedding_id = 0
    template_id = 'invite-0'
    gs.insert_row(phone_number, name)
    db.init_user_row(phone_number, wedding_id=wedding_id, name=name)
    return await send_template_id(wedding_id, template_id, phone_number)

async def send_wedding_day(phone_number):
    if phone_number == None:
        logging.error(f"Invalid phone: {phone_number}")
        return Response(status_code=400, content="Invalid phone number")
    # TODO: clean phone number
    wedding_id = 0
    template_id = 'wedding_day-0'
    return await send_template_id(wedding_id, template_id, phone_number)

# =============================================================================== #

def startup():
    # ==================================================================
    ## Setting callbacks:
    # -----------------
    wa.add_delivery_handler_cb(got_new_wa_delivery)
    wa.add_message_handler_cb(got_new_wa_message)

# try:
#     pass

# except KeyboardInterrupt:
#     import traceback, sys
#     print(traceback.format_exc())
#     print(sys.exc_info()[2])
#     print("Clean exit....")
#     sys.exit(0)