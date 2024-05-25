import logging
import os
from fastapi import BackgroundTasks, Request, Response, Query
from fastapi.responses import RedirectResponse

from . import db_interface as db
from . import gs_interface as gs
from . import wa_interface as wa
from .message_templates import templates

from datetime import datetime
from .types import *

# =============================================================================== #

def verify_legal_send(template_id, wedding_row, invitee_row):
    if template_id == 'invite' and invitee_row['state'] != 'waiting' or invitee_row['status'] in ['read', 'delivered']:
        return "Already sent invite to {}".format(**invitee_row)
    elif template_id == 'reminder' and invitee_row['state'] not in ['invite']:
        return "Cannot send reminder to {}".format(**invitee_row)
    return None
    
def get_new_state(curr_state, curr_status, message, status):
    # if we sent a template:
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
            'wedding_day_accepted': 'post-wedding-message',
            'post_wedding': '',
        }.get(template, None)
        if res:
            return res
    return curr_state
    
def get_new_message_id(curr_state, message):
    if curr_state=='remind':
        if message == YES_ATTENDING:
            return 'accepted'
        elif message == NOT_ATTENDING:
            return 'declined'
        elif message == MAYBE_ATTENDING:
            return 'maybe'
        else:
            return None
    # else if message is digits:
    elif curr_state=='followup-guest-num' and message.isdigit():
        return 'followup-answered'
    elif curr_state=='followup-answered':
        return 'answered'
    return None
    
def convert_form_to_row(answers):
    return {
        'phone' : answers['Phone number'],
        'requests' : answers['הערות או בקשות'],
        'confirmed' : answers['מספר האורחים שיגיעו'] if answers['האם תגיעו לחתונה?'] == 'כן' else '0',
        'veggis' : answers['כמות צמחוניים\\טבעוניים'],
        'state' : 'answered',
    }
    
# =============================================================================== #

async def got_new_form_update(request: Request):
    path_params = request['path_params']
    params = request.query_params
    rj = await request.json()
    answers = {q['name']:str(q['value']).strip() for q in rj['submission']['questions']}
    answers = convert_form_to_row(answers)
    logging.debug("Received update_row req with path_params: %s, query_params: %s, json: %s", path_params, params, rj)
    await gs.update_row_with_form_answer(answers)
    if not await db.update_row(**answers):
        return Response(status_code=404, content="Error occured")
    return Response(status_code=200, content="OK")
    
async def got_new_wa_delivery(delivery_status, msg_id, phone_number, timestamp):
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
    fields['history'] = row['history'] + f"{(timestamp, msgid, message, status)}"
    
    # get the new state
    curr_state = row['state']
    curr_status = row['status']
    wedding_id = row['wedding_id']
    
    # update the row
    gs.update_row(row.get('phone'), **fields)
    res = await db.update_row(uid, **fields, tables = table)
    if not res:
        logging.error("Error updating row with incoming wa message")
        
    # send new template
    followup_messagd_id = get_new_message_id(curr_state, message)
    if followup_messagd_id:
        return await send_message_id(wedding_id, followup_messagd_id, phone_number)
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
    new_state = get_new_state(invitee_row['state'], invitee_row['status'], message_id, status)
    timestamp = str(datetime.now())
    msgid = res.id
    update_fields = {
        "history" : invitee_row['history'] + f"{(timestamp, msgid, message_id, status)}",
        "msgid"   : res.id,
        "status"  : status,
        "state"   : new_state,
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
        return Response(status_code=400, content=f"Illegal template sending: {res}")
    res = wa.messenger.send_template(**template)
    
    if res.get('error', None) != None:
        logging.error(res)
        status = "error"
        resp = Response(status_code=400, content="Error when trying to send the invite")
    else:
        logging.info(res)
        status = res['messages'][0]['message_status']
        resp = Response(status_code=200, content="Success")
    new_state = get_new_state(invitee_row['state'], invitee_row['status'], template_id, status)
    timestamp = str(datetime.now())
    msgid = res['messages'][0]['id']
    invitee_row.update({
        "history" : invitee_row['history'] + f"{(timestamp, msgid, template_id, status)}",
        "msgid"   : msgid,
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
        table, uid, row = await db.get_row(uid, tables=[db.WEDDING_TABLE]) #supabase.table(WEDDING_TABLE).select("*").eq("uid", uid).execute()
        if uid is None:
            return Response(status_code=404, content=f"Not found ({row})")
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

# =============================================================================== #

def startup():
    # ==================================================================
    ## Setting callbacks:
    # -----------------
    wa.add_delivery_handler_cb(got_new_wa_delivery)
    wa.add_message_handler_cb(got_new_wa_message)

def test():
    # Clicking from WA RSVP works - V
    # Table updates - V
    # GS updates - V
    
    # Verify we can send a message and update all the statuses upto 'read'
    # Verify we can recieve a message and update the history
    # Verify we can recieve a message from unknown and update the messages table
    
    # Send invite to a new invitee, try to send another one. expect error.
    # send invite to unknown invitee. expect error.
    # send invite to a wrong number. expect error.
    
    # Send reminder to an invitee.
    # receive text, verify that the text is in the history/notes and the state is reminded.
    # Send another reminder, expect error.
    # receive declined, verify that the state is answered and last message is delined message.
    # receive 0 -> TBD
    # receive new answer, verify that the state is waiting for number.
    # receive text, verify that the text is in the history/notes and the state is waiting for number.
    # receive number, verify that the state is answered and last message is filled message.
    # receive text, verify that the state is answered and last message is filled message and notes + history is updated.
    
    # Send reminder to an invitee.
    # receive accepted, verify that the state is waiting for number.
    # receive text, verify that the text is in the history/notes and the state is waiting for number.
    # receive number, verify that the state is answered and last message is filled message.
    # receive text, verify that the state is answered and last message is filled message and notes + history is updated.
    
    # Send reminder to an invitee.
    # receive maybe, verify that the state is reminded and sent maybe.
    # receive text, verify that the text is in the history/notes and the state is reminded.
    # receive number, verify that the text is in the history/notes and the state is reminded.
    # receive accepted, verify that the state is waiting for number.
    # receive decline, verify that the state is answered and history is declined message and sent declined message.
    # receive text, verify that the state is answered and last message is filled message and notes + history is updated.
    # receive number -> TBD
    
    # RSVP route 
    # app.add_route("/rsvp/{code}", WeddingWA.rsvp, ["GET"])
    # -> verify getting 302
    # -> verify update to clicked
    # -> verify error if not exists
    
    # app.add_route("/get_google_cal", WeddingWA.get_google_calendar, ["GET"]) #/{code}
    # -> verify getting 302
    
    # app.add_route("/", WeddingWA.wa.verify_wa_token , ["GET"])
    # app.add_route("/", WeddingWA.wa.wa_in_webhook , ["POST"])
    # app.add_route("/send-message-id/{wedding_id}/{message}/{phone_number}", WeddingWA.send_message_id , ["GET"])
    # app.add_route("/send-template-id/{wedding_id}/{template_id}/{phone_number}", WeddingWA.send_template_id , ["GET"])
    # app.add_route("/update_invitee", WeddingWA.got_new_form_update, ["POST"])
    pass