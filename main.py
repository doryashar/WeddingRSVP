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
app.add_route("/", WeddingWA.wa.verify_wa_token , ["GET"])
app.add_route("/", WeddingWA.wa.wa_in_webhook , ["POST"])

app.add_route("/send-message-id/{wedding_id}/{message}/{phone_number}", WeddingWA.send_message_id , ["GET"])
app.add_route("/send-template-id/{wedding_id}/{template_id}/{phone_number}", WeddingWA.send_template_id , ["GET"])

app.add_route("/rsvp/{code}", WeddingWA.rsvp, ["GET"])
app.add_route("/get_google_cal", WeddingWA.get_google_calendar, ["GET"]) #/{code}
app.add_route("/update_invitee", WeddingWA.got_new_form_update, ["POST"])

# app.add_route("/send-reminders/{phone_number}", WeddingWA.send_reminder , ["GET"])
# app.add_route("/send-invites/{phone_number}/{name}", WeddingWA.send_invite , ["GET"])


# ==================================================================
## Run the app:
# -----------------
if __name__ == "__main__":
    uvicorn.run(app, host='0.0.0.0', port=8070)