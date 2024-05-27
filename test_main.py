import logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
# from dotenv import load_dotenv
# load_dotenv()
import pytest
from fastapi.testclient import TestClient
from main import app
from main import WeddingWA
import random, string
from time import time
client = TestClient(app)
class AttrDict(dict):
    def __getattr__(self, key):
        return self[key]

    def __setattr__(self, key, value):
        self[key] = value
        
async def fake_send_read_receipt(data):
    return True
def fake_send_message(message ,phone_number):
    item = AttrDict(status_code=200, messages = [{'id': 'TEST', 'message_status' : 'accepted'}])
    logging.error(f"Sending {message} to {phone_number}")
    return item
WeddingWA.wa.send_read_receipt = fake_send_read_receipt
WeddingWA.wa.messenger.send_message = fake_send_message
WeddingWA.wa.messenger.send_template = lambda template, recipient_id, *args, **kwargs: fake_send_message(template, recipient_id)

wedding_id = 0

def fake_receive_message(phone, message):
    id = str(random.randint(1000000000,9999999999))
    msgid = ''.join([random.choice(string.ascii_letters) for i in range(20)])
    timestamp = time()
    received_message = {'object': 'whatsapp_business_account', 'entry': [{'id': str(id), 'changes': [{'value': {'messaging_product': 'whatsapp', 'metadata': {'display_phone_number': '972559569965', 'phone_number_id': '101369269635426'}, 'contacts': [{'profile': {'name': 'Dor'}, 'wa_id': phone}], 'messages': [{'from': phone, 'id': msgid, 'timestamp': timestamp, 'text': {'body': message}, 'type': 'text'}]}, 'field': 'messages'}]}]}
    return received_message, msgid

# async def test_send_template(template_id = 'reminder-0'):
#     """ 
#     - Verify we can send a template and update all the statuses upto 'read' 
#     """    
#     response = client.get(f"/send-template-id/{wedding_id}/{template_id}/{phone_number}") #, headers={"X-Token": "coneofsilence"})
#     assert response.status_code == 200
    #TODO: verify it was updated in db and in gs
    
#     # assert response.json() == {
#     #     "id": "foo",
#     #     "title": "Foo",
#     #     "description": "There goes my hero",
#     # }
    
# @pytest.mark.asyncio
# async def test_send_message():
#     table, uid, row = await WeddingWA.db.get_row(phone=phone_number)
#     assert message == row.get('message')
#     assert msgid == row.get('msgid')
    
@pytest.mark.asyncio
async def test_receive_message(message=None):
    """
    - Verify we can recieve a message and update the history
    """
    phone_number = '972548826569'
    if message is None:
        message = ''.join([random.choice(string.ascii_letters) for i in range(10)])
    received_message, msgid = fake_receive_message(phone_number, message)
    response = client.post('/', json=received_message)
    assert response.status_code == 200
    table, uid, row = await WeddingWA.db.get_row(phone=phone_number)
    history = row.get('history')
    assert msgid in history
    assert message in history
    #TODO: verify in gs
    return received_message, msgid
    
@pytest.mark.asyncio
async def test_receive_unknown_message():
    """
    - Verify we can recieve a message from unknown and update the messages table
    """
    message = 'TEST' + ''.join([random.choice(string.ascii_letters) for i in range(10)])
    phone_number = str(random.randrange(0,9999999999))
    received_message, msgid = fake_receive_message(phone_number, message)
    response = client.post('/', json=received_message)
    assert response.status_code == 200
    table, uid, row = await WeddingWA.db.get_row_by(bys=('phone',phone_number), allow_multi=True)
    
    assert uid != None
    assert table == WeddingWA.db.MESSAGES_TABLE
    if uid == 'multi':
        assert any([message in r.values() for r in row])
    else:
        assert message in row.values()
    #TODO: verify in gs

