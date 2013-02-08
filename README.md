Lloyds TSB Statement Downloader
===============================

Status
------

Not finished yet!

Background
----------

I wanted to download my statement history but it turns out that LBG's export 
function isn't suited to bulk exports:

1. It only allows you to export 3 months at a time. 
2. It only allows you to export 150 entries at a time.
3. If a given period contains 150 entries then it fails silently. So you have
   to check each and every download manually and choose a smaller window if 
   the row count is 150.
4. There is no guarantee you'll get the range that you requested. Caching bugs
   cause your browser to download the same file multiple times, so to be sure
   you actually get the export you requested you must log in and out between
   exports.

Clearly this will not do. The idea of this script is to download your account
history to a CSV file without having to dedicate a weekend to the task.

Ingredients
-----------

You will need:

1. Python 2.7.x or greater
2. The mechanize module (apt-get install python-mechanize)
3. A Lloyds TSB account

License
-------
Copyright (c) 2013 Gaz Davidson <gaz@bitplane.net>

Licensed under the [WTFPL](http://en.wikipedia.org/wiki/WTFPL) with one
additional clause:

   1. Don't blame me.


