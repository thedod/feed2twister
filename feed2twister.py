from conf import *
import feedparser,anydbm,sys
from bitcoinrpc.authproxy import AuthServiceProxy

def get_next_k(twister,username):
    try:
        return twister.getposts(1,[{'username':username}])[0]['userpost']['k']+1
    except:
        return 0

def main(max_items):
    db = anydbm.open(DB_FILENAME,'c')
    twister = AuthServiceProxy(RPC_URL)
    for feed_url in FEEDS:
        logging.info(feed_url)
        feed = feedparser.parse(feed_url)
        n_items = 0
        for e in feed.entries:
            eid = '{0}|{1}'.format(feed_url,e.id)
            if db.has_key(eid): # been there, done that (or not - for a reason)
                logging.debug('Skipping duplicate {0}'.format(eid))
            else: # format as a <=140 character string
                if len(e.link)<=MAX_URL_LENGTH:
                    msg = u'{0} {1}'.format(e.link,e.title)
                    if len(msg)>140: # Truncate (and hope it's still meaningful)
                        msg = msg[:137]+u'...'
                else: # Link too long. Not enough space left for text :(
                    msg = ''
                db[eid] = msg.encode('utf8') # Anydbm can't do unicode. utf8 may become >140, but it doesn't matter ;)
                if not msg: # We've marked it as "posted", but no sense really posting it.
                    logging.warn(u'Link too long at {0}'.format(eid))
                    continue
                if n_items>=max_items: # Avoid accidental flooding
                    logging.warn(u'Skipping "over quota" item: {0}'.format(msg))
                    continue
                logging.info(u'posting {0}'.format(msg))
                try:
                    twister.newpostmsg(USERNAME,get_next_k(twister,USERNAME),msg)
                except Exception,e:
                    logging.error(e)
                n_items+=1

if __name__=='__main__':
    if len(sys.argv)>1:
        if len(sys.argv)>2 or not sys.argv[1].isdigit():
            sys.stderr.write("""Usage: {cmd} [N]
if [optional] N is supplied, it's used as the maximum items to post (per feed). Default is {n}.
If there are more than N new items in a feed, "over quota" items get marked as if they were posted
(this can be handy when you add a new feed with a long history).
Specifically, {cmd} 0 would make all feeds "catch up" without posting anything.
""".format(cmd=sys.argv[0],n=MAX_NEW_ITEMS_PER_FEED))
            sys.exit(-1)
        else:
            n = int(sys.argv[1])
    else:
        n = MAX_NEW_ITEMS_PER_FEED
    main(n)
