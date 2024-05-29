import logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)

from dotenv import load_dotenv
load_dotenv()

from os import getenv
import time
import uvicorn
from fastapi import FastAPI
from src.WeddingWA import app as WeddingWA


app = FastAPI()
WeddingWA.startup()

# ==================================================================
## Init routers:
# -----------------
# @app.get("/")
app.add_api_route("/wa_hook/", WeddingWA.wa.verify_wa_token , methods=["GET"])
app.add_api_route("/wa_hook/", WeddingWA.wa.wa_in_webhook , methods=["POST"])

app.add_api_route("/send-message-id/{wedding_id}/{message}/{phone_number}", WeddingWA.send_message_id , methods=["GET"])
app.add_api_route("/send-template-id/{wedding_id}/{template_id}/{phone_number}", WeddingWA.send_template_id , methods=["GET"])

app.add_api_route("/rsvp/{code}", WeddingWA.rsvp, methods=["GET"])
app.add_api_route("/get_google_cal", WeddingWA.get_google_calendar, methods=["GET"]) #/{code}
app.add_api_route("/update_invitee", WeddingWA.got_new_form_update, methods=["POST"])

# app.add_api_route("/send-reminders/{phone_number}", WeddingWA.send_reminder , methods=["GET"])
# app.add_api_route("/send-invites/{phone_number}/{name}", WeddingWA.send_invite , methods=["GET"])


# ==================================================================
## Run the app:
# -----------------
if __name__ == "__main__":
    uvicorn.run(app, host='0.0.0.0', port=8070)