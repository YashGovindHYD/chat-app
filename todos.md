# TODOs

## Features to add
- [ ] Feed feature
- [ ] Combined endpoint: get conversations + their messages in one response
- [ ] Get all messages for a particular conversation (e.g. `GET /messages?conversation_id=`)

## Known issues
- [ ] `websocket_chat.py:62` — `data['conversation_id']` reads from the client payload instead of the URL path param; works only because clients happen to send it, but is redundant/fragile
- [ ] Old conversations (created before the auto-add-owner fix) don't have the owner in `conversation_members` — needs manual backfill if they should be usable
