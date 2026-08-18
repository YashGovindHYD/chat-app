# TODOs

## Features to add

- [ ] Feed feature

## Known issues

- [ ] `websocket_chat.py:62` — `data['conversation_id']` reads from the client payload instead of the URL path param; works only because clients happen to send it, but is redundant/fragile