@pytest.mark.asyncio
async def test_reminder_flows():
    template_id = 'reminder-0'
    phone_number = '972548826569'
    
    # first, reset the user state and history to invite:
    res = await WeddingWA.db.update_row(phone=phone_number, state='invite', requests='', history='',tables=[WeddingWA.db.WEDDING_TABLE])
    assert res is True
    
    # Send reminder to an invitee.
    response = client.get(f"/send-template-id/{wedding_id}/{template_id}/{phone_number}") #, headers={"X-Token": "coneofsilence"})
    assert response.status_code == 200
    # await test_send_template(template_id='reminder-0')

    # receive text, verify that the text is in the history/requests and the state is reminded.
    received_message, msgid = await test_receive_message()
    table, uid, row = await WeddingWA.db.get_row(phone=phone_number)
    #TODO: assert received_message in row['requests']
    assert row['state'] == 'remind'
    
    # Send another reminder, expect error.
    response = client.get(f"/send-template-id/{wedding_id}/{template_id}/{phone_number}") #, headers={"X-Token": "coneofsilence"})
    assert response.status_code != 200
    
    # receive declined, verify that the state is answered and last message is delined message.
    received_message, msgid = fake_receive_message(phone_number, WeddingWA.NOT_ATTENDING)
    response = client.post('/', json=received_message)
    table, uid, row = await WeddingWA.db.get_row(phone=phone_number)
    assert row['state'] == 'answered'
    assert WeddingWA.NOT_ATTENDING in row['history'] #TODO: maybe the last message in history?
    assert row['confirmed'] == '0'
    
    # receive 0 -> not changing (TODO: verify not changing if same value entered / message "updated")
    received_message, msgid = fake_receive_message(phone_number, WeddingWA.NOT_ATTENDING)
    response = client.post('/', json=received_message)
    table, uid, row = await WeddingWA.db.get_row(phone=phone_number)
    assert row['state'] == 'answered'
    assert "0" in row['history'] #TODO: maybe the last message in history?
    assert row['confirmed'] == '0'
    
    # receive new answer, verify that the state is waiting for number.
    received_message, msgid = fake_receive_message(phone_number, WeddingWA.YES_ATTENDING)
    response = client.post('/', json=received_message)
    table, uid, row = await WeddingWA.db.get_row(phone=phone_number)
    assert row['state'] == 'followup-guest-num'
    assert WeddingWA.YES_ATTENDING in row['history'] #TODO: maybe the last message in history?
    assert row['confirmed'] == '' 
    
    # receive text, verify that the text is in the history/requests and the state is waiting for number.
    message = "BALBLA"
    received_message, msgid = fake_receive_message(phone_number, message)
    response = client.post('/', json=received_message)
    table, uid, row = await WeddingWA.db.get_row(phone=phone_number)
    assert row['state'] == 'followup-guest-num'
    assert message in row['history']
    assert message in row['requests']
    assert row['confirmed'] == ''
    
    # receive number, verify that the state is answered and last message is filled message.
    message = "4"
    received_message, msgid = fake_receive_message(phone_number, message)
    response = client.post('/', json=received_message)
    table, uid, row = await WeddingWA.db.get_row(phone=phone_number)
    assert row['state'] == 'answered'
    assert message in row['history']
    assert row['confirmed'] == message
    
    # receive text, verify that the state is answered and last message is filled message and requests + history is updated.
    text = "BALBLA"
    received_message, msgid = fake_receive_message(phone_number, text)
    response = client.post('/', json=received_message)
    table, uid, row = await WeddingWA.db.get_row(phone=phone_number)
    assert row['state'] == 'answered'
    assert text in row['history']
    assert text in row['requests']
    assert row['confirmed'] == message
    
@pytest.mark.asyncio
async def test_reminder_flows_1():
    template_id = 'reminder-0'
    phone_number = '972548826568'
    #Add the row:
    res = WeddingWA.db.init_user_row(phone=phone_number, state='invite')
    assert len(res.data) == 1
    
    # first, reset the user state and history to invite:
    res = await WeddingWA.db.update_row(phone=phone_number, confirmed='', state='invite', requests='', history='',tables=[WeddingWA.db.WEDDING_TABLE])
    assert res is True
    
    # Send reminder to an invitee.
    response = client.get(f"/send-template-id/{wedding_id}/{template_id}/{phone_number}") #, headers={"X-Token": "coneofsilence"})
    assert response.status_code == 200
    
    # receive accepted, verify that the state is waiting for number.
    received_message, msgid = fake_receive_message(phone_number, WeddingWA.YES_ATTENDING)
    response = client.post('/', json=received_message)
    table, uid, row = await WeddingWA.db.get_row(phone=phone_number)
    assert row['state'] == 'followup-guest-num'
    assert WeddingWA.YES_ATTENDING in row['history']
    assert row['confirmed'] in ['', None] 
    
    # receive text, verify that the text is in the history/requests and the state is waiting for number.
    message_1 = "RANDOM" + ''.join([random.choice(string.ascii_letters) for i in range(10)])
    received_message, msgid = fake_receive_message(phone_number, message_1)
    response = client.post('/', json=received_message)
    table, uid, row = await WeddingWA.db.get_row(phone=phone_number)
    assert row['state'] == 'followup-guest-num'
    assert message_1 in row['history']
    assert message_1 in row['requests']
    assert row['confirmed'] in ['', None] 
    
    # receive number, verify that the state is answered and last message is filled message.
    conf = str(random.randint(0,10))
    received_message, msgid = fake_receive_message(phone_number, conf)
    response = client.post('/', json=received_message)
    table, uid, row = await WeddingWA.db.get_row(phone=phone_number)
    assert row['state'] == 'answered'
    assert conf in row['history']
    assert conf not in row['requests'].split('\n')[-1]
    assert row['confirmed'] == conf
    
    # receive text, verify that the state is answered and last message is filled message and requests + history is updated.
    message_2 = "RANDOM" + ''.join([random.choice(string.ascii_letters) for i in range(10)])
    received_message, msgid = fake_receive_message(phone_number, message_2)
    response = client.post('/', json=received_message)
    table, uid, row = await WeddingWA.db.get_row(phone=phone_number)
    assert row['state'] == 'answered'
    assert message_2 in row['history'] and message_1 in row['history']
    assert message_2 in row['requests'] and message_1 in row['requests']
    assert row['confirmed'] == conf
    
    #delete the row
    res = WeddingWA.db.del_user_row(phone=phone_number)
    assert len(res.data)
    
