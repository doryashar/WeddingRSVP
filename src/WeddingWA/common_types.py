from typing import List


YES_ATTENDING= "כן, אני אגיע!"
NOT_ATTENDING ="לצערי לא אגיע"
MAYBE_ATTENDING = "עוד לא הוחלט"

    # 'clicked', 
STATES = [
    'waiting', 
    'invite', 
    'answered', 
    'remind',
    # 'declined', 
    'followup-guest-num', #TODO: rename to accepted-wait-for-guest-num
    # 'followup-answered', 
    # 'followup-finish', 
    # 'not-coming-msg', 
    'day-of-wedding-message', 
    'post-wedding-message'
]

TEMPLATE_TYPES: List[str] = [
    'invite',
    'reminder',
    'accepted',
    'declined',
    'filled',
    'maybe',
    'wedding_day_declined',
    'wedding_day_accepted',
    'post_wedding',
]
BASE_URL = 'http://wedding.yashar.us'
BASE_ENC = 432523595431
LITTLE_ENC = 4324

def enc_phone(phone: str):
    return hex((int(phone) + BASE_ENC) * LITTLE_ENC)[2:]

def dec_phone(encrypted: str):
    return str(int((int(encrypted, 16) / LITTLE_ENC) - BASE_ENC))