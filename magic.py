#%%
import pandas as pd
import requests
import time
import json
import urllib.parse
import numpy as np
import re
from bs4 import BeautifulSoup

Editionen = {
    "The Brothers' War":"Krieg-der-Brueder", 
    "The Brothers' War Retro Artifacts":"Krieg-der-Brueder"
    }


#%% read csv and parse
df = pd.read_csv("cards.csv", header=0)
edition = "bro"
lang ="de"
responses = []
for index, line in df.iterrows():
    set = line.Set
    number = line.Nummer
    name = line.Karte
    url = f"https://api.scryfall.com/cards/search?q=lang%3A{lang}+extras%3Atrue"
    if not pd.isnull(number): url += f"+number%3A{number}"
    if not pd.isnull(number): url += f"+set%3A{edition}"
    if not pd.isnull(name): url += f"+name%3A%2F{urllib.parse.quote(name)}%2F"
    df.at[index, "Url"] = url
    responses.append(requests.get(url=url))
    time.sleep(0.2)

#%%
# def print_json_keys(json_obj, level=0):
#     if isinstance(json_obj, dict):
#         for key in json_obj:
#             print("  " * level + key)
#             print_json_keys(json_obj[key], level + 1)
#     elif isinstance(json_obj, list):
#         for item in json_obj:
#             print_json_keys(item, level)
# print_json_keys(val)

# %% search card and fill information
columns = ["Funde", "Edition", "Nummer", "Kartenname", "Foil" "Preis"]
df_filled = pd.DataFrame(columns=columns)
for response in responses:
    val = response.json()
    Funde = len(val["data"])
    Kartenname = val["data"][0]["printed_name"]
    Edition = val["data"][0]["set"]
    Nummer = val["data"][0]["collector_number"]
    #print(f"Anzahl: {Funde} {Kartenname}")
    new_row = pd.DataFrame({"Funde":Funde, "Edition":Edition, "Nummer":Nummer, "Kartenname":Kartenname}, index=[0])
    df_filled = pd.concat([df_filled, new_row], ignore_index=True)
    

# %% fill price and save to csv
for index, card in df_filled.iterrows():
    Kartenurl = card.Kartenname.replace("ä", "ae").replace("ö", "oe").replace("ü", "ue").replace("Ä", "Ae").replace("Ö", "Oe").replace("Ü", "Ue")
    Kartenurl= re.sub('[^0-9a-zA-Z]+', '-', Kartenurl)
    url= f"https://www.trader-online.de/Vorbestellbar/Krieg-der-Brueder-The-Brothers-War/{Kartenurl}.html"
    #print(url)
    response = requests.get(url=url)
    soup = BeautifulSoup(response.content, "html.parser")
    results = soup.find(class_="price-pre price_product_details")
    df_filled.at[index, "Preis"] = results.text.replace("[","").replace("€","").replace(" ","")

    time.sleep(0.2)
df_filled.to_csv("result.csv", sep=";")
# %%
