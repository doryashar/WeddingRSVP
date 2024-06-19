from .common_types import *
def get_invite0(phone_number, name, host, date, hour, location, city, header_image="https://i.ibb.co/HpsM474/Whats-App-Image-2024-05-18-at-22-14-04.jpg", *args, **kwargs):
    url = f'rsvp/{enc_phone(kwargs.get("uid"))}'
    return  {
        'template':'general_wedding', 
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

def get_wedding_day0(phone_number, name, host, date, hour, location, city, *args, **kwargs):
    google_directions = f'directions_google'
    waze_directions = f'directions_waze'
    gift_link = "https://payboxapp.page.link/Z9Hn4FHkw7nu44eG9" #f'https://wedding.yashar.us/gift'
    when = 'מחר'
    return  {
        'template':'wedding_day', 
        'recipient_id':phone_number, 
        'components':[
            {
                "type": "header",
                "parameters": [
                {
                    "type": "text",
                    "text": when
                }
                ] 
            },
            {"type": "body",  "parameters": [
                {"type": "text", "text": hour},
                {"type": "text", "text": f'{city} ,{location}'},
                {"type": "text", "text": host},
                {"type": "text", "text": gift_link},
                {"type": "text", "text": when},
                ]
             },
            {"type": "button", "sub_type": "url", "index": "0", "parameters": [ {"type": "text", "text": google_directions}]},
            {"type": "button", "sub_type": "url", "index": "1", "parameters": [ {"type": "text", "text": waze_directions}]},
        ],
        'lang':"he"
    }


def get_reminder0(phone_number, name, host, date, hour, location, city, *args, **kwargs):
    return  {
        'template':'wedding_reminder_1', 
        'recipient_id':phone_number, 
        'components':[
            {"type": "body",  "parameters": [
                {"type": "text", "text": host},
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
    
    'filled-0' : 'מעולה, רשמתי. לכל שינוי הערה או בקשה (למשל מנות צמחוניות) תוכלו לכתוב כאן עד יום החתונה.',
    'filled-1' : '',
    'filled-2' : '',
    
    'maybe-0' : """אין בעיה.
נשמח לעדכון בהמשך.
ניתן להשיב בצ׳אט זה עם מספר האנשים שיגיעו לחתונה.
(0 במידה לא מגיעים או מספר אחר במידה וכן)

תודה רבה """,
    'maybe-1' : '.אוקיי, כשתדעו פשוט כתבו את מספר האנשים שיגיעו או 0 אם לא תגיעו. בכל מקרה נשמח לתשובה בהקדם!',
    'not-filled-0' : 'אנא כתבו מספר בלבד',
    'updated-0' : 'עדכנתי את הכמות ל-{confirmed} מוזמנים. להערות או שינויים, כתבו לי כאן!',
    'request_added-0' : 'אוקיי, רשמתי.',
    
    'wedding_day-0' : get_wedding_day0,
    
    'wedding_day_declined-0' : '',
    
    'wedding_day_accepted-0' : '',
    'wedding_day_accepted-1' : '',
    
    'post_wedding-0' : '',
    'post_wedding-1' : '',
    'post_wedding-2' : '',
}