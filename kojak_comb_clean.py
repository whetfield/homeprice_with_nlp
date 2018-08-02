"""
Combining scraping results and cleaning for Project Kojak at Metis Data Science Immersive.
Non - real estate portal websites / cleaning
"""
import pandas as pd
import numpy as np
import glob
import os
from bs4 import BeautifulSoup
import re
from selenium import webdriver
import selenium
import time
import random
import pickle
import requests


def adding_scraped_columns_to_df (city_df, scraped_list_of_dicts):
    
    """
    Create new columns in dataframe for the scraped data from site
    """
    
    for key in ['Description','List_Date','List_Price','Photos','School_Rating']:
        city_df[key] = [entry[key] for entry in scraped_list_of_dicts]
    
    return city_df


def add_datetimes_and_saletime (city_df):

    """
    Add columns for pandas datetime for list and sale date, and days to sell

    Return the new dataframe

    """
    
    #Need to drop entries where couldn't get list_date

    city_df = city_df.loc[city_df['List_Date'] != 'n/a' , :]
    city_df.reset_index(drop= True, inplace= True)

    #Make current list and sale date strings pandas datetimes
    modified_list_date = pd.to_datetime(city_df['List_Date'], format= '%b %d, %Y')
    modified_sale_date = pd.to_datetime(city_df['SOLD DATE'])

    city_df.loc[ : ,'List_Date'] = modified_list_date
    city_df.loc[ : ,'SOLD DATE'] = modified_sale_date
    
    city_df.loc[ : , 'Sale_Time'] = city_df.loc[: ,'SOLD DATE'] - city_df.loc[ :,'List_Date']

    return city_df


def cleaning_after_saletime_added(city_df):
    """
    Cleaning up dataframe adfter the modified saletime added

    Dropping and non- Single Family Residential transaction types
    Dropping entries with NaN

    Casting Zip Codes to int rather than float
    """

    #Get rid of definitely unnecessary columns
    columns = ['NEXT OPEN HOUSE START TIME','NEXT OPEN HOUSE END TIME',
                'FAVORITE', 'DAYS ON MARKET', 'INTERESTED']

    city_df = city_df.drop(labels= columns, axis=1, inplace=False)


    #Drop any entries with NaN in key columns
    key_columns = ['SOLD DATE', 'ZIP', 'PRICE', 'SQUARE FEET', 'YEAR BUILT',
                'LATITUDE', 'LONGITUDE', 'PROPERTY TYPE']
    city_df = city_df.dropna(subset= key_columns, inplace= False, how= 'any')



    #Get rid of any non single family residential homes
    city_df = city_df.loc[city_df['PROPERTY TYPE'] == 'Single Family Residential' , :]
    
    #Get rid of any where Photos or School Rating not available
    city_df = city_df.loc[city_df['Photos'] != 'n/a' , :]
    city_df = city_df.loc[city_df['School_Rating'] != 'n/a' , :]

   
    #Cast Zip codes to integers
    city_df.loc[:,'ZIP'] = pd.to_numeric(city_df['ZIP'],errors='coerce')
    city_df.loc[:,'ZIP'] = city_df['ZIP'].apply(int)


    city_df.reset_index(drop= True, inplace= True)

    return city_df

def get_zipcode_demo_data (zip_code_list):

    """
    Scrape city_data for demographic info for zip codes passed

    Return five lists of different demographics
    """

    income_list=[]
    population_list=[]
    ba_list=[]
    grad_list =[]
    married_list=[]

    for z in zip_code_list:
        #print("http://www.city-data.com/zips/"+z)
        #print(z)
        z = str(z)
        response=requests.get("http://www.city-data.com/zips/"+z+".html")
        
        if(response.status_code==200):

            soup = BeautifulSoup(response.text, "html.parser")
            income = soup.find("b", text=re.compile("^Estimated median household income in 2016:"))
            population = soup.find("b", text=re.compile("^Estimated zip code population in 2016:"))
            ba = soup.find("b", text=re.compile("^Bachelor's degree or higher:"))
            grad = soup.find("b", text=re.compile("^Graduate or professional degree:"))
            married = soup.find("b", text=re.compile("^Now married:"))


            income_list.append(income.next_sibling.next_element.text)
            population_list.append(population.next_sibling)
            ba_list.append(ba.next_sibling)
            grad_list.append(grad.next_sibling)
            married_list.append(married.next_sibling)

        else:
            #print("oops")
            income_list.append("oops$")
            population_list.append(",")
            ba_list.append(",")
            grad_list.append(",")
            married_list.append(",")
            
            
    return income_list, population_list, ba_list, grad_list, married_list


