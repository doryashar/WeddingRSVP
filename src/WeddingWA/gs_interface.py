import logging, os
from fastapi import Response, Request

# ==================================================================
async def update_row_with_form_answer(answers):
    try:
        docname = "Family Reunion RSVP Form"
        sh = gc.open(docname)
        wks = sh.get_worksheet(1)
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

def connect_gspread():
        import gspread, json
        auser = json.loads(os.getenv('GSPREAD_AUTHORIZED_USER', '{}'))
        creads = json.loads(os.getenv('GSPREAD_CREDENTIALS', '{}'))
        gc, authorized_user = gspread.oauth_from_dict(creads, authorized_user_info=auser)    
        return gc
gc = connect_gspread()
import pandas as pd

# async def update_invitee_in_gsheet(request: Request):
#     path_params = request['path_params']
#     params = request.query_params
#     rj = await request.json()
#     logging.info("Received update_row req with path_params: %s, query_params: %s, json: %s", path_params, params, rj)
#     try:    
#         docname = "Family Reunion RSVP Form"
#         sh = gc.open(docname)
#         wks = sh.get_worksheet(1)
#         dataframe = pd.DataFrame(wks.get_all_records())
#         answers = {q['name']:str(q['value']).strip() for q in rj['submission']['questions']}
#         item = dataframe[dataframe['phone'].astype(str) == answers['Phone number']]
#         if len(item) != 1: 
#             raise Exception(f"phone: {answers['Phone number']} was found {len(item)} times")
#         else:
#             logging.debug(f"Found item {item} for answers: {answers}") 
            
#         loc = item.index[0]
#         dataframe.loc[loc, 'requests'] = answers['הערות או בקשות']
#         dataframe.loc[loc, 'confirmed'] = answers['מספר האורחים שיגיעו'] if answers['האם תגיעו לחתונה?'] == 'כן' else '0'
#         dataframe.loc[loc, 'veggis'] = answers['כמות צמחוניים\\טבעוניים']
#         dataframe.loc[loc, 'status'] = 'Answered'
#         # dataframe.update(item)
#         wks.update([dataframe.columns.values.tolist()] + dataframe.values.tolist())
#         logging.info(f"Done updating wks {wks}")
#     except Exception as exp:
#         logging.error(f"Exception caught in update_invitee_in_gsheet: {exp}")
#         return Response(status_code=500, content=f"{exp}")
#     return Response("Success", status_code=200)
