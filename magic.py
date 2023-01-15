#%%
import pandas as pd
import requests
import time
import urllib.parse
import numpy as np
import re
from bs4 import BeautifulSoup

#%%
Editionen = {
    "The Brothers' War":"Krieg-der-Brueder", 
    "The Brothers' War Retro Artifacts":"Krieg-der-Brueder"
    }

def GetInfo(url):
    response = requests.get(url=url)
    time.sleep(0.2)
    response_json = response.json()
    if not "total_cards" in response_json:
        Funde = -999
    else:
        Funde = response_json["total_cards"]
    if Funde == 1:
        Kartenname = response_json["data"][0]["printed_name"]
        Edition = response_json["data"][0]["set"]
        Nummer = response_json["data"][0]["collector_number"]
    else:
        Kartenname= "?"
        Edition = "?"
        Nummer = "?"
    return {"Funde":Funde, "Edition":Edition, "Nummer":Nummer, "Kartenname":Kartenname}


#%% 
# read csv and parse
df = pd.read_csv("cards.csv", header=0)
df["Funde"] =  np.nan
default_edition = "bro"
lang ="de"
responses = []
for index, line in df.iterrows():
    edition = line.Edition if not pd.isnull(line.Edition) else default_edition
    number = line.Nummer
    name = line.Karte

    url = f"https://api.scryfall.com/cards/search?q=lang%3A{lang}+extras%3Atrue"
    if not pd.isnull(number): url += f"+number%3A{number}"
    if edition != "any": url += f"+set%3A{edition}"
    if not pd.isnull(name): url += f"+name%3A%2F{urllib.parse.quote(name)}%2F"
    if pd.isnull(line.Foil): df.at[index, "Foil"] = False
    df.at[index, "scryfall"] = url
    Info = GetInfo(url)

    df.at[index, "Funde"] = int(Info["Funde"])
    if Info["Funde"] == 1: 
        df.at[index, "Edition"] = Info["Edition"]
        df.at[index, "Nummer"] = Info["Nummer"]
        df.at[index, "Karte"] = Info["Kartenname"]

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
        df.at[index, "Preis"] = "err"


    
    time.sleep(0.2)

df.to_csv("result.csv", sep=";", encoding='utf-16')
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
