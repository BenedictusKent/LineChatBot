from transitions.extensions import GraphMachine
from urllib.request import Request, urlopen
from bs4 import BeautifulSoup as soup
from utils import send_text_message, send_button_carousel, send_button_message

load = 0        # not loaded = 0, loaded = 0
bubble = ""     # previous user input
search = 0      # new search = 0, searched before = 1
interest = 0    # which anime title the user interested in [start at 1]
link = []       # link to specific title
info = []       # info for specific anime title
title = []      # all possible title
img_url = []    # url of images

upcoming_title = []
upcoming_link = []
upcoming_load = 0

def variable_reset():
    global load, bubble, search, link, title, img_url
    load = 0
    bubble = ""
    search = 0
    link.clear()
    info.clear()
    title.clear()
    img_url.clear()

def anime_search(chat, search_url):
    global link, title, img_url, nothing

    # request to open url
    req = Request(search_url, headers={'User-Agent': 'Mozilla/5.0'})
    client = urlopen(req)
    htmlpage = client.read()
    client.close()
    # parse html and take useful info
    wholepage = soup(htmlpage, "html.parser")
    divs = wholepage.findAll("div", {"class": "information di-tc va-t pt4 pl8"})      # num of searches
    for i in range(len(divs)):
        title.append(divs[i].a.text.strip())
        link.append(divs[i].a["href"])
    # better picture of filtered search
    for i in range(len(title)):
        req = Request(link[i], headers={'User-Agent': 'Mozilla/5.0'})
        client = urlopen(req)
        htmlpage = client.read()
        client.close()
        specific = soup(htmlpage, "html.parser")
        imgtag = specific.find("img", {"alt": title[i]})
        img_url.append(str(imgtag["data-src"]))

def anime_info():
    global link, interest

    # request to open url
    req = Request(link[interest], headers={'User-Agent': 'Mozilla/5.0'})
    client = urlopen(req)
    htmlpage = client.read()
    client.close()
    # parse html and take all info
    wholepage = soup(htmlpage, "html.parser")
    left = wholepage.find("div", {"style": "width: 225px"})
    for spantag in left.findAll("span", {"class": "dark_text"}):
        info.append(str(spantag.text.strip()))
        temp = str(spantag.next_sibling.strip())
        if temp:
            info.append(temp)

def anime_upcoming():
    global upcoming_title, upcoming_link

    search_url = "https://myanimelist.net/topanime.php?type=upcoming"
    # request to open url
    req = Request(search_url, headers={'User-Agent': 'Mozilla/5.0'})
    client = urlopen(req)
    htmlpage = client.read()
    client.close()
    # parse html and take useful info
    wholepage = soup(htmlpage, "html.parser")
    a = wholepage.findAll("a", {"class": "hoverinfo_trigger fl-l ml12 mr8"})
    for i in range(len(a)):
        upcoming_link.append(a[i]["href"])
        upcoming_title.append(a[i].img["alt"].replace("Anime: ", ""))

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
# Search state

    def is_going_to_search(self, event):
        text = event.message.text
        return text.lower() == "search"

    def on_enter_search(self, event):
        print("Enter search state")
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
        send_text_message(reply_token, "Type in anime you want to look up")

# =================================================================
# load_more state

    def is_going_to_load(self, event):
        text = event.message.text
        return text.lower() == "more" or text.lower() == "load"

    def on_enter_load(self, event):
        global bubble, img_url, title, link, load
        load = 1

        userid = event.source.user_id
        send_button_carousel(userid, bubble, img_url, title, link, load)

# =================================================================
# goto info state

    def is_going_to_repeatinfo(self, event):
        text = event.message.text
        return text.lower() == "info"

    def on_enter_repeatinfo(self, event):
        global interest
        print("Enter repeat info stage")
        command = "Type " + str(interest) + " to go back to info state"
        reply_token = event.reply_token
        send_text_message(reply_token, command)

# =================================================================
# info state

    def is_going_to_info(self, event):
        global interest
        text = event.message.text
        interest = int(text)
        return text.isdigit() and interest < 10

    def on_enter_info(self, event):
        global interest, img_url, title
        label = ["Synopsis", "Status", "Schedule"]
        chat = ["synopsis", "status", "schedule"]
        image = img_url[interest]
        name = title[interest]
        userid = event.source.user_id
        send_button_message(userid, image, name, label, chat)

# =================================================================
# synopsis state

    def is_going_to_synopsis(self, event):
        text = event.message.text
        return text.lower() == "synopsis"

    def on_enter_synopsis(self, event):
        global interest, link
        req = Request(link[interest], headers={'User-Agent': 'Mozilla/5.0'})
        client = urlopen(req)
        htmlpage = client.read()
        client.close()
        wholepage = soup(htmlpage, "html.parser")
        paragraph = wholepage.find("p", {"itemprop": "description"})
        paragraph = paragraph.text
        reply_token = event.reply_token
        send_text_message(reply_token, paragraph)

# =================================================================
# schedule state

    def is_going_to_schedule(self, event):
        text = event.message.text
        return text.lower() == "schedule"

    def on_enter_schedule(self, event):
        global interest, link, info

        # if info not searched before, then search
        if not info:
            anime_info()

        # look for appropriate item
        sched = "No data found"
        for i in range(len(info)):
            if(info[i] == "Broadcast:"):
                sched = info[i+1]
                break

        # message
        reply_token = event.reply_token
        send_text_message(reply_token, sched)

# =================================================================
# status state

    def is_going_to_status(self, event):
        text = event.message.text
        return text.lower() == "status"

    def on_enter_status(self, event):
        global interest, link, info

        # if info not searched before, then search
        if not info:
            anime_info()

        # look for appropriate item
        for i in range(len(info)):
            if(info[i] == "Status:"):
                if ":" in info[i+1]:
                    status = "No data found"
                else:
                    status = info[i+1]
                break

        # message
        reply_token = event.reply_token
        send_text_message(reply_token, status)

# =================================================================
# top upcoming state

    def is_going_to_upcoming(self, event):
        text = event.message.text
        return text.lower() == "upcoming"

    def on_enter_upcoming(self, event):
        global upcoming_title, upcoming_load

        # search if not searched before
        if(upcoming_load == 0):
            anime_upcoming()
            upcoming_load = 1

        # show 10 titles each time and restart if reached the end
        text = ""
        number = upcoming_load
        if(number >= 50):
            number = 1
            upcoming_load = 1
        if(number < 50):
            end = number * 10
            start = end - 10
            for i in range(start, end):
                text += str(number) + ". " + upcoming_title[i]
                if(i < end-1):
                    text += "\n"
                number += 1
            upcoming_load += 1

        # message
        reply_token = event.reply_token
        send_text_message(reply_token, text)