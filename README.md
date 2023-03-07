# linktower

This is a small Flask application I made for practice creating websites and API's among other things. I wrote this program using [org-mode's](https://orgmode.org/worg/) [literate programming](http://literateprogramming.com/) facilities. This means that the program is meant to be read as a document with source code rather than source code with comments. For this I've exported the org file to html, which can be found in the file [linktower.html](linktower.html). This was somewhat of an experiment in literate programming for me.

	I probably won't deploy this application due to the difficulties of content moderation (don't want to have to deal with people posting links to illegal things, seemingly the fate of all pastebin sites).

## Running the application
Since it's somewhat inconvenient to install emacs just to tangle the org file, I did so myself. The resulting program is contained entirely in `app.py`. It can be run with `python -m flask run`. In order to intialize the database, run `sqlite test.db < schema.sql`.


