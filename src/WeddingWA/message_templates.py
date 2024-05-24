
def get_invite0(phone_number, name, host, date, hour, location, city, url, header_image="https://i.ibb.co/HpsM474/Whats-App-Image-2024-05-18-at-22-14-04.jpg", *args, **kwargs):
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
    
    'filled-0' : '',
    'filled-1' : '',
    'filled-2' : '',
    
    'maybe-0' : '',
    
    
    'wedding_day_declined-0' : '',
    
    'wedding_day_accepted-0' : '',
    'wedding_day_accepted-1' : '',
    
    'post_wedding-0' : '',
    'post_wedding-1' : '',
    'post_wedding-2' : '',
}