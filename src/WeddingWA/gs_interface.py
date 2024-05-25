import logging, os
from fastapi import Response, Request

# ==================================================================
async def update_row_with_form_answer(answers):
    try:
        logging.info(f"Updating spreadsheet {docname} with {answers}") 
        
        dataframe = pd.DataFrame(wks.get_all_records())
        item = dataframe[dataframe['phone'].astype(str) == answers['phone']]
        if len(item) != 1: 
            raise Exception(f"phone: {answers['phone']} was found {len(item)} times")
        else:
            logging.debug(f"Found item {item} for answers: {answers}") 
        
        loc = item.index[0]
        for a,b in answers.items():
            dataframe.loc[loc, a] = b
        # dataframe.update(item)
        wks.update([dataframe.columns.values.tolist()] + dataframe.values.tolist())
        logging.info(f"Done updating wks {wks}")
    except Exception as exp:
        logging.error(f"Exception caught in update_row_with_form_answer: {exp}")
        return Response(status_code=500, content=f"{exp}")
    return Response("Success", status_code=200)

# ==================================================================

def save_wks(wks, df):
    wks.update([df.columns.values.tolist()] + df.values.tolist())
        
def update_row(phone, **fields):
    pass

def connect_gspread():
        import gspread, json
        auser = json.loads(os.getenv('GSPREAD_AUTHORIZED_USER', '{}'))
        creads = json.loads(os.getenv('GSPREAD_CREDENTIALS', '{}'))
        gc, authorized_user = gspread.oauth_from_dict(creads, authorized_user_info=auser)    
        return gc

gc = connect_gspread()
import pandas as pd

docname = "Family Reunion RSVP Form"
sh = gc.open(docname)
wks = sh.get_worksheet(1)
