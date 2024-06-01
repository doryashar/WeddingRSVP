#!/usr/bin/env python
import requests
import logging
import gspread
import json
import pandas as pd
import re, time, os
from dotenv import load_dotenv

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
load_dotenv()

# Ofir:
def send_invite(phone_number, name):
    if phone_number == None or name == None:
        logging.error(f"Invalid invite: {phone_number}({name})")
        return 0
    try:
        res = requests.get(f"https://wedding.yashar.us/send-invite/{phone_number}/{name}")
        if res.status_code == 200:
            logging.info(f"Sent invite to {name} {phone_number}")
            return 1
        else:
            logging.error(f"Failed to send invite to {name} {phone_number}: \n{res.status_code} => {res.text}")
            return 0
    except Exception as e:
        logging.error(f"Failed to send invite to {name} {phone_number}: \n{e}")
        return 0
    
def send_reminder(phone_number):
    if phone_number == None:
        logging.error(f"Invalid invite: {phone_number}")
        return 0
    try:
        res = requests.get(f"https://wedding.yashar.us/send-template-id/0/reminder-0/{phone_number}")
        if res.status_code == 200:
            logging.info(f"Sent reminder to {phone_number}")
            return 1
        else:
            logging.error(f"Failed to send reminder to {phone_number}: \n{res.status_code} => {res.text}")
            return 0
    except Exception as e:
        logging.error(f"Failed to send reminder to {phone_number}: \n{e}")
        return 0
    
def send_invitations(list_of_invites, limit):
    k = 0
    for i, row in list_of_invites[:limit].iterrows():
        if send_invite(row['phone'], row['full name']) == 1:
            list_of_invites.loc[i, 'status'] = 'sent'
            k+=1
        else:
            list_of_invites.loc[i, 'status'] = 'error'
        time.sleep(1)
    return k

def connect_from_pc():
    with open('.creds/creds.json', 'r') as f:
        credentials = json.load(f)
    with open('.creds/authorized_user.json', 'r') as f:
        auser = json.loads(json.load(f)) # auser = json.loads(os.getenv('GSPREAD_AUTHORIZED_USER', '{}'))
    for i in range(2):
        try:
            gc, authorized_user = gspread.oauth_from_dict(credentials, authorized_user_info=auser)
            gc.list_spreadsheet_files()
            break
        # except gspread.auth.exceptions.DefaultCredentialsError:
        #     logging.info("No Google credentials found")
        # except gspread.auth.exceptions.RefreshError:
        #     logging.error("Failed to refresh credentials")
        except Exception as e:
            logging.error(f"Exception caught in gspread: ({type(e)}){e}")
        finally:
            auser = None
    
    with open('.creds/authorized_user.json', 'w') as f:
        json.dump(authorized_user, f)
    return gc

def get_list_of_invites():
    gc = connect_from_pc()
    # gc = gspread.(credentials)
    docname = "Family Reunion RSVP Form"
    sheetname = "OFIR"
    # try:
    sh = gc.open(docname)#.sheet1
    # except gspread.exceptions.SpreadsheetNotFound:
    #     sh = gc.create(docname)
    wks = sh.get_worksheet(1)
    
    # gc = gspread.service_account(
    # credentials_filename='path/to/the/credentials.json',
    # authorized_user_filename='path/to/the/authorized_user.json'
    # )

    dataframe = pd.DataFrame(wks.get_all_records())
    # dataframe = wks.get_all_records()
    # wks.update([dataframe.columns.values.tolist()] + dataframe.values.tolist())
    return dataframe, wks

def fix_phone(phone):
    phone = re.sub('[^0-9+]','', str(phone))
    if phone.startswith('05') and len(phone) == 10:
        phone = f'972{phone[1:]}'
    elif phone.startswith('5') and len(phone) == 9:
        phone = f'972{phone}'
    elif phone.startswith('+'):
        phone = phone[1:]
    return phone
        
def clean_df(df):
    # Could use apply/map, just invitees[condition], filter, query, iloc
    df['phone'] = df['phone'].apply(fix_phone) # clean_list['phone'].replace('[^0-9]','', regex=True,inplace=True)
    return df

def filter_df(df, priority=1, status='None'):
    cond = lambda k:k['phone'] != '' and (priority is None or k['priority'] == priority) and (status is None or k['status'] == status)
    df = df[df.apply(cond, axis=1)]
    return df

    

# =================================


def invite_users(
    limit = 10,
    run_priority = None,
    run_status = 'None'
    ):
    df, wks = get_list_of_invites()
    new_df = clean_df(df)
    new_df = filter_df(df, run_priority, run_status)
    logging.info(f"Sending {max(limit,len(new_df))} new invites")
    k = send_invitations(new_df, limit)
    if k:
        logging.info(f"Sent {k} invites. Saving new data")
        # df.loc[new_df.index] = new_df
        # save_wks(wks, df)
    else:
        logging.error("Sent no invites")

# =================================

def main():
    # send_invite('972524232229', 'בר')
    df, wks = get_list_of_invites()
    # send_reminder('972548826569')
    # send_reminder('972528343166')

if __name__ == '__main__':
    main()
    # update_check()
    
    
    