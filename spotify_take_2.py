# -*- coding: utf-8 -*-
"""
Created on Wed Mar 20 19:44:01 2019

@author: KG
"""

from selenium import webdriver
from selenium.webdriver.chrome.options import Options  
import pandas as pd

chrome_options = Options()
chrome_options.add_argument('--headless')

driver = webdriver.Chrome(options = chrome_options)
driver.get('https://www.cbcmusic.ca/on-air/playlogs')

#click on nightstream element
# CHANGING THE NUMBER IN LI[X] WILL CHANGE WHICH SHOW IS CLICKED
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

# enable spotify, set-up code in different file


