from .common_types import *
def get_invite0(phone_number, name, host, date, hour, location, city, url=None, header_image="https://i.ibb.co/HpsM474/Whats-App-Image-2024-05-18-at-22-14-04.jpg", *args, **kwargs):
    if url is None:
        url = f'{BASE_URL}/rsvp/{enc_phone(phone_number)}'
    return  {
        'template':'TBD', 
        'recipient_id':phone_number, 
        'components':[
            {
                "type": "header",
                "parameters": [
                {
                    "type": "image",
                    "image": {
                    "link": header_image
                    }
                }
                ] 
            },
            {"type": "body",  "parameters": [
                {"type": "text", "text": name},
                {"type": "text", "text": host},
                {"type": "text", "text": date},
                {"type": "text", "text": hour},
                {"type": "text", "text": location},
                {"type": "text", "text": city},
                ]},
            {"type": "button", "sub_type": "url", "index": "0", "parameters": [ {"type": "text", "text": url}]},
        ],
        'lang':"he"
    }

def get_reminder0(phone_number, name, host, date, hour, location, city, *args, **kwargs):
    return  {
        'template':'wedding_reminder_1', 
        'recipient_id':phone_number, 
        'components':[
            {"type": "body",  "parameters": [
                {"type": "text", "text": name},
                ]
             },
        ],
        'lang':"he"
    }

templates = {
    'invite-0' : get_invite0,
    
    'reminder-0' : get_reminder0,
    'reminder-1' : '',
    'reminder-2' : '',
    
    'accepted-0' : 'איזה כיף! כמה תהיו?',
    'accepted-1' : '',
    'accepted-2' : '',
    
    'declined-0' : 'חבל... נשמח לחגוג אתכם בעתיד. אם תתחרטו תוכלו פשוט לכתוב את מספר האנשים שיגיעו',
    'declined-1' : '',
    'declined-2' : '',
    
    'filled-0' : 'מעולה, רשמתי. לכל שינוי הערה או בקשה (למשל מנות צמחוניות) תוכלו לכתוב כאן עד יום החתונה. נתראה שם!',
    'filled-1' : '',
    'filled-2' : '',
    
    'maybe-0' : '.אוקיי, כשתדעו פשוט תכתוב את המספר האנשים שיגיעו או 0 אם לא תגיעו. בכל מקרה נשמח לתשובה בהקדם!',
    
    'updated-0' : 'עדכנתי את הכמות ל-{} מוזמנים. להערות או שינויים, כתבו לי כאן!',
    'request_added-0' : 'אוקיי, רשמתי.',
    
    'wedding_day_declined-0' : '',
    
    'wedding_day_accepted-0' : '',
    'wedding_day_accepted-1' : '',
    
    'post_wedding-0' : '',
    'post_wedding-1' : '',
    'post_wedding-2' : '',
}