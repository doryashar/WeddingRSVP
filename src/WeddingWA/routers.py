# from fastapi import APIRouter, Depends, HTTPException
# # router = APIRouter(
# #     prefix="/items",
# #     tags=["items"],
# #     # dependencies=[Depends(get_token_header)],
# #     responses={404: {"description": "Not found"}},
# # )


# # ==================================================================
# ## Init routers:
# # -----------------
# # @app.get("/")
# app.add_route("/", WeddingWA.wa.verify_wa_token , ["GET"])
# app.add_route("/", WeddingWA.wa.wa_in_webhook , ["POST"])

# app.add_route("/send-message-id/{wedding_id}/{message}/{phone_number}", WeddingWA.send_message_id , ["GET"])
# app.add_route("/send-template-id/{wedding_id}/{template_id}/{phone_number}", WeddingWA.send_template_id , ["GET"])

# app.add_route("/rsvp/{code}", WeddingWA.rsvp, ["GET"])
# app.add_route("/get_google_cal", WeddingWA.get_google_calendar, ["GET"]) #/{code}
# app.add_route("/update_invitee", WeddingWA.got_new_form_update, ["POST"])

# # app.add_route("/send-reminders/{phone_number}", WeddingWA.send_reminder , ["GET"])
# # app.add_route("/send-invites/{phone_number}/{name}", WeddingWA.send_invite , ["GET"])