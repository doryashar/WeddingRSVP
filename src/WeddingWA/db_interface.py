# db_interface.py

import logging
import os, time
from datetime import datetime
from supabase import create_client, Client
  
url: str = os.environ.get("SUPABASE_URL")
key: str = os.environ.get("SUPABASE_KEY")
username: str = os.environ.get("SUPABASE_USER")
password: str = os.environ.get("SUPABASE_PASS")

supabase: Client = create_client(url, key)
session = supabase.auth.sign_in_with_password(dict(email=username, password=password))

WEDDING_TABLE = "wedding_statuses"
MESSAGES_TABLE = "whatsapp_messages" # For unknown phone
ERRORS_TABLE = "wedding_errors"

## Base Functions ##
def add_wedding(**fields):
    pass #TODO
def archive_wedding(bys, to="archived"):
    pass

def add_error(message):
    data = supabase.table(ERRORS_TABLE).insert({"timestamp": str(datetime.now()), "message": message}).execute()
    if len(data.data) == 0:
        return False
    return True

def add_message(phone, message, msgid):
    data = supabase.table(MESSAGES_TABLE).insert({"phone": phone, "msgid": msgid, "timestamp": str(datetime.now()), "message": message}).execute()
    if len(data.data) == 0:
        return False
    return True

def init_user_row(phone, wedding_id=0, **fields):
    data = supabase.table(WEDDING_TABLE).select("*").eq("phone", phone).execute() #.eq("wedding_id", wedding_id)
    if len(data.data) == 0:
        logging.info(f"init_user_row: {phone}, {wedding_id}, {fields}")
        return supabase.table(WEDDING_TABLE).insert({"phone": phone, "wedding_id": wedding_id, "state": "waiting", "timestamp": str(datetime.now()), **fields}).execute()
    else:
        return data
    
def del_user_row(phone, wedding_id=0, **fields):
    # data = supabase.table(WEDDING_TABLE).select("*").eq("phone", phone).eq("wedding_id", wedding_id).execute()
    # if len(data.data) == 0:
    #     return True
    # else:
        return supabase.table(WEDDING_TABLE).delete().eq("phone", phone).eq("wedding_id", wedding_id).execute()
    
async def get_row_by(bys, tables=[WEDDING_TABLE, MESSAGES_TABLE], allow_multi=False):
    if not isinstance(bys, list):
        bys = [bys]
    for table in tables:
        data = supabase.table(table).select("*")
        for by in bys: data = data.eq(*by)
        data = data.execute()
        if len(data.data) == 1:
            return table, data.data[0]['uid'], data.data[0]
        elif len(data.data) > 1:
            if allow_multi:
                return table, 'multi', data.data
            return table, None, f"found more than 1 results for {bys} in {table}"
    return None, None, f"no results for {bys} in {tables}"

async def update_tables_by(bys, tables=[WEDDING_TABLE, MESSAGES_TABLE], **fields):
    if not isinstance(bys, list):
        bys = [bys]
    if not isinstance(tables, list):
        tables = [tables] 
    for table in tables:
        try:
            data = supabase.table(table).update({"timestamp": str(datetime.now()), **fields})
            for by in bys:
                data = data.eq(*by)
            data = data.execute()
            if len(data.data):
                return data.data
        except Exception as exp:
            logging.error(f"trying to update table {table} by {bys} with fields: {fields} failed with exception: {exp}")
            return False
    logging.error(f'did not find {bys} in {tables}')
    supabase.table(ERRORS_TABLE).insert({"timestamp": str(datetime.now()), 'message' : f"{fields}"})
    return False
    
        
async def update_row(phone=None, wedding_id=0, uid=None, tables=[WEDDING_TABLE, MESSAGES_TABLE], **fields):
    if uid is None:
        bys = [('phone', phone)] #, ('wedding_id', wedding_id)]
    else:
        bys = [('uid', uid)]
    
    res = await update_tables_by(bys, tables=tables, **fields)
    if not res:
        #TODO: insert to errors table?
        return False
    return True
    
    
async def get_row(phone=None, wedding_id=0, uid=None, tables=[WEDDING_TABLE, MESSAGES_TABLE]):
    if uid is None:
        bys = [('phone', phone)] #, ('wedding_id', wedding_id)]
    else:
        bys = [('uid', uid)]
    return await get_row_by(bys, tables=tables)
    
 

# async def update_message_status_change(new_status, msgid, phone, timestamp):
#     update_by = [("msgid", msgid)]
#     if await update_tables_by(update_by, **{"status": new_status, "timestamp": timestamp}) is None:
#         #TODO: what about a regular message update (will be only in history)
#         logging.error(f"Error in update_status: {update_by}")
#         #TODO: insert to errors table?
#         return Response(status_code=404, content="msg not found")
    
async def get_wedding_by_id(wedding_id):
    #TODO
    return dict(
        host = "אופיר ישר וקובי ואקנין.",
        date = '20/06/2024',
        hour = '19:30',
        location = 'אולם דואאה',
        city = 'ראשון-לציון',
    )