@pytest.mark.asyncio
async def test_reminder_flows_2():
    template_id = 'reminder-0'
    phone_number = '972548826567'
    
    res = WeddingWA.db.init_user_row(phone=phone_number, state='invite')
    assert len(res.data) == 1
    
    # first, reset the user state and history to invite:
    res = await WeddingWA.db.update_row(phone=phone_number, state='invite', requests='', history='',tables=[WeddingWA.db.WEDDING_TABLE])
    assert res is True
    
    # Send reminder to an invitee.
    response = client.get(f"/send-template-id/{wedding_id}/{template_id}/{phone_number}") #, headers={"X-Token": "coneofsilence"})
    assert response.status_code == 200
    
    # receive maybe, verify that the state is reminded and sent maybe.
    received_message, msgid = fake_receive_message(phone_number, WeddingWA.MAYBE_ATTENDING)
    response = client.post('/', json=received_message)
    table, uid, row = await WeddingWA.db.get_row(phone=phone_number)
    assert row['state'] == 'remind'
    assert WeddingWA.MAYBE_ATTENDING in row['history']
    assert 'אוקיי, כשתדעו פשוט תכתוב את המספר האנשים שיגיעו או 0 אם לא תגיעו. בכל מקרה נשמח לתשובה בהקדם!' in row['history']
    assert row['message'] == 'maybe-0'
    assert row['confirmed'] in ['', None] 
    
    # receive text, verify that the text is in the history/requests and the state is reminded.
    message_2 = "RANDOM" + ''.join([random.choice(string.ascii_letters) for i in range(10)])
    received_message, msgid = fake_receive_message(phone_number, message_2)
    response = client.post('/', json=received_message)
    table, uid, row = await WeddingWA.db.get_row(phone=phone_number)
    assert row['state'] == 'remind'
    assert message_2 in row['history'] and WeddingWA.MAYBE_ATTENDING in row['history']
    assert message_2 in row['requests']
    
    # receive number, verify that the text is in the history/requests and the state is answered.
    conf = str(random.randint(0,10))
    received_message, msgid = fake_receive_message(phone_number, conf)
    response = client.post('/', json=received_message)
    table, uid, row = await WeddingWA.db.get_row(phone=phone_number)
    assert row['state'] == 'answered'
    assert conf in row['history']
    assert conf not in row['requests'].split('\n')[-1]
    assert row['confirmed'] == conf
    
    # receive accepted, verify that the state is waiting for number.
    # receive decline, verify that the state is answered and history is declined message and sent declined message.
    # receive text, verify that the state is answered and last message is filled message and requests + history is updated.
    # receive number -> TBD
    
    #delete the row
    res = WeddingWA.db.del_user_row(phone=phone_number)
    assert len(res.data)
    
def test():
    # Clicking from WA RSVP works - V
    # Table updates - V
    # GS updates - V
    # Send message and verify it is in history and statuses are updated up until read
    
    # Send invite to a new invitee, try to send another one. expect error.
    # send invite to unknown invitee. expect error.
    # send invite to a wrong number. expect error.
    

    
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

"""
def test_read_item_bad_token():
    response = client.get("/items/foo", headers={"X-Token": "hailhydra"})
    assert response.status_code == 400
    assert response.json() == {"detail": "Invalid X-Token header"}


def test_read_nonexistent_item():
    response = client.get("/items/baz", headers={"X-Token": "coneofsilence"})
    assert response.status_code == 404
    assert response.json() == {"detail": "Item not found"}


def test_create_item():
    response = client.post(
        "/items/",
        headers={"X-Token": "coneofsilence"},
        json={"id": "foobar", "title": "Foo Bar", "description": "The Foo Barters"},
    )
    assert response.status_code == 200
    assert response.json() == {
        "id": "foobar",
        "title": "Foo Bar",
        "description": "The Foo Barters",
    }


def test_create_item_bad_token():
    response = client.post(
        "/items/",
        headers={"X-Token": "hailhydra"},
        json={"id": "bazz", "title": "Bazz", "description": "Drop the bazz"},
    )
    assert response.status_code == 400
    assert response.json() == {"detail": "Invalid X-Token header"}


def test_create_existing_item():
    response = client.post(
        "/items/",
        headers={"X-Token": "coneofsilence"},
        json={
            "id": "foo",
            "title": "The Foo ID Stealers",
            "description": "There goes my stealer",
        },
    )
    assert response.status_code == 409
    assert response.json() == {"detail": "Item already exists"}
"""