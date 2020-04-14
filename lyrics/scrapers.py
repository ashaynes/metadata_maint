from bs4 import BeautifulSoup
import requests

def scrape(source, url):
    lyrics = str()
    soup = BeautifulSoup(requests.get(url).content, "lxml")
        
    if source == "MetroLyrics":
        verses = soup.find_all("p", {"class": "verse"})
        for verse in verses:
            lyrics += verse.text+"\n\n"

    elif source == "Genius":
        lyrics = soup.select("p")[0].text
        
    else:
        print ("Not a valid lyrics source passed")

    return lyrics