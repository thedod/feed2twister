from conf import *
import feedparser,anydbm,sys
from bitcoinrpc.authproxy import AuthServiceProxy

### truncated_utf8() is based on http://stackoverflow.com/a/13738452
def _is_utf8_lead_byte(b):
    '''A UTF-8 intermediate byte starts with the bits 10xxxxxx.'''
    return (ord(b) & 0xC0) != 0x80

def truncated_utf8(text,max_bytes,ellipsis='\xe2\x80\xa6'):
    '''If text[max_bytes] is not a lead byte, back up until a lead byte is
    found and truncate before that character.'''
    utf8 = text.encode('utf8')
    if len(utf8) <= max_bytes:
        return utf8
    i = max_bytes-len(ellipsis)
    while i > 0 and not _is_utf8_lead_byte(utf8[i]):
        i -= 1
    return utf8[:i]+ellipsis

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
                else: # Link too long. Not enough space left for text :(
                    msg = ''
                utfmsg = truncated_utf8(msg,140)
                db[eid] = utfmsg
                if not utfmsg: # We've marked it as "posted", but no sense in really posting it.
                    logging.warn(u'Link too long at {0}'.format(eid))
                    continue
                if n_items>=max_items: # Avoid accidental flooding
                    logging.warn('Skipping "over quota" item: {0}'.format(utfmsg)) # NOT unicode
                    continue
                logging.info('posting {0}'.format(utfmsg)) # NOT unicode
                try:
                    twister.newpostmsg(USERNAME,get_next_k(twister,USERNAME),utfmsg)
                except Exception,e: # To do: find out why some unicode chars screw this and how to do this "right"
                    logging.error(`e`)
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
