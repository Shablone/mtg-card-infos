#%%
import pandas as pd
import requests
import time
import urllib.parse
import numpy as np
import re
from tqdm.notebook import tqdm
from bs4 import BeautifulSoup

#%%
Editionen = {
    "The Brothers' War":"Krieg-der-Brueder", 
    "The Brothers' War Retro Artifacts":"Krieg-der-Brueder"
    }

def GetInfoFromScryfall(lang, number, edition, name, foil):

    url = f"https://api.scryfall.com/cards/search?q=lang%3A{lang}+extras%3Atrue"

    if not pd.isnull(number): 
        url += f"+number%3A{number}"
    if edition != "any": 
        url += f"+set%3A{edition}"
    if not pd.isnull(name): 
        url += f"+name%3A%2F{urllib.parse.quote(name)}%2F"

    response = requests.get(url=url)    
    response_json = response.json()

    if response_json["total_cards"] == 1:
        card = response_json["data"][0]
        card["total_cards"] = response_json["total_cards"]
        card["scryfall_api"] = url        
        return card
    else:
        return {
            "total_cards": response_json["total_cards"],
            "scryfall_api":url,
            }

def FillInfoFromScryfall(df, index):
    Info = GetInfoFromScryfall(lang,
        df.at[index,"number"],
        df.at[index,"edition"],
        df.at[index,"cardnameDE"],
        df.at[index,"foil"]
        )
    df.at[index,"Funde"] = int(Info["total_cards"])
    if Info["total_cards"] == 1: 
        df.at[index,"edition"] = Info["set"]
        df.at[index,"number"] = Info["collector_number"]
        df.at[index,"cardnameDE"] = Info["printed_name"]
        df.at[index,"cardnameEN"] = Info["name"]
        df.at[index,"rarity"] = Info["rarity"]
        df.at[index,"scryfall"] = Info["scryfall_uri"]
        df.at[index,"scryfall_api"] = Info["scryfall_api"]        
        df.at[index,"cardmarket"] = (Info["purchase_uris"]["cardmarket"]
            .replace("referrer=scryfall&","")
            .replace("&utm_campaign=card_prices&utm_medium=text&utm_source=scryfall","")
        )
        if pd.isnull(line.foil): df.at[index, "foil"] = False

def GetInfoFromTraderOnline(cardnameDE):
    parsedName = cardnameDE.replace("ä", "ae").replace("ö", "oe").replace("ü", "ue").replace("Ä", "Ae").replace("Ö", "Oe").replace("Ü", "Ue").replace("ß", "ss")
    parsedName= re.sub('[^0-9a-zA-Z]+', '-', parsedName)
    url= f"https://www.trader-online.de/Magic-The-Gathering/Einzelkarten/Deutsch/Krieg-der-Brueder/{parsedName}.html"
    result = {"Traderonline" :url}
    
    response = requests.get(url=url)

    try:
        soup = BeautifulSoup(response.content, "html.parser")
        results = soup.find(class_="price-pre price_product_details")
        result["price"] = results.text.replace("[","").replace("€","").replace(" ","")
    except Exception:
        result["price"] = "not found"     
    return result

def FillInfoFromTraderOnline(df, index):
    Info = GetInfoFromTraderOnline(df.at[index,"cardnameDE"])
    df.at[index,"price_traderonline"] = Info["price"]

def GetInfoFromCardmarket(cardmarket_url, foil):
    foilfilter = "Y" if foil == "True" else "N"
    response = requests.get(url=cardmarket_url)
    url = response.url +(f"?language=3&minCondition=2&isFoil={foilfilter}")
    #cardmarket redirects search to single file. Filters then have to be appended
    df.at[index,"cardmarket"] = url

    response = requests.get(url=cardmarket_url)
    result = {}
    try:
        soup = BeautifulSoup(response.content, "html.parser")
        results = soup.select("#tabContent-info > div > div.col-12.col-lg-6.mx-auto > div > div.info-list-container.col-12.col-md-8.col-lg-12.mx-auto.align-self-start > dl > dd:nth-child(14) > span")
        result["price"] = results[0].text.replace("€","").replace(" ","")
    except Exception:
        result["price"] = "error"     
    return result

def FillInfoFromCardmarket(df, index):
    if pd.isnull(df.at[index,"cardmarket"]):
        df.at[index, "price_cardmarket"] = "url missing"
    else:
        Info = GetInfoFromCardmarket(df.at[index,"cardmarket"], df.at[index,"foil"])
        
        df.at[index,"price_cardmarket"] = Info["price"]



#%% 
# read csv and parse
df = pd.read_csv("data/cards.csv", header=0)
df["Funde"] =  np.nan
default_edition = "bro"
lang ="de"
responses = []

with tqdm(total=len(df)*3) as pbar1:
    for index, line in df.iterrows():
        if pd.isnull(line.edition): df.at[index,"edition"] = default_edition

        FillInfoFromScryfall(df, index)
        pbar1.update(1)
        
        FillInfoFromTraderOnline(df, index)
        pbar1.update(1)
        
        FillInfoFromCardmarket(df, index)
        pbar1.update(1)
        
        #time.sleep(0.2) #websites requests  sleep times inbetween requests
        pbar1.update(1)
            
#%%
df.to_csv("data/result.csv", sep=";", encoding='utf-16')

#%%
def print_json_keys(json_obj, level=0):
    if isinstance(json_obj, dict):
        for key in json_obj:
            print("  " * level + key)
            print_json_keys(json_obj[key], level + 1)
    elif isinstance(json_obj, list):
        for item in json_obj:
            print_json_keys(item, level)
# print_json_keys(val)
# %%
