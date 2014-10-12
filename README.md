Feed2twister is a simple script to post items from RSS/ATOM feeds to [Twister](http://twister.net.co).

### Prerequisites

* [Twister](http://twister.net.co/) (of course)
* [python-bitcoinrpc](https://pypi.python.org/pypi/python-bitcoinrpc/)
* [feedparser](https://pypi.python.org/pypi/feedparser/)
* [gdshortener](https://github.com/torre76/gd_shortener/) (optional)

### Installing

 * run `git submodule update --init`
   (to install a [patched version](https://github.com/thedod/python-bitcoinrpc/tree/unicode-fix-for-twister)
   of bitcoin-rpc (a twister-related unicode fix).
   If you don't have git(?) you can [download the zip](https://github.com/thedod/python-bitcoinrpc/archive/unicode-fix-for-twister.zip),
   and copy the bitcoinrpc directory into this directory (overwrite whatever you have ther now. probably an empty folder).

 * Copy `feed2twister.conf.example` to `feed2twister.conf` and edit it to taste.

### Running

Normally, you would run this as a cron task: `cd /path/to/this ; python feed2twister.py` [`-n N`] [`-c CONFIGFILE`]

if [optional] `N` is supplied, it's used as the maximum items to post (per feed). Default is `0`.

If there are more than `N` new items in a feed, "over quota" items get marked as if they were posted
(this can be handy when you add a new feed with a long history).

Specifically, `python feed2twister.py 0` would make all feeds "catch up" without posting anything.

if [optional] `CONFIGFILE` is supplied, it is used as a custom config file, instead of the first file found in the following list: ./feed2twister.conf, ~/.config/feed2twister.conf, ~/.feed2twister.conf