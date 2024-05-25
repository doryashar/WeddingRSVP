# import logging
# logging.basicConfig(
#     level=logging.INFO,
#     format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
# )
# from dotenv import load_dotenv
# load_dotenv()
import pytest
from fastapi.testclient import TestClient
from main import app
from main import WeddingWA
import random, string
from time import time
client = TestClient(app)


wedding_id = 0
message_id = 'reminder-0'
phone_number = '972548826569'

def fake_receive_message(phone, message):
    id = str(random.randint(1000000000,9999999999))
    msgid = ''.join([random.choice(string.ascii_letters) for i in range(20)])
    timestamp = time()
    received_message = {'object': 'whatsapp_business_account', 'entry': [{'id': str(id), 'changes': [{'value': {'messaging_product': 'whatsapp', 'metadata': {'display_phone_number': '972559569965', 'phone_number_id': '101369269635426'}, 'contacts': [{'profile': {'name': 'Dor'}, 'wa_id': phone}], 'messages': [{'from': phone, 'id': msgid, 'timestamp': timestamp, 'text': {'body': message}, 'type': 'text'}]}, 'field': 'messages'}]}]}
    return received_message, msgid

@pytest.mark.asyncio
async def test_read_item():
    """ 
    - Verify we can send a message and update all the statuses upto 'read'
    - Verify we can recieve a message and update the history
    - Verify we can recieve a message from unknown and update the messages table
    """
    response = client.get(f"/send-template-id/{wedding_id}/{message_id}/{phone_number}") #, headers={"X-Token": "coneofsilence"})
    assert response.status_code == 200
    # assert response.json() == {
    #     "id": "foo",
    #     "title": "Foo",
    #     "description": "There goes my hero",
    # }
    #TODO: verify all statuses upto "read"
    
    message = 'שלום'
    received_message, msgid = fake_receive_message(phone_number, message)
    response = client.post('/', json=received_message)
    assert response.status_code == 200
    table, uid, row = await WeddingWA.db.get_row(phone=phone_number)
    history = row.get('history')
    assert message == row.get('message')
    assert msgid == row.get('msgid')
    assert msgid in history
    assert message in history
    
    # - Verify we can recieve a message from unknown and update the messages table
    

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