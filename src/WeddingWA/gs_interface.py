import logging, os
from fastapi import Response, Request

# ==================================================================
async def update_row_with_form_answer(fields):
    answers = fields.copy()
    logging.info(f"Updating spreadsheet {docname} with {answers}") 
    phone = answers.pop('phone', None)
    return update_row(phone, **answers)
        
# ==================================================================

def save_wks(wks, df):
    df = df.fillna('') #To fix: Out of range float values are not JSON compliant
    wks.update([df.columns.values.tolist()] + df.values.tolist())

def insert_row(phone, name, **fields):
    pass #TODO: fill

def update_row(phone, **fields):
    try:
        dataframe = pd.DataFrame(wks.get_all_records())
        item = dataframe[dataframe['phone'].astype(str) == str(phone)]
        if len(item) != 1: 
            raise Exception(f"phone: {phone} was found {len(item)} times")
        else:
            logging.debug(f"Found item {item} for answers: {fields}") 
        
        loc = item.index[0]
        for a,b in fields.items():
            if b:
                dataframe.loc[loc, a] = b 
        # dataframe.update(item)
        save_wks(wks, dataframe)
        logging.info(f"Done updating wks {wks}")
    except Exception as exp:
        logging.error(f"Exception caught in update_row_with_form_answer: {exp}")
        return Response(status_code=500, content=f"{exp}")
    return Response("Success", status_code=200)

def connect_gspread():
        import gspread, json
        auser = os.getenv('GSPREAD_AUTHORIZED_USER', None)
        auser = json.loads(auser) if auser else None
        creds = json.loads(os.getenv('GSPREAD_CREDENTIALS', '{}'))
        logging.info(f"Trying to connect with creds: {creds}, auser: {auser}")
        gc, authorized_user = gspread.oauth_from_dict(creds, authorized_user_info=auser)    
        logging.info(f"Authorized user is: {authorized_user}")
        return gc

gc = connect_gspread()
import pandas as pd

docname = "Family Reunion RSVP Form"
sh = gc.open(docname)
wks = sh.get_worksheet(1)
