import requests
import cloudscraper
from bs4 import BeautifulSoup

url = "https://animeflv.net"
scraper = cloudscraper.create_scraper()

class Episode:
    id_: str
    number: int
    url: str

    def __init__(self, id_: str, number: str, url: str):
        self.id_ = id_
        self.number = number
        self.url = url

class Anime:
    id_: str
    title: str
    image: str
    description: str
    type_: str
    valoration: float
    votes: str
    follows: str
    status: str
    genres: list
    episodes: list


    def __init__(self, id_: str, title: str, image: str, description: str, type_: str, valoration: float):
        self.id_ = id_
        self.title = title
        self.image = image
        self.description = description
        self.type_ = type_
        self.valoration = valoration

    def set_info(self):
        page = scraper.get(f"{url}/anime/{self.id_}")
        soup = BeautifulSoup(page.content, "html.parser")

        self.valoration = soup.find(id = "votes_prmd").text
        self.votes = soup.find(id="votes_nmbr").text
        self.follows = soup.find("div", class_="Top").find("div").find("span").text


        response = requests.get(f"https://jimov-api.vercel.app/anime/flv/name/{self.id_}").json()
        
        self.description = response["synopsis"]
        self.status = response["status"]
        self.genres = response["genres"]

        self.episodes = []
        for item in response["episodes"]:
            id_ = item["url"][19:]
            self.episodes.append(
                Episode(
                    id_ = id_,
                    number = id_[len(self.id_) + 1:],
                    url = "",
                )
            )
        self.episodes.reverse()




def get_search(query: str):
    animes = []

    page = scraper.get(f"{url}/browse?q={query}")
    soup = BeautifulSoup(page.content, "html.parser")

    for result in soup.find_all(class_="Anime alt B"):
        secondContainer = result.find(class_="Description").find_all("p")
        animes.append(
            Anime(
                id_ = result.find("a")["href"][7:],
                title = result.find("h3", class_="Title").text,
                image = result.find("img")["src"],
                description = secondContainer[1].text,
                type_ = secondContainer[0].find("span").text,
                valoration = result.find("span", class_="Vts fa-star").text,
            )
        )

    return animes


def get_jimov_link(episode_id: str):
    response = requests.get(f"https://jimov-api.vercel.app/anime/flv/episode/{episode_id}").json()

    for item in response["servers"]:
        if item["name"] == "Our Server":
            return item["file_url"]