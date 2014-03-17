import logging
logging.basicConfig(level=logging.INFO)
#logging.basicConfig(level=logging.ERROR) # For deployment. It's on a don't wanna know basis :)
USERNAME = 'MYTWISTERUSERNAME' # e.g 'thedod'
RPC_URL = 'http://MYRPCUSER:MYRPCPASSWORD@127.0.0.1:28332' # change to rpcuser and rpcpassword from ~/.twister/twister.conf
DB_FILENAME = 'items.db' # db is mainly there to keep track of "what not to post again" :) (debugging too, I guess)
MAX_URL_LENGTH = 100 # this leaves 36 characters and a ... to get to 140. If we don't have that, we skip the item :(
MAX_NEW_ITEMS_PER_FEED = 3 # we don't want to flood more than that in a single run.
FEEDS = [ # Use your own feeds, of course :)
    'https://swatwt.com/favs/rss/en',
    'https://github.com/thedod.atom'
]