def make_demographic_dictionary (zip_code_list, income_list,population_list,ba_list,grad_list,married_list):
    """
    Take demographic lists from get_zipcode_demo_data function and return dictinaries with zip_code keys amd 
    demographic values
    """


    income_list =[i.split("$")[1].replace(',',"") for i in income_list]
    population_list =[i.strip().replace(',',"") for i in population_list]
    ba_list = [i.strip().replace('%',"") for i in ba_list]
    grad_list = [i.strip().replace('%',"") for i in grad_list]
    married_list = [i.strip().replace('%',"") for i in married_list]
    
    
    
    income_dict = {zip_code: income for zip_code, income in zip(zip_code_list,income_list)}
    population_dict = {zip_code: population for zip_code, population in zip(zip_code_list,population_list)}
    ba_dict = {zip_code: ba for zip_code, ba in zip(zip_code_list,ba_list)}
    grad_dict = {zip_code: grad for zip_code, grad in zip(zip_code_list,grad_list)}
    married_dict = {zip_code: marriage for zip_code, marriage in zip(zip_code_list,married_list)}
    
    
    return income_dict, population_dict, ba_dict, grad_dict, married_dict


def make_numeric_demo_arrays (city_df, demo_dict):
    """
    For every entry in the dataframe, created an array with
    the appropriate demographic value for the transactions zip code
    """
    
    value_list = []
    for code in city_df['ZIP']:
        try:
            value_list.append(np.float(demo_dict[code]))
        except:
            value_list.append(np.NaN)
            
    return value_list


def add_regional_identifier (city_df, seattle = 0, san_diego = 0, la_area = 0):
    """
    Must set keyword arguments appropriately
    
    Add to city_dataframe columns of 1's for area download and column of zeroes
    for area not from.  
        
    """
    
    city_df['Seattle_Area'] = seattle
    city_df['San_Diego_Area'] = san_diego
    city_df['LA_Area'] = la_area
    
    return city_df


def combine_dataframes (city_df_list):
    """
    For all the city_dataframes passed, combine into a single dataframe,
    shuffle the entries, reset_the index
    """
    
    combined_dataframe = pd.concat(city_df_list, ignore_index = True)
    
    combined_dataframe = combined_dataframe.sample(frac=1).reset_index(drop=True)
    
    return combined_dataframe




