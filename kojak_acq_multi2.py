"""
Acquisition and cleaning helper functions for Project Kojak at Metis Data Science Immersive
"""
import pandas as pd
import glob
import os
from bs4 import BeautifulSoup
import re
from selenium import webdriver
import selenium
import time
import random
import pickle
from multiprocessing import Pool
import random


def consolidate_csvs_and_eliminate_duplicates (csv_folder_path):
    """
    Take local filepath for folder with a regions various csv files

    Concatenate into a single dataframe

    Drop duplicate records

    Drop records that don't have a Days on Market entry

    Rename URL column and drop entries with duplicate URLs

    """


    all_files = glob.glob(os.path.join(csv_folder_path, "*.csv")) 
    df_from_each_file = (pd.read_csv(f) for f in all_files)
    concatenated_df   = pd.concat(df_from_each_file, ignore_index=True)

    concatenated_df.drop_duplicates(inplace = True)

    concatenated_df.dropna (subset=['DAYS ON MARKET'], inplace=True)

    concatenated_df.rename(columns = {'URL (SEE http://www.redfin.com/buy-a-home/comparative-market-analysis FOR INFO ON PRICING)':\
                   'URL'}, inplace = True)
    concatenated_df.drop_duplicates(subset = ['URL'], inplace=True)

    house_sales_df = concatenated_df.reset_index(drop=True, inplace = False)


    return house_sales_df



def get_property_commentary (soup):
    """
    Take property page soup and return the text description of the property.
    """
    
    commentary = ''
    
    for tag in soup.findAll('div', {'class': 'remarks'}):
        commentary += tag.text.strip()

    return commentary


def average_schools_rating(soup):
    """
    Take redfin BeautifulSoup page and find the average GreatSchools Rating
    of schools serving the home
    """
    total = 0
    count = 0
    
    for tag in soup.findAll('div', {'class': 'rating'}):
        try: 
            rating = int(tag.text.strip())
        except:
            continue
        total += rating
        count += 1
        
    return total / count


def get_property_history (soup):
    """
    From individual property soup page, get 
    a list of dictionaries getting the different property events
    on the page (sales, listings, price, changes, etc.)
    """

    property_history = []
    reg_property_history_row = re.compile('propertyHistory\-[0-9]+')
    
    for row in soup.find_all('tr', attrs={'id': reg_property_history_row}):
        data_cells = row.find_all('td')
        history_data_row = {}
        history_data_row['date'] = data_cells[0].get_text()
        history_data_row['event & source'] = data_cells[1].get_text()
        history_data_row['price'] = data_cells[2].get_text()
        history_data_row['appreciation'] = data_cells[3].get_text()
        property_history.append(history_data_row)
            
    return property_history


def get_list_date_and_price (property_history_list_of_dicts):
    
    """
    Take list of dicts returned from the get_prperty_history method
    and return the list_date and listing price
    """
    
    list_date = "n/a"
    list_price = "n/a"
    
    for hist_dict in property_history_list_of_dicts:
    
        if ('List' or 'list') in hist_dict['event & source']:
            list_date = hist_dict['date']
            #Take string $439,990 and get to right of dollar sign and get rid of comma before int conversion`
            list_price = int(hist_dict['price'].split('$')[1].replace(',',''))
            break
        
        else:
            continue
    
    
    return list_date,list_price


def get_number_of_photos(soup):
    """
    Take property page soup and return count of number of photos in listing
    
    """

    image_count_index = soup.find('div', {'class': 'PagerIndex'}).text.strip()
    
    return int(image_count_index.split('of')[1].strip())


def get_property_page_info (soup):
    
    """
    Take the property page BeautifulSoup soup object and return dictionary with following info for property
    
    Description:  String description of property
    
    Photos:  Int number of photos on the MLS page
    
    List_Date: String listing date
    
    List_Price: Int listing price
    
    School_Rating:  Average Great Schools rating of nearby schools  
    
    """
    
    info_dict = {'Description' : None,
                 'Photos': None,
                 'List_Date': None,
                 'List_Price': None,
                 'School_Rating': None}
    
    try: 
        info_dict['Description'] = get_property_commentary(soup)
        
    except:
        info_dict['Description'] = 'n/a'
        
    
    try:
        info_dict['Photos'] = get_number_of_photos(soup)
        
    except:
        info_dict['Photos'] = 'n/a'
        
    
    try:
        info_dict['List_Date'] , info_dict['List_Price'] = get_list_date_and_price(get_property_history(soup))
        
    except:
        info_dict['List_Date'] = 'n/a'
        info_dict['List_Price'] = 'n/a'   
    
    
    try:
        info_dict['School_Rating'] = average_schools_rating(soup)
        
    except:
        info_dict['School_Rating'] = 'n/a'
        
        
    
    return info_dict




def scrape_property_page_urls (url_list, list_property_page_dicts= []):
    """
    Pass the URL series from the df returned from consolidate_csvs_and_eliminate_duplicates function

    Will use Selenium to go to each URL and get info

    Return list of dicts with dicts in form get_property_info method

    """


    browser = webdriver.Chrome()


    for index, url in enumerate(url_list):
        browser.get(url)
        soup = BeautifulSoup(browser.page_source, 'html.parser')
        list_property_page_dicts.append(get_property_page_info(soup))
        time.sleep(random.choice([0.15,0.25]))

        if index % 500 == 0:
            #if using multiple runs simul, number and changfe in_process_property
            pickle_name = str(index) + '_' + str(random.choice(range(1,100))) + '.p'
            pickle.dump(list_property_page_dicts, open(pickle_name,'wb'))



    return list_property_page_dicts



if __name__ == '__main__':
    pool = Pool(processes=3)              # start 3 worker processes

    

    #path = r'/Users/whetfield/Documents/data_science/metis_dsi/projects/proj5_Kojak/CSV Redfin/Seattle'
    ie_terminal_df = pickle.load(open("ie_terminal_df.p", "rb"))



    #change this on each run from result1,result2
    result4_ie = pool.apply_async(scrape_property_page_urls, [ie_terminal_df['URL'].loc[12000:15600]])
    result5_ie = pool.apply_async(scrape_property_page_urls, [ie_terminal_df['URL'].loc[15601:19583]])
    #result5_ie = pool.apply_async(scrape_property_page_urls, [ie_terminal_df['URL'].loc[8000:11999]])

