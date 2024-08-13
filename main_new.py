import os
import re
import json
import subprocess
import requests
from bs4 import BeautifulSoup
from HdRezkaApi import HdRezkaApi
from mirror_update import update_mirror

# Load settings
global search_result
settings = json.load(open("settings.json", "r"))
URL = settings["mirror_link"]
HEADERS = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/81.0.4044.138 Safari/537.36'}

def search(query):
    """Search on HDrezka, using autocomplete search URL"""
    global URL
    try:
        response = requests.post(f'https://{URL}/engine/ajax/search.php', data={'q': query}, headers=HEADERS, timeout=100)
        parsed_html = BeautifulSoup(response.text, 'lxml')
        results = {"URL": [], "Name": [], "Year": [], "Rating": []}

        for i, link in enumerate(parsed_html.find_all('a'), start=1):
            try:
                url = link.get('href')
                name = link.find_all('span')[0].get_text()
                year = re.search("-[0-9]{4}", url).group().replace("-", "")
                rating = link.find_all('span')[1].get_text()
                
                print(f"{i}. | URL: {url}\n | Name: {name}\n | Year: {year}\n | Rating: {rating}\n{'-'*84}")
                
                results["URL"].append(url)
                results["Name"].append(name)
                results["Year"].append(year)
                results["Rating"].append(rating)
            except IndexError:
                break
        return results
    except (requests.exceptions.SSLError, requests.exceptions.ConnectionError):
        print("\033[1;31;91m Got SSLError, probably mirror is invalid. Trying to get new... \033[1;31;91m")
        if update_mirror():
            URL = json.load(open("settings.json", "r"))["mirror_link"]
        else:
            print("\033[1;31;91m Error while updating mirror link! Seems like problem with HDrezka \033[1;31;91m")
        return None

def select_translation(translations):
    """Select a translation from the available options"""
    for i, (tr_name, _) in enumerate(translations.items(), start=1):
        print(f"{i}. | {tr_name}")
    choice = int(input("Select translation, please: "))
    tr_name = list(translations.keys())[choice - 1]
    return tr_name, translations[tr_name]

def select_resolution(streams):
    """Select a resolution from available streams"""
    for i, res in enumerate(streams.videos.keys(), start=1):
        print(f"{i}. | {res}")
    return int(input("Select resolution, please: "))

def action(user_input, url, name):
    """Main user actions"""
    if user_input.lower() == "p":
        subprocess.call(['mpv', url])
    elif user_input.lower() == "d":
        os.system(f'wget -c -O "{name}.mp4" {url}')
    elif user_input.lower() == "l":
        print(f"URL: \n{url}")

def handle_film(rezka, film_data):
    """Handle film selection and actions"""
    translations = rezka.getTranslations()
    tr_name, tr_index = select_translation(translations)
    streams = rezka.getStream('1', '1', tr_index)
    res_index = select_resolution(streams)
    stream = list(streams.videos.values())[res_index - 1].split(":hls")[0]
    filename = f'{film_data["name"]}-{film_data["year"]}'
    action(input("What would you do [P]lay, [D]ownload or [L]ist: "), stream, filename)

def handle_tv_series(rezka, series_data):
    """Handle TV series selection and actions"""
    global search_result
    translations = rezka.getTranslations()
    tr_name, tr_index = select_translation(translations)
    getseasons = rezka.getSeasons()
    seasons = getseasons[tr_name]['seasons']
    episodes = getseasons[tr_name]['episodes']
    for i, season in enumerate(seasons.keys(), start=1):
        print(f"{i}. | Season {season}")
    season_num = input("Select season, please: ")

    for i, episode in enumerate(episodes.keys(), start=1):
        print(f"{i}. | Episode {episode}")
    episode_num = input("Select episode(s), please: ")

    filename = f'{series_data["name"]}-{series_data["year"]}-S{season_num}-E{episode_num}'
    dirname = f'{series_data["name"]}-{series_data["year"]}'
    if not os.path.isdir(dirname):
        os.mkdir(dirname)
    if episode_num.__contains__("-"):
        res = rezka.getStream(season_num, episode_num.split('-')[0], tr_index)
        res_index = select_resolution(res)
        for episode in range(int(episode_num.split('-')[0]),int(episode_num.split('-')[1])+1):        
            res = rezka.getStream(season_num, episode, tr_index)
            stream = list(res.videos.values())[res_index - 1].split(":hls")[0]
            filename = f'{series_data["name"]}-{series_data["year"]}-S{season_num}-E{episode}'
            action("d", stream, f"{dirname}/{filename}")
    else:
        res = rezka.getStream(season_num, episode_num, tr_index)
        res_index = select_resolution(res)
        stream = list(res.videos.values())[res_index - 1].split(":hls")[0]
        action(input("What would you do [P]lay, [D]ownload or [L]ist: "), stream, f"{dirname}/{filename}")

def main():
    while True:
        query = input("Enter search words: ")
        search_result = search(query)
        if search_result:
            break
        else:
            print("No results")

    choice = int(input("Select film, please: "))
    rezka = HdRezkaApi(search_result["URL"][choice - 1])
    item_data = {
        "name": search_result["Name"][choice-1].replace("/", "|"),
        "year": search_result["Year"][choice-1]
    }
    if rezka.type == "video.movie":
        handle_film(rezka, item_data)
    elif rezka.type == "video.tv_series":
        handle_tv_series(rezka, item_data)

if __name__ == "__main__":
    main()
