Wedding Inviter

* docker build and run: 
`docker build -t weddingapp:latest -f ./Dockerfile .`
`docker run --rm -p 80:80 weddingapp:latest`


TODO:
- add user functions (routes) for send-invite, send-reminder
- for every response error put logging message.
- add errors table to put some need to review errors there. test
- add reminded times to allow multiple reminders
- automated template sending depending on the wedding configuration timing.
- failsafe mechanism (kafka?k8s?)
- remove wedding id, instead, each phone number is used for only single wedding at a time. when the wedding is done, archive.
- each instance should get configuration for the weeding with attached phone number, and specific table for this phone number.

- customer website:
 - marketing page
 - contact us button/email form/live chat
 - for paid wedding: see details, upload/download csv, add/edit/remove fields and rows. chat
 - for managers: chat with customer, add wedding, manage wedding

- add "archive" wedding
- secure routes with access tokens

====================================================================
high level functions-

- send_invites
- retry_failed_invites
- send_reminder
- send_day_wedding
- send_post_wedding

====================================================================
routes - 

+ send-template/{template_id}/{uid}
+ rsvp/{code}
+ whatsapp/{}
+ send-messgae/{}

====================================================================
Tables-

WEDDINGS_INFO
==============
id
names
date
time
place
location
calendar invite
image




WEDDING_INVITES
================
wedding_id - 
gift - 
notes -
coming -
vegis - 
guest_requests - 


UID - user unique id
Phone - user main phone number
PhoneALT - user alternative phone number
Name - 
Relation - 
num_of_invitees - 
clicked - Boolean, if the user entered the url
STATE - Waiting, Invited, Answered(coming/notcoming), Reminded, Remind-Answered, FollowUp-guest-num, followup-answered, followup-finish, not-coming-msg, day-of-wedding-message, post-wedding-message
MSGID - last sent message delivery ID.
STATUS - last sent message delivery status: trying, failed, delivery-error, sent, delivered, read.
TIMESTAMP - last update timestamp
time - created time
message_history - [(timestamp, id, message, status)...]