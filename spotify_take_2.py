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
from difflib import SequenceMatcher
import pandas as pd
from datetime import datetime
import spotipy
import spotipy.util as util
import os
import config
import sqlite3

#function to add some string distance help for misspellings of program names
def similar(a,b):
    return SequenceMatcher(None, a, b).ratio()

# main function that creates a data frame of the program on cbc's tracklist
def scrape_cbc_weblogs(program_name):
    chrome_options = Options()
    chrome_options.add_argument('--headless')
    
    driver = webdriver.Chrome(options = chrome_options)
    driver.get('https://www.cbcmusic.ca/on-air/playlogs')
    
    #click on the specified program name
    elem = driver.find_elements_by_class_name('playlog__programs__program__title')
    prog_names_list = list()
    for i in range(len(elem)):
        if(elem[i].text != ''):
            prog_names_list.append(elem[i].text.lower())
            
    #if the input is not an exact match will find the closest distance program name
    try:        
        i = prog_names_list.index(program_name.lower())
    except ValueError:
        prog_names_list = pd.DataFrame(prog_names_list)
        prog_names_list.columns =['program']
        prog_names_list['ratio'] = [similar(program_name,i) for i in prog_names_list['program']]
        if prog_names_list['ratio'].max() >= .5:
            i = prog_names_list['ratio'].idxmax()
        else:
            print('INPUT ERROR:\nprogram name does not match any known program. check input\nINPUT ERROR')
            return

    
    elem = driver.find_element_by_xpath('//*[@id="Playlog"]/div[5]/ul/li[{}]/div[1]/div[2]/div/button'.format(i+1)).click()
    
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
    
    song_album_list = data_df.drop(data_df[data_df.attr_type != 'Album'].index).drop(columns = 'attr_type').reset_index(drop = True)
    song_title_list = data_df.drop(data_df[data_df.attr_type != 'Title'].index).drop(columns = 'attr_type').reset_index(drop = True)
    song_artist_list = data_df.drop(data_df[data_df.attr_type != 'Artist'].index).drop(columns = 'attr_type').reset_index(drop = True)

    elem = driver.find_elements_by_class_name('playlog__programs__program__broadcasttime')
    #times come in with poor formatting need to adjust into a full datetime
    times_list = list()
    for i in range(len(elem)):
        if(elem[i].text != ''):
            if(len(elem[i].text)==3):
                z = '0'+elem[i].text[:1]+':00'+elem[i].text[1:3]
            elif(len(elem[i].text) == 4):
                z = elem[i].text[:2]+':00'+elem[i].text[2:4]
            elif(len(elem[i].text) == 6):
                z = '0'+elem[i].text
            else:
                z = elem[i].text
            z2 = str(datetime.today().strftime('%Y-%m-%d')) +' '+ z
            app = datetime.strptime(z2.upper(),'%Y-%m-%d %I:%M%p').strftime('%Y-%m-%d %H:%M:%S')
            times_list.append(app)
    times_list = pd.DataFrame(times_list)
    times_list.columns = ['timestamp']
    prog_name_list = [program_name] * len(times_list)
    prog_name_list = pd.DataFrame(prog_name_list)
    data_df = pd.concat([song_title_list,song_artist_list,song_album_list,times_list,prog_name_list],axis=1)
    data_df.columns = ['title','artist','album','timestamp','program_name']
    driver.close()
    return(data_df)

data_df = scrape_cbc_weblogs('nightstream')

# initial spotify enable
#first time giving this scope you will need to input the url from your browser!! and uncomment the spotify redirect uri var
def get_spotify_token(username):
    token = util.prompt_for_user_token(username,client_id = config.api_key, client_secret = config.api_secret,
                                       redirect_uri ='http://localhost:8888/callback/', scope = 'playlist-modify-public')
    return(token)
    


#find all of the spotify song ids for the scraped songs from cbc
# returns no_id_found if there is not a close enough match from the scrape --potential to add in logic to use fuzzy matching and artist only calls
def get_spotify_ids(track_name = '', artist_name = '',username):
    token = get_spotify_token(username)
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

def initialize_sqlite_tables(wd):
    os.chdir(wd)
    sqlite_file = 'cbc_spotify_project_db.sqlite'
    table_name1 = 'all_playlogs'
    table_name2 = 'mornings_masterlist'
    table_name3 = 'shift_masterlist'
    table_name4 = 'drive_masterlist'
    table_name5 = 'afterdark_masterlist'
    col_spotify_id = 'spotify_id varchar(50)'
    col_dttm = 'dttm datetime2'
    col_title = 'title varchar(255)'
    col_artist = 'artist varchar(255)'
    col_album = 'album varchar(255)'
    col_program_name = 'program_name varchar(50)'
    col_added = 'track_added_dttm datetime2'
    
    conn = sqlite3.connect(sqlite_file)
    c = conn.cursor()
    
    c.execute('CREATE TABLE {tn} ({si},{dt},{ti},{ar},{al},{pr})'\
              .format(tn=table_name1,si=col_spotify_id,dt=col_dttm,ti=col_title,ar=col_artist,al=col_album,pr=col_program_name))
    
    c.execute('CREATE TABLE {tn} ({si} PRIMARY KEY,{ad})'.format(tn=table_name2,si=col_spotify_id,ad=col_added))
    c.execute('CREATE TABLE {tn} ({si} PRIMARY KEY,{ad})'.format(tn=table_name3,si=col_spotify_id,ad=col_added))
    c.execute('CREATE TABLE {tn} ({si} PRIMARY KEY,{ad})'.format(tn=table_name4,si=col_spotify_id,ad=col_added))
    c.execute('CREATE TABLE {tn} ({si} PRIMARY KEY,{ad})'.format(tn=table_name5,si=col_spotify_id,ad=col_added))
    
    conn.commit()
    conn.close()
    
initialize_sqlite_tables('C:/Users/KG/Desktop/spotify_cbc_project-master')

def add_songs_to_playlist(username, playlist_name, df):
    token = get_spotify_token(username)
    spotify = spotipy.Spotify(auth = token)
    #get playlist id
    playlist_results = spotify.user_playlists(username)
    playlist_id_update = ''
    #pull first instance of playlist match
    for i in range(0,len(playlist_results['items'])):
        if playlist_results['items'][i]['name'] == playlist_name:
            playlist_id_update = playlist_results['items'][i]['id']
            break
    add_song_list = df['spotify_id'][df['spotify_id'] != 'no_id_found']
    spotify.user_playlist_add_tracks(user = username, playlist_id = playlist_id_update,tracks=list(add_song_list))


add_songs_to_playlist('kgsoloman5k','cbc_radio_2_nightstream',data_df)
    
