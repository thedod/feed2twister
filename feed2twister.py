#!/usr/bin/env python2
# -*- coding: utf-8 -*-

import os,feedparser,anydbm,argparse,ConfigParser
import sys
from bitcoinrpc.authproxy import AuthServiceProxy

SCRIPT_PATH = os.path.dirname(os.path.realpath(__file__))

arg_parser = argparse.ArgumentParser(description='Feed2twister is a simple script to post items from RSS/ATOM feeds to Twister.')
arg_parser.add_argument('--config', '-c', help='Alternate config file. Default is {0}.'.format(os.path.join(SCRIPT_PATH, 'feed2twister.conf')))
arg_parser.add_argument('--repost-existing', '-f', action='store_true',
                        help='For debugging purposes. reposts items even if they are marked as already posted. Use with care.')
arg_parser.add_argument('maxitems', metavar='N', type=int, nargs='?', default=None,
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
    if option in main_config and main_config[option]:
        v = main_config[option]
        return str(v).lower() in ('yes', 'true', 't', '1')
    return False

def get_array_conf_option(option):
    if option in main_config and main_config[option]:
        return main_config[option].split("\n")
    return []

import logging
log_level = logging.ERROR
if 'logging_level' in main_config and main_config['logging_level']:
    log_level = main_config['logging_level']
    log_level = getattr(logging, log_level.upper())

logging.basicConfig(level=log_level)

# url shorteners
shortener = str(main_config.get('use_shortener', 'false')).lower()

# is.gd is the default (for historical reasons, but they're tor-user hostile :( )
if shortener in ['isgd', 'is.gd', 'gd', 'true', 'yes', 'y', '1']:
    import gdshortener
    shorten = \
        lambda url: gdshortener.ISGDShortener().shorten(url=url, log_stat=get_bool_conf_option('shortener_stats'))[0]
elif shortener in ['v', 'vgd', 'v.gd']:
    import gdshortener
    shorten = \
        lambda url: gdshortener.VGDShortener().shorten(url=url, log_stat=get_bool_conf_option('shortener_stats'))[0]
elif shortener in ['ur1', 'ur1.ca', 'ur1ca']:
    import ur1
    shorten = lambda url: ur1.shorten(url)
elif shortener in ['user_shortener', 'user']:
    from user_shortener import shorten  # User should create user_shortener.py
elif shortener in ['false', 'no', 'n', '0']:
    shorten = lambda url: url
else:
    logging.error('Invalid configuration for "use_shortener"!')
    sys.exit(10)
# endregion

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
    db = anydbm.open(os.path.expanduser(main_config['db_filename']),'c')
    twister = AuthServiceProxy(main_config['rpc_url'])

    for feed_url in get_array_conf_option('feeds'):
        logging.info(feed_url)
        feed = feedparser.parse(feed_url)
        n_items = 0

        # store posts for later since we want to post them in chronological order
        msgs = []

        for i, e in enumerate(feed.entries):
            eid = '{0}|{1}'.format(feed_url,e.get('id','???'))

            if eid in db.keys() and not args.repost_existing:  # been there, done that (or not - for a reason)
                logging.debug('Skipping duplicate {0}'.format(eid))

            else: # format as a <=140 character string
                if not get_bool_conf_option('do_not_include_link'):
                    # Construct the link, possibly with shortener
                    entry_url = str(shorten(e.link))

                    if len(entry_url) <= int(main_config['max_url_length']):
                        msg = u'{0} {1}'.format(entry_url,e.title)

                    else: # Link too long. Not enough space left for text :(
                        msg = ''

                else:
                    entry_title = e.title
                    if 'skip_first_title_char' in main_config and main_config['skip_first_title_char']:
                        entry_title = entry_title[int(main_config['skip_first_title_char']):]

                    msg = u'{0}'.format(entry_title)


                if len(msg)>140: # Truncate (and hope it's still meaningful)
                    msg = msg[:137]+u'...'


                utfmsg = truncated_utf8(msg,140)# limit is 140 utf-8 bytes (not chars)
                msg = unicode(utfmsg,'utf-8') # AuthServiceProxy needs unicode [we just needed to know where to truncate, and that's utf-8]
                if not msg: # We've marked it as "posted", but no sense really posting it.
                    logging.warn(u'Link too long at {0}'.format(eid))
                    continue

                logging.info(u'will post {0}'.format(msg))
                msgs.append((eid, msg, utfmsg))

                n_items+=1

                if n_items >= max_items:
                    logging.warn(u'Quota reached. Skipping {0} items:'.format(len(feed.entries[i+1:])))

                    for ee in feed.entries[i+1:]:
                        eeid = '{0}|{1}'.format(feed_url, ee.get('id','???'))
                        logging.warn(u'    {0}'.format(eeid))
                        # already saved this item to db anyways, so we're done here
                        if eeid in db.keys():
                            continue
                        # this is a *new* message we're skipping. build some fake post message in case
                        # we want to have a look at the database for debugging or such
                        utf8msg = truncated_utf8(u'Skipped: {0}'.format(e.title), 140)
                        db[eeid] = utf8msg
                    break

        # done parsing this feed, now post what we found, but in chronological order
        msgs.reverse()
        for (eid, msg, utfmsg) in msgs:
            try:
                logging.info(u'now posting {0}'.format(msg))
                next_k = get_next_k(twister, main_config['username'])
                twister.newpostmsg(main_config['username'], next_k, msg)
                db[eid] = utfmsg # anydbm can't handle unicode, so it's a good thing we've also kept the utf-8 :)
            except Exception, e:
                logging.error(repr(e))  # usually not very informative :(
                try: # temporary patch
                    if e.error:
                        logging.error(e.error)
                except Exception,e:
                    logging.error('error loggin borked %s',repr(e))  # usually not very informative :(


if __name__=='__main__':
    if args.maxitems != None:
        n = args.maxitems
    elif 'max_new_items_per_feed' in main_config and main_config['max_new_items_per_feed']:
        n = int(main_config['max_new_items_per_feed'])
    else:
        n = 0
    main(n)
