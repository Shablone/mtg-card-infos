#%%
import pandas as pd
import requests
import time
import urllib.parse
import numpy as np
import re
from tqdm import tqdm
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
    if pd.isnull(foil): 
        df.at[index, "Foil"] = False

    response = requests.get(url=url)
    time.sleep(0.2) #website requests from sleep times inbetween requests
    response_json = response.json()

    

    if response_json["total_cards"] == 1:
        card = response_json["data"][0]
        card["total_cards"] = response_json["total_cards"]
        return card
    else:
        return {
            "total_cards": response_json["total_cards"],
            "scryfall_uri":url
            }


#%% 
# read csv and parse
df = pd.read_csv("data/cards.csv", header=0)
df["Funde"] =  np.nan
default_edition = "bro"
lang ="de"
responses = []
with tqdm(total=len(df)) as pbar:
    for index, line in df.iterrows():
        edition = line.Edition if not pd.isnull(line.Edition) else default_edition
        number = line.Nummer
        name = line.Karte
        foil = line.Foil

        Info = GetInfoFromScryfall(lang,number,edition,name,foil)

        df.at[index, "Funde"] = int(Info["total_cards"])
        if Info["total_cards"] == 1: 
            df.at[index, "Edition"] = Info["set"]
            df.at[index, "Nummer"] = Info["collector_number"]
            df.at[index, "Karte"] = Info["printed_name"]
            df.at[index, "Seltenheit"] = Info["rarity"]
            df.at[index, "scryfall"] = Info["scryfall_uri"]
        pbar.update(1)

# %% 
# fill price and save to csv
for index, card in df.iterrows():
    Kartenurl = card.Karte.replace("ä", "ae").replace("ö", "oe").replace("ü", "ue").replace("Ä", "Ae").replace("Ö", "Oe").replace("Ü", "Ue").replace("ß", "ss")
    Kartenurl= re.sub('[^0-9a-zA-Z]+', '-', Kartenurl)
    url= f"https://www.trader-online.de/Magic-The-Gathering/Einzelkarten/Deutsch/Krieg-der-Brueder/{Kartenurl}.html"
    df.at[index, "trader"] = url
    response = requests.get(url=url)

    try:
        soup = BeautifulSoup(response.content, "html.parser")
        results = soup.find(class_="price-pre price_product_details")
        df.at[index, "Preis"] = results.text.replace("[","").replace("€","").replace(" ","")
    except Exception:
        df.at[index, "Preis"] = "not found"


    
    time.sleep(0.2)

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