def additional_features_to_base_df (city_combined_df):
    """
    Add some additional features to the combined df returnd from combine_dataframes 
    function 
    """

    city_combined_df['Log_Price'] = city_combined_df['PRICE'].apply(np.log)
    city_combined_df['$/SQUARE FEET'] = city_combined_df['PRICE'] / city_combined_df['SQUARE FEET']
    city_combined_df['Home_sqft_per_lot_sqft'] = city_combined_df['SQUARE FEET'] / city_combined_df['LOT SIZE']
    city_combined_df['Age_of_House'] = 2018.25 - city_combined_df['YEAR BUILT']
    city_combined_df['Sale_Time_Float'] = city_combined_df['Sale_Time'].astype('timedelta64[D]')

    # Create a list for number of comps a property has, defined as sold within 6 months prior of listing
    # List for average price per square foot of those comps
    # Loop to find
    
    past_comps_list = []
    average_price_per_sq_ft_comps = []
    
    for index, entry in city_combined_df.iterrows():
        mask = (city_combined_df['ZIP'] == entry['ZIP']) & (city_combined_df['SOLD DATE'] < entry['List_Date'])\
                                                    & (city_combined_df['SOLD DATE'] > (entry['List_Date'] - pd.Timedelta(days=180)))
         
        try:
            past_comp_count = mask.value_counts().loc[True]
        except:
            past_comp_count = 0

        past_comps_list.append(past_comp_count)         

        #Subset datafrane based on comps mask in order to get the average price pe square foot of comps
        comps_df = city_combined_df[mask]
        average_price_per_sq_ft_comps.append(np.mean(comps_df['$/SQUARE FEET']))


    city_combined_df["Prior_6_months_comps"] = past_comps_list
    city_combined_df['Comps_$_Square_Foot'] = average_price_per_sq_ft_comps
    city_combined_df['Price_Based_on_Comps'] = city_combined_df['Comps_$_Square_Foot'] * city_combined_df['SQUARE FEET']

    #If no Comps divide by zero, these were essentially too early in the data set
    city_combined_df.dropna(subset=['Price_Based_on_Comps'], inplace = True)
    city_combined_df = city_combined_df[city_combined_df['Price_Based_on_Comps'] != np.inf]

    #Visual Inspection of some outliers, "fat finger errors", wrong square footage (ie 1 square foot home)
    
    city_combined_df.loc[25548,'PRICE'] = 572500.0
    city_combined_df.drop([11787], inplace= True) #Seems like ok record, thought had only 1 in total sqaure footage
    #city_combined_df.drop([8075], inplace = True)
    city_combined_df.loc[27940,'PRICE'] = 273000.0
    city_combined_df.loc[25263,'PRICE'] = 575000.0
    city_combined_df.loc[12674,'PRICE'] = 325000.0
    city_combined_df.loc[7019,'PRICE'] = 430000.0
    
    #Hundreds of Millions, wrong prices, has 23839 has a $10k price, obviously wrong
    city_combined_df.drop([23221], inplace= True)
    city_combined_df.drop([29106], inplace= True)
    city_combined_df.drop([23839], inplace= True)
    
    
    #No Square Footage for unit
    city_combined_df.drop([15669], inplace= True)

    #city_combined_df.drop([2423], inplace = True)
    #city_combined_df.drop([1620], inplace = True)

    #Eliminate Homes with negative listing time, have been relisted since sold recently
    city_combined_df = city_combined_df[city_combined_df['Sale_Time_Float'] > 0]

    #Eliminate Homes with negative age, year built was greater than 2018
    city_combined_df = city_combined_df[city_combined_df['Age_of_House'] > 0]


    return city_combined_df


def add_case_shiller (city_combined_df, path_caseshiller_csv):
    """
    Add 20-City time series index value.  Based on the list date, look 85 days
    back to get the month-year value of the index to pull.  IE, the January 2018
    Index value was not available until March 27, 2018
    """

    #Get lagged dates based on Home Listing Date which correspond to appropriate
    #Index Value month datee.  85 days comes from January 2018 being available
    # March 27,2018. So March 26, would be in December and pull December index value
    #Note using List_Date as well, not sale date, so being conservative in what 
    #Data will be available 
    
    index_date_series = city_combined_df.List_Date - pd.Timedelta(days=85)

    #Import CSV with case_shiller values and do some basic cleaning
    cs_df = pd.read_csv(path_caseshiller_csv)
    cs_df = cs_df.loc[1: , ['Unnamed: 1', 'Unnamed: 2']]
    cs_df.columns = ['Date','Value']


    #Get a list of values 
    case_shiller_entries = []

    for date in index_date_series:
        case_shiller_entries.append(float(cs_df.loc[cs_df.Date == date.strftime('%b-%Y'), 'Value'].iloc[0]))


    city_combined_df['Lagged_Case_Shiller_Index'] = case_shiller_entries

    return city_combined_df










        
        








