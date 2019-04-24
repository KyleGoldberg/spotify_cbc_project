# spotify_cbc_project
use cbc radio 2 playlogs combined with spotify API to automatically create playlists

First, we check the robots.txt of the CBC website to ensure we are not scraping against their wishes.
https://www.cbcmusic.ca/robots.txt

Following the rules outlined in the below link, we are good to go.
http://www.robotstxt.org/robotstxt.html

Ensure to create a file config.py with your spotify client id and spotify client secret as "api_key" and "api_secret"

The script then follows this path ->
*Initial Work:*
Scrape the artist/track name from the desired cbc radio 2 program ->
Identify the spotify song id associated with each individual track/artist ->
Store the raw event time logs in a sqlite database ->
Store master list of all played tracks for a given program in a sqlite database ->
Check for any new additions to the master list from the latest day ->
Add any new additions to the designated spotify playlist for that program

*Future Work:*
Pull down song level attributes into the sqlite database to do some exploratory data analysis
Use Genius API to pull song lyrics into sqlite database to join with the spotify data
