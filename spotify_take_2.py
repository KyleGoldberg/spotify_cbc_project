# -*- coding: utf-8 -*-
"""
Created on Wed Mar 20 19:44:01 2019

@author: KG
"""
#notes --
# make a new playlist if this playlist is full
# dedupe playlist


#test
from selenium import webdriver
from selenium.webdriver.chrome.options import Options  
import pandas as pd

chrome_options = Options()
chrome_options.add_argument('--headless')

driver = webdriver.Chrome(options = chrome_options)
driver.get('https://www.cbcmusic.ca/on-air/playlogs')

#click on nightstream element
# CHANGING THE NUMBER IN LI[X] WILL CHANGE WHICH SHOW IS CLICKED
# set up a loop to append all numbers in order to capture all shows -- how to capture the show name??
elem = driver.find_element_by_xpath('//*[@id="Playlog"]/div[5]/ul/li[7]/div[1]/div[2]/div/button').click()

#pull all elements (composer,title,artist,album)
# clean them up to just get the title/artist pairs

elem = driver.find_elements_by_class_name('playlog__programs__program__data')
#prob need to add a show name field once we start pulling other than nightstream
data_list = list()
for i in range(len(elem)):
    if(elem[i].text != ''):
        data_list.append(elem[i].text)
        
elem = driver.find_elements_by_class_name('playlog__programs__program__property__name')

data_cat_list = list()
for i in range(len(elem)):
    if(elem[i].text != ''):
        data_cat_list.append(elem[i].text)
        
data_df = pd.concat([pd.DataFrame(data_list),pd.DataFrame(data_cat_list)],axis=1)
data_df.columns = ['song_attr','attr_type']

data_df = data_df.drop(data_df[data_df.attr_type == 'Composer'].index)
data_df = data_df.drop(data_df[data_df.attr_type == 'Album'].index)

song_title_list = data_df.drop(data_df[data_df.attr_type == 'Artist'].index).drop(columns = 'attr_type').reset_index(drop = True)
song_artist_list = data_df.drop(data_df[data_df.attr_type == 'Title'].index).drop(columns = 'attr_type').reset_index(drop = True)

data_df = pd.concat([song_title_list,song_artist_list],axis=1)
data_df.columns = ['title','artist']

driver.close()


# initial spotify enable
import spotipy
import spotipy.util as util
import os

os.environ["SPOTIPY_CLIENT_ID"] = '03de3dd701084c42852155a92f0e92db'
os.environ["SPOTIPY_CLIENT_SECRET"] = "xx"
os.environ["SPOTIPY_REDIRECT_URI"] = 'http://localhost:8888/callback/'

#first time giving this scope you will need to input the url from your browser!!
token = util.prompt_for_user_token('kgsoloman5k',scope = 'playlist-modify-public')


#find all of the spotify song ids for the scraped songs from cbc
# returns no_id_found if there is not a close enough match from the scrape --potential to add in logic to use fuzzy matching and artist only calls
def get_spotify_ids(track_name = '', artist_name = ''):
    token = util.prompt_for_user_token('kgsoloman5k',scope = 'playlist-modify-public')
    spotify = spotipy.Spotify(auth = token)
    query = ''
    if track_name != '':
        query = query + 'track:'+track_name
    if (track_name != '' and artist_name != ''):
        query = query + ' '
    if artist_name != '':
        query = query + 'artist:'+artist_name
    results = spotify.search(q=query, type = 'track')
    ret = ''
    try:
        ret = results['tracks']['items'][0]['id']
    except IndexError:
        ret = 'no_id_found'
    return(ret)

    
data_df['spotify_id'] = [get_spotify_ids(x,y) for x,y in zip(data_df['title'],data_df['artist'])]

def add_songs_to_playlist(username, playlist_name, df):
    token = util.prompt_for_user_token(username,scope = 'playlist-modify-public')
    spotify = spotipy.Spotify(auth = token)
    #get playlist id
    playlist_results = spotify.user_playlists(username)
    playlist_id_update = ''
    for i in range(0,len(playlist_results['items'])):
        if playlist_results['items'][i]['name'] == playlist_name:
            playlist_id_update = playlist_results['items'][i]['id']
            break
    add_song_list = df['spotify_id'][df['spotify_id'] != 'no_id_found']
    spotify.user_playlist_add_tracks(user = username, playlist_id = playlist_id_update,tracks=list(add_song_list))


add_songs_to_playlist('kgsoloman5k','cbc_radio_2_nightstream',data_df)

    
