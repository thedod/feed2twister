import os,feedparser,anydbm,argparse,ConfigParser
from bitcoinrpc.authproxy import AuthServiceProxy

SCRIPT_PATH = os.path.dirname(os.path.realpath(__file__))

arg_parser = argparse.ArgumentParser(description='Feed2twister is a simple script to post items from RSS/ATOM feeds to Twister.')
arg_parser.add_argument('--config', '-c', help='Alternate config file. Default is {0}.'.format(os.path.join(SCRIPT_PATH, 'feed2twister.conf')))
arg_parser.add_argument('--maxitems', '-n', type=int, metavar='N',
                        help="""Maximum items to post (per feed). Default is 0.
If there are more than N new items in a feed, "over quota" items get marked as if they were posted (this can be handy when you add a new feed with a long history). Specifically, %(prog)s 0 would make all feeds "catch up" without posting anything.""")
args = arg_parser.parse_args()

from xdg.BaseDirectory import xdg_config_home
main_config_file = ConfigParser.ConfigParser()
if args.config:
    main_config_file.read([os.path.expanduser(args.config)])
else:
    main_config_file.read([os.path.join(SCRIPT_PATH, 'feed2twister.conf'), os.path.join(xdg_config_home, 'feed2twister.conf'), os.path.expanduser('~/.feed2twister.conf')])
main_config = main_config_file.defaults()

def get_bool_conf_option(option):
    if main_config[option]:
        v = main_config[option]
        return str(v).lower() in ('yes', 'true', 't', '1')
    return False

def get_array_conf_option(option):
    if main_config[option]:
        return main_config[option].split("\n")
    return []

import logging
log_level = logging.ERROR
if main_config['logging_level']:
    log_level = main_config['logging_level']
    log_level = getattr(logging, log_level.upper())

logging.basicConfig(level=log_level)

if get_bool_conf_option('use_shortener'):
    try:
        import gdshortener
    except ImportError:
        USE_SHORTENER = False


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
    db = anydbm.open(main_config['db_filename'],'c')
    twister = AuthServiceProxy(main_config['rpc_url'])

    for feed_url in get_array_conf_option('feeds'):
        logging.info(feed_url)
        feed = feedparser.parse(feed_url)
        n_items = 0

        for e in feed.entries:
            eid = '{0}|{1}'.format(feed_url,e.id)

            if db.has_key(eid): # been there, done that (or not - for a reason)
                logging.debug('Skipping duplicate {0}'.format(eid))

            else: # format as a <=140 character string
                # Construct the link, possibly with shortener
                entry_url = gdshortener.ISGDShortener().shorten(url=e.link, log_stat=get_bool_conf_option('shortener_stats'))[0] if get_bool_conf_option('use_shortener') else e.link

                if len(entry_url) <= int(main_config['max_url_length']):
                    msg = u'{0} {1}'.format(entry_url,e.title)

                    if len(msg)>140: # Truncate (and hope it's still meaningful)
                        msg = msg[:137]+u'...'

                else: # Link too long. Not enough space left for text :(
                    msg = ''


                utfmsg = truncated_utf8(msg,140)# limit is 140 utf-8 bytes (not chars)
                msg = unicode(utfmsg,'utf-8') # AuthServiceProxy needs unicode [we just needed to know where to truncate, and that's utf-8]
                db[eid] = utfmsg # anydbm, on the other hand, can't handle unicode, so it's a good thing we've also kept the utf-8 :)
                if not msg: # We've marked it as "posted", but no sense really posting it.
                    logging.warn(u'Link too long at {0}'.format(eid))
                    continue

                if n_items >= max_items: # Avoid accidental flooding
                    logging.warn(u'Skipping "over quota" item: {0}'.format(msg))
                    continue

                logging.info(u'posting {0}'.format(msg))

                try:
                    twister.newpostmsg(main_config['username'],
                                       get_next_k(twister,
                                                  main_config['username']),
                                       msg)
                except Exception,e:
                    logging.error(`e`) # usually not very informative :(

                n_items+=1



if __name__=='__main__':
    if args.maxitems != None:
        n = args.maxitems
    elif main_config['max_new_items_per_feed']:
        n = int(main_config['max_new_items_per_feed'])
    else:
        n = 0
    main(n)
