Feed2twister is a simple script to post items from RSS/ATOM feeds to
[Twister](http://twister.net.co).

----

**Note:** If you upgrade an old installation where you don't have
`feed2twister.conf` yet, use a copy of `feed2twister.conf.example`s and
edit it so that it contains similar settings to those you had at `conf.py`

----

### Prerequisites

* Python 2
* [Twister](http://twister.net.co/) (of course)
* [python-bitcoinrpc](https://pypi.python.org/pypi/python-bitcoinrpc/)
* [feedparser](https://pypi.python.org/pypi/feedparser/)
* URL shortener dependencies (see `use_shortener` at `feedparser.conf.example`)

### Installing

 * run `git submodule update --init` (to install a [patched
   version](https://github.com/thedod/python-bitcoinrpc/tree/unicode-fix-for-twister)
   of bitcoin-rpc (a twister-related unicode fix). If you don't have
   git(?) you can [download the
   zip](https://github.com/thedod/python-bitcoinrpc/archive/unicode-fix-for-twister.zip),
   and copy the bitcoinrpc directory into this directory (overwrite
   whatever you have ther now. probably an empty folder).

 * Copy `feed2twister.conf.example` to `feed2twister.conf` and edit it
   to taste.

### Running

Normally, you would run this as a cron task:
`/path/to/this/feed2twister.py [-c CONFIGFILE] [N]`

if [optional] `N` is supplied, it's used as the maximum items to post
(per feed). Default is (by presence order) max_new_items_per_feed from
conf file or 0.

If there are more than `N` new items in a feed, "over quota" items get
marked as if they were posted (this can be handy when you add a new feed
with a long history).

Specifically, `python feed2twister.py 0` would make all feeds "catch up"
without posting anything.

if [optional] `CONFIGFILE` is supplied, it is used as a custom config
file, instead of the first file found in the following list:
`./feed2twister.conf`, `~/.config/feed2twister.conf`,
`~/.feed2twister.conf`

### User defined URL shortener

There is now an option to use your own URL shortener by defining
`use_shortener = user_shortener` at `feed2twister.conf`.

If you're looking for ideas,
the shortener I use is [here](https://github.com/thedod/private_url_shortener#readme).


### Hidden configuration

Some more options are available:

* `do_not_include_link` (boolean, default False): if True, feed2twister
  will NOT prepend the feed item title with the item link before posting
  it to twister.

* `skip_first_title_char` (int, default None): if set, feed2twister will
  strip this amount of character from the begining of the feed item
  title. Usefull to skip your login from app.net feed for example.
