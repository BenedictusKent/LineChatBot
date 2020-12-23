from transitions.extensions import GraphMachine
from urllib.request import Request, urlopen
from bs4 import BeautifulSoup as soup
from utils import send_text_message, send_button_carousel

load = 0        # not loaded = 0, loaded = 0
bubble = ""     # previous user input
search = 0      # new search = 0, searched before = 1
link = []       # link to specific title
title = []      # all possible title
img_url = []    # url of images

def variable_reset():
    global load, bubble, search, link, title, img_url
    load = 0
    bubble = ""
    search = 0
    link.clear()
    title.clear()
    img_url.clear()

def anime_search(chat, search_url):
    global link, title, img_url, nothing

    # request to open url
    req = Request(search_url, headers={'User-Agent': 'Mozilla/5.0'})
    client = urlopen(req)
    htmlpage = client.read()
    client.close()
    # parse html and go to article tag
    wholepage = soup(htmlpage, "html.parser")
    articlepage = wholepage.article
    # take useful info
    divs = articlepage.findAll("div", {"class": "list di-t w100"})      # num of searches
    for div in divs:
        second = div.find("div", {"class": "information di-tc va-t pt4 pl8"})
        title.append(second.a.text.strip())
        link.append(second.a["href"])
    # better picture of filtered search
    for i in range(len(title)):
        req = Request(link[i], headers={'User-Agent': 'Mozilla/5.0'})
        client = urlopen(req)
        htmlpage = client.read()
        client.close()
        specific = soup(htmlpage, "html.parser")
        imgtag = specific.find("img", {"alt": title[i]})
        img_url.append(str(imgtag["data-src"]))

class TocMachine(GraphMachine):
    def __init__(self, **machine_configs):
        self.machine = GraphMachine(model=self, **machine_configs)

# =================================================================
# Exit state

    def is_going_to_quit(self, event):
        text = event.message.text
        return text.lower() == "quit"

    def on_enter_quit(self, event):
        print("Enter quit stage")
        reply_token = event.reply_token
        send_text_message(reply_token, "End")
        self.go_back()

# =================================================================
# Update state

    def is_going_to_update(self, event):
        text = event.message.text
        return text.lower() == "update"

    def on_enter_update(self, event):
        print("Enter update state")
        reply_token = event.reply_token
        send_text_message(reply_token, "Type in anime you want to look up")

# =================================================================
# Title state

    def is_going_to_title(self, event):
        text = event.message.text
        return True

    def on_enter_title(self, event):
        text = event.message.text

        if(text.lower() == "back"):
            reply_token = event.reply_token
            send_text_message(reply_token, "Back to main")
            self.go_back()
        else:
            url = text.lower().replace(" ", "%20")
            search_url = "https://myanimelist.net/search/all?q=" + url + "&cat=all"
            
            # check if user input has been checked previously
            global search, title, load, link, img_url, bubble
            if not bubble:
                bubble = str(text.lower())
            else:
                if(bubble == text.lower()):
                    load = 0
                    search = 1
                else:
                    variable_reset()
                    bubble = str(text)
            print(search)
            
            # search in MyAnimeList.net
            if(search == 0):
                anime_search(bubble, search_url)
                search = 1
            
            userid = event.source.user_id
            send_button_carousel(userid, bubble, img_url, title, link, load)

# =================================================================
# Repeat state

    def is_going_to_repeat(self, event):
        text = event.message.text
        return text.lower() == "repeat"

    def on_enter_repeat(self, event):
        print("Enter repeat stage")
        reply_token = event.reply_token
        send_text_message(reply_token, "repeating")


# =================================================================
# load_more state

    def is_going_to_load(self, event):
        text = event.message.text
        return text.lower() == "more"

    def on_enter_load(self, event):
        global bubble, img_url, title, link, load
        load = 1

        userid = event.source.user_id
        send_button_carousel(userid, bubble, img_url, title, link, load)