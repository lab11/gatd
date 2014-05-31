Website Example
===============

GATD leverages socket.io for streaming data and we use some libraries for
graphing (flot, jquery, underscore). You can use [bower](http://bower.io/) to
install all of these automatically, simply run:

`bower install`

Then, edit the `computer_usage.html` set the `GATD_HOSTNAME` and
`COMP_USAGE_PROFILE_ID` variables (they are at the beginning of the `onload`
function, around line 185).

Next, run a local webserver to serve the page:

`python3 -m http.server 8000` or `python2 -m SimpleHTTPServer 8000`

In a browser, go to <http://localhost:8000/computer_usage.html>. If everything's
working, you should see a checkbox for your machine at the bottom of the page,
check it and watch the data!
