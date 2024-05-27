import logging, os, sys
from heyoo import WhatsApp
from fastapi import Response, Request
from fastapi import FastAPI, BackgroundTasks, Request, Response, Query

logging.debug(f"Connecting to whatsapp")
messenger = WhatsApp(os.getenv("WHATSAPP_TOKEN"), phone_number_id=os.getenv("WHATSAPP_PHONE_NUMBER_ID"))


message_handler_cb = []
delivery_handler_cb = []
def add_message_handler_cb(cb):
    message_handler_cb.append(cb)
def add_delivery_handler_cb(cb):
    delivery_handler_cb.append(cb)
    


async def send_message(phone_number, message):    
    logging.info(f"Sending message: {message} to: {phone_number}")
    rsp = messenger.send_message(message, phone_number)
    logging.info(f"Response: {rsp}")
    if rsp.get('error', None):
        return Response(status_code=rsp['error']['code'], content=rsp['error']['message'])
    ret = Response(status_code=200, content="Success")
    ret.id = rsp['messages'][0]['id']
    return ret


    
async def handle_incoming_message(message, from_mobile, from_name, id):
    logging.info("Handling Message: %s", message)
    for cb in message_handler_cb:
        rsp = await cb(id, from_mobile, "received", message, from_name)
    return rsp    
    
async def handle_delivery_status(delivery, msg_id, mobile, timestamp):
    logging.info(f"Handling delivery={delivery}, msg_id={msg_id}, mobile={mobile}, timestamp={timestamp}")
    # delivery in ['sent','delivered','read']    
    for cb in delivery_handler_cb:
        rsp = await cb(delivery, msg_id, mobile, timestamp)
    return rsp

async def send_read_receipt(data):
    msg_id = messenger.get_message_id(data)
    json_data = {
        "messaging_product": "whatsapp",
        "status": "read",
        "message_id": msg_id,
    }
    messenger.send_custom_json(json_data)  
      
# async 
async def handle_data(data):
    changed_field = messenger.changed_field(data)
    if changed_field == "messages":
        new_message = messenger.is_message(data)
        if new_message:
            mobile = messenger.get_mobile(data)
            name = messenger.get_name(data)
            message_type = messenger.get_message_type(data)
            logging.info(f"New Message; sender:{mobile} name:{name} type:{message_type}")
            if message_type == "text":
                message = data['button'].get('text')
                await send_read_receipt(data)
                id = messenger.get_message_id(data)
                await handle_incoming_message(message, mobile, name, id)
                return
            
            elif message_type == "button":
                message = messenger.get_message(data)
                await send_read_receipt(data)
                id = messenger.get_message_id(data)
                await handle_incoming_message(message, mobile, name, id)
                return

            elif message_type == "interactive":
                message_response = messenger.get_interactive_response(data)
                interactive_type = message_response.get("type")
                message_id = message_response[interactive_type]["id"]
                message_text = message_response[interactive_type]["title"]
                logging.info(f"Interactive Message; {message_id}: {message_text}")

            elif message_type == "location":
                message_location = messenger.get_location(data)
                message_latitude = message_location["latitude"]
                message_longitude = message_location["longitude"]
                logging.info("Location: %s, %s", message_latitude, message_longitude)

            elif message_type == "image":
                image = messenger.get_image(data)
                image_id, mime_type = image["id"], image["mime_type"]
                image_url = messenger.query_media_url(image_id)
                image_filename = messenger.download_media(image_url, mime_type)
                logging.info(f"{mobile} sent image {image_filename}")

            elif message_type == "video":
                video = messenger.get_video(data)
                video_id, mime_type = video["id"], video["mime_type"]
                video_url = messenger.query_media_url(video_id)
                video_filename = messenger.download_media(video_url, mime_type)
                logging.info(f"{mobile} sent video {video_filename}")

            elif message_type == "audio":
                audio = messenger.get_audio(data)
                audio_id, mime_type = audio["id"], audio["mime_type"]
                audio_url = messenger.query_media_url(audio_id)
                audio_filename = messenger.download_media(audio_url, mime_type)
                logging.info(f"{mobile} sent audio {audio_filename}")

            elif message_type == "document":
                file = messenger.get_document(data)
                file_id, mime_type = file["id"], file["mime_type"]
                file_url = messenger.query_media_url(file_id)
                file_filename = messenger.download_media(file_url, mime_type)
                logging.info(f"{mobile} sent file {file_filename}")
            else:
                logging.info(f"{mobile} sent {message_type} ")
                logging.info(data)
        else:
            delivery = messenger.get_delivery(data)
            if delivery:
                msg_id = data['entry'][0]['changes'][0]["value"]['statuses'][0].get('id', None)
                timestamp = data['entry'][0]['changes'][0]["value"]['statuses'][0].get('timestamp', None)
                mobile = data['entry'][0]['changes'][0]["value"]['statuses'][0].get('recipient_id', None)
                # message = data['entry'][0]['changes'][0]['statuses'][0].
                await handle_delivery_status(delivery, msg_id, mobile, timestamp)
                logging.info(f"Message : {delivery}")
            else:
                logging.info("No new message")
 
async def verify_wa_token(
    token: str = Query(alias="hub.verify_token"),
    challenge: str = Query(alias="hub.challenge"),
    ):
    if token == os.getenv('WHATSAPP_VERIFY_TOKEN'):
        logging.info("Verified webhook")
        return Response(status_code=200, content=challenge)
    logging.error("Webhook Verification failed")
    return Response(status_code=400, content="Invalid verification token")
 
async def wa_in_webhook(request: Request, bg_tasks: BackgroundTasks):
    try:
        data = await request.json()
        logging.info("Received webhook data: %s", data)
        bg_tasks.add_task(handle_data, data)
        return "Success"
    except Exception as e:
        logging.error(f"Exception caught in webhook: {e}")
        return Response(status_code=404, content="Not found")