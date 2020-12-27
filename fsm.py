from transitions.extensions import GraphMachine
from urllib.request import Request, urlopen
from urllib.parse import quote, unquote
from bs4 import BeautifulSoup as soup
from utils import send_text_message, send_button_carousel, send_button_message

load = 0                # not loaded = 0, loaded = 0
bubble = ""             # previous user input
search = 0              # new search = 0, searched before = 1
interest = 0            # which anime title the user interested in [start at 1]
link = []               # link to specific title
info = []               # info for specific anime title
title = []              # all possible title
img_url = []            # url of images
from_search = -1

upcoming_title = []
upcoming_link = []
upcoming_info = []
upcoming_more = 0
upcoming_interest = -1
from_upcoming = -1

news_title = []
news_clip = []
news_link = []
news_more = -1

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
        name = divs[i].a.text.strip()
        temp = quote(name.encode("unicode-escape"))
        temp = unquote(temp)
        title.append(temp)

        url = divs[i].a["href"]
        temp = quote(url.encode("unicode-escape"))
        temp = unquote(temp)
        link.append(temp)
    # better picture of filtered search
    for i in range(len(title)):
        req = Request(link[i], headers={'User-Agent': 'Mozilla/5.0'})
        client = urlopen(req)
        htmlpage = client.read()
        client.close()
        specific = soup(htmlpage, "html.parser")
        imgtag = specific.find("img", {"alt": title[i]})
        img_url.append(str(imgtag["data-src"]))

def anime_info(search_url):
    global from_upcoming, from_search
    # request to open url
    req = Request(search_url, headers={'User-Agent': 'Mozilla/5.0'})
    client = urlopen(req)
    htmlpage = client.read()
    client.close()
    # parse html and take all info
    wholepage = soup(htmlpage, "html.parser")
    left = wholepage.find("div", {"style": "width: 225px"})
    if(from_search == 1):
        global info
        for spantag in left.findAll("span", {"class": "dark_text"}):
            info.append(str(spantag.text.strip()))
            temp = str(spantag.next_sibling.strip())
            if temp:
                info.append(temp)
    elif(from_upcoming == 1):
        global upcoming_info
        for spantag in left.findAll("span", {"class": "dark_text"}):
            upcoming_info.append(str(spantag.text.strip()))
            temp = str(spantag.next_sibling.strip())
            if temp:
                upcoming_info.append(temp)

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

def anime_news():
    global news_clip, news_link, news_title
    # request to open url
    req = Request("https://myanimelist.net/", headers={'User-Agent': 'Mozilla/5.0'})
    client = urlopen(req)
    htmlpage = client.read()
    client.close()
    # parse html and go to article tag
    wholepage = soup(htmlpage, "html.parser")
    newspage = wholepage.findAll("div", {"class": "news-unit clearfix"})
    for i in range(len(newspage) - 4):
        # find h3
        h = newspage[i].find("h3", {"class": "title news_h3"})
        news_link.append(h.a["href"])
        news_title.append(h.a.text.strip())
        # find p
        p = newspage[i].find("p")
        news_clip.append(p.text.strip())

class TocMachine(GraphMachine):
    def __init__(self, **machine_configs):
        self.machine = GraphMachine(model=self, **machine_configs)

# =================================================================
# Search state

    def is_going_to_search(self, event):
        text = event.message.text
        global from_search, from_upcoming
        from_search = 1
        from_upcoming = -1
        return text.lower() == "search" or text.lower() == "quit"

    def on_enter_search(self, event):
        text = event.message.text

        if(text.lower() == "quit"):
            reply_token = event.reply_token
            send_text_message(reply_token, "Back to main")
            self.go_back()
        elif(text.lower() == "search"):
            #print("Enter search state")
            reply_token = event.reply_token
            send_text_message(reply_token, "Type in anime you want to look up")

# =================================================================
# Title state

    def is_going_to_title(self, event):
        text = event.message.text
        return True

    def on_enter_title(self, event):
        text = event.message.text

        if(text.lower() == "quit"):
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
        return text.lower() == "repeat" or text.lower() == "quit"

    def on_enter_repeat(self, event):
        text = event.message.text

        if(text.lower() == "quit"):
            reply_token = event.reply_token
            send_text_message(reply_token, "Back to main")
            self.go_back()
        elif(text.lower() == "repeat"):
            #print("Enter repeat stage")
            reply_token = event.reply_token
            send_text_message(reply_token, "Type in anime you want to look up")

# =================================================================
# load_more state

    def is_going_to_load(self, event):
        text = event.message.text
        return text.lower() == "more" or text.lower() == "load" or text.lower() == "quit"

    def on_enter_load(self, event):
        text = event.message.text

        if(text.lower() == "quit"):
            reply_token = event.reply_token
            send_text_message(reply_token, "Back to main")
            self.go_back()
        else:
            global bubble, img_url, title, link, load
            if(load == 0):
                load = 1
            else:
                load = 0

            userid = event.source.user_id
            send_button_carousel(userid, bubble, img_url, title, link, load)

# =================================================================
# goto info state

    def is_going_to_repeatinfo(self, event):
        text = event.message.text
        return text.lower() == "info" or text.lower() == "quit"

    def on_enter_repeatinfo(self, event):
        text = event.message.text

        if(text.lower() == "quit"):
            reply_token = event.reply_token
            send_text_message(reply_token, "Back to main")
            self.go_back()
        elif(text.lower() == "info"):
            global interest, upcoming_interest, from_search, from_upcoming
            #print("Enter repeat info stage")
            if(from_search == 1):
                command = "Type " + str(interest) + " to go back to info state"
            elif(from_upcoming == 1):
                command = "Type " + str(upcoming_interest) + " to go back to info state"
            reply_token = event.reply_token
            send_text_message(reply_token, command)

# =================================================================
# info state

    def is_going_to_info(self, event):
        global interest, from_upcoming, upcoming_interest, from_search
        text = event.message.text
        if(text.lower() != "quit"):
            if(from_upcoming == 1):
                upcoming_interest = int(text)
            elif(from_search == 1):
                interest = int(text)
        return (text.isdigit() and interest < 10) or text.lower() == "quit"

    def on_enter_info(self, event):
        global from_upcoming, from_search
        text = event.message.text

        if(text.lower() == "quit"):
            reply_token = event.reply_token
            send_text_message(reply_token, "Back to main")
            self.go_back()
        else:
            label = ["Synopsis", "Release","Status","Schedule"]
            chat = ["synopsis", "release","status", "schedule"]
            if(from_upcoming == 1):
                global upcoming_title, upcoming_link, upcoming_interest
                url = upcoming_link[upcoming_interest]
                url = quote(url.encode("unicode-escape"))
                url = unquote(url)
                req = Request(url, headers={'User-Agent': 'Mozilla/5.0'})
                client = urlopen(req)
                htmlpage = client.read()
                client.close()
                wholepage = soup(htmlpage, "html.parser")
                div = wholepage.find("div", {"style": "text-align: center;"})
                image = div.a.img["data-src"]
                name = upcoming_title[upcoming_interest]
                userid = event.source.user_id
                send_button_message(userid, image, name, label, chat)
            elif(from_search == 1):
                global interest, img_url, title
                image = img_url[interest]
                name = title[interest]
                userid = event.source.user_id
                send_button_message(userid, image, name, label, chat)

# =================================================================
# synopsis state

    def is_going_to_synopsis(self, event):
        text = event.message.text
        return text.lower() == "synopsis" or text.lower() == "quit"

    def on_enter_synopsis(self, event):
        text = event.message.text

        if(text.lower() == "quit"):
            reply_token = event.reply_token
            send_text_message(reply_token, "Back to main")
            self.go_back()
        elif(text.lower() == "synopsis"):
            global from_upcoming, from_search
            if(from_upcoming == 1):
                global upcoming_link, upcoming_interest
                url = upcoming_link[upcoming_interest]
                req = Request(url, headers={'User-Agent': 'Mozilla/5.0'})
                client = urlopen(req)
                htmlpage = client.read()
                client.close()
            elif(from_search == 1):
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
        return text.lower() == "schedule" or text.lower() == "quit"

    def on_enter_schedule(self, event):
        text = event.message.text

        if(text.lower() == "quit"):
            reply_token = event.reply_token
            send_text_message(reply_token, "Back to main")
            self.go_back()
        elif(text.lower() == "schedule"):
            global from_upcoming, from_search
            if(from_upcoming == 1):
                global upcoming_interest, upcoming_info, upcoming_link
                if not upcoming_info:
                    anime_info(upcoming_link[upcoming_interest])
                sched = "No data found"
                for i in range(len(upcoming_info)):
                    if(upcoming_info[i] == "Broadcast:"):
                        sched = upcoming_info[i+1]
                        break
            elif(from_search == 1):
                global interest, link, info
                # if info not searched before, then search
                if not info:
                    anime_info(link[interest])
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
        return text.lower() == "status" or text.lower() == "quit"

    def on_enter_status(self, event):
        text = event.message.text

        if(text.lower() == "quit"):
            reply_token = event.reply_token
            send_text_message(reply_token, "Back to main")
            self.go_back()
        elif(text.lower() == "status"):
            global from_upcoming, from_search
            if(from_upcoming == 1):
                global upcoming_interest, upcoming_info, upcoming_link
                if not upcoming_info:
                    anime_info(upcoming_link[upcoming_interest])
                for i in range(len(upcoming_info)):
                    if(upcoming_info[i] == "Status:"):
                        if ":" in upcoming_info[i+1]:
                            status = "No data found"
                        else:
                            status = upcoming_info[i+1]
                        break
            elif(from_search == 1):
                global interest, link, info
                # if info not searched before, then search
                if not info:
                    anime_info(link[interest])
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
# date state

    def is_going_to_date(self, event):
        text = event.message.text
        return text.lower() == "release" or text.lower() == "quit"

    def on_enter_date(self, event):
        text = event.message.text

        if(text.lower() == "quit"):
            reply_token = event.reply_token
            send_text_message(reply_token, "Back to main")
            self.go_back()
        elif(text.lower() == "release"):
            global from_upcoming, from_search
            if(from_upcoming == 1):
                global upcoming_interest, upcoming_info, upcoming_link
                if not upcoming_info:
                    anime_info(upcoming_link[upcoming_interest])
                
                for i in range(len(upcoming_info)):
                    if(upcoming_info[i] == "Aired:"):
                        if ":" in upcoming_info[i+1]:
                            date = "No data found"
                        else:
                            date = upcoming_info[i+1]
                        break
            elif(from_search == 1):
                global interest, link, info
                # if info not searched before, then search
                if not info:
                    anime_info(link[interest])
                # look for appropriate item
                for i in range(len(info)):
                    if(info[i] == "Aired:"):
                        if ":" in info[i+1]:
                            date = "No data found"
                        else:
                            date = info[i+1]
                        break

            # message
            reply_token = event.reply_token
            send_text_message(reply_token, date)

# =================================================================
# top upcoming state

    def is_going_to_upcoming(self, event):
        text = event.message.text
        global upcoming_more, upcoming_info, from_upcoming, from_search
        upcoming_info.clear()
        from_search = -1
        from_upcoming = 1
        if(upcoming_more != 0):
            upcoming_more = 1
        return text.lower() == "upcoming"

    def on_enter_upcoming(self, event):
        global upcoming_title, upcoming_more

        # search if not searched before
        if(upcoming_more == 0):
            anime_upcoming()
            upcoming_more = 1

        # show 10 titles each time and restart if reached the end
        text = ""
        if(upcoming_more < 5):
            end = upcoming_more * 10
            start = end - 10
            for i in range(start, end):
                text += str(i+1) + ". " + upcoming_title[i]
                if(i < end-1):
                    text += "\n"
            upcoming_more += 1

        # message
        reply_token = event.reply_token
        send_text_message(reply_token, text)

# =================================================================
# more upcoming state

    def is_going_to_moreupcoming(self, event):
        text = event.message.text
        return text.lower() == "more" or text.lower() == "quit"

    def on_enter_moreupcoming(self, event):
        text = event.message.text
        
        if(text.lower() == "quit"):
            reply_token = event.reply_token
            send_text_message(reply_token, "Back to main")
            self.go_back()
        elif(text.lower() == "more"):
            global upcoming_title, upcoming_more

            # show 10 titles each time and restart if reached the end
            text = ""
            if(upcoming_more == 6):
                upcoming_more = 1
            if(upcoming_more < 6):
                end = upcoming_more * 10
                start = end - 10
                for i in range(start, end):
                    text += str(i+1) + ". " + upcoming_title[i]
                    if(i < end-1):
                        text += "\n"
                upcoming_more += 1

            # message
            reply_token = event.reply_token
            send_text_message(reply_token, text)

# =================================================================
# to info state

    def is_going_to_infofromupcoming(self, event):
        text = event.message.text
        return text.lower() == "learn more" or text.lower() == "quit"

    def on_enter_infofromupcoming(self, event):
        text = event.message.text
        
        if(text.lower() == "quit"):
            reply_token = event.reply_token
            send_text_message(reply_token, "Back to main")
            self.go_back()
        elif(text.lower() == "learn more"):
            global from_upcoming
            from_upcoming = 1
            # message
            reply_token = event.reply_token
            send_text_message(reply_token, "Which anime are you interested? [number-1]")

# =================================================================
# news state

    def is_going_to_news(self, event):
        text = event.message.text
        return text.lower() == "news" or text.lower() == "quit"

    def on_enter_news(self, event):
        text = event.message.text
        
        if(text.lower() == "quit"):
            reply_token = event.reply_token
            send_text_message(reply_token, "Back to main")
            self.go_back()
        elif(text.lower() == "news"):
            global news_more, news_link, news_clip, news_title
            if(news_more == -1):
                anime_news()
                news_more = 0
            if(news_more == 4):
                news_more = 0
            text = news_title[news_more] + "\n\n"
            text += news_clip[news_more]
            news_more += 1
            # message
            reply_token = event.reply_token
            send_text_message(reply_token, text)

# =================================================================
# morenews state

    def is_going_to_morenews(self, event):
        text = event.message.text
        return text.lower() == "read more" or text.lower() == "quit" or text.lower() == "more"

    def on_enter_morenews(self, event):
        text = event.message.text
        
        if(text.lower() == "quit"):
            reply_token = event.reply_token
            send_text_message(reply_token, "Back to main")
            self.go_back()
        else:
            global news_more, news_link, news_clip, news_title
            if(news_more == 4):
                news_more = 0
            text = news_title[news_more] + "\n\n"
            text += news_clip[news_more]
            news_more += 1
            # message
            reply_token = event.reply_token
            send_text_message(reply_token, text)

# =================================================================
# specific news state

    def is_going_to_specific(self, event):
        text = event.message.text
        return text.lower() == "specific" or text.lower() == "quit"

    def on_enter_specific(self, event):
        text = event.message.text
        
        if(text.lower() == "quit"):
            reply_token = event.reply_token
            send_text_message(reply_token, "Back to main")
            self.go_back()
        elif(text.lower() == "specific"):
            global news_more, news_link, news_clip, news_title
            search_url = news_link[news_more-1]
            # request to open url
            req = Request(search_url, headers={'User-Agent': 'Mozilla/5.0'})
            client = urlopen(req)
            htmlpage = client.read()
            client.close()
            # parse html and find text location
            wholepage = soup(htmlpage, "html.parser")
            paragraph = wholepage.find("div", {"class": "content clearfix"})
            text = paragraph.text.strip()
            # message
            reply_token = event.reply_token
            send_text_message(reply_token, text)

# =================================================================
# exit news state

    def is_going_to_exitnews(self, event):
        text = event.message.text
        return text.lower() == "exit" or text.lower() == "quit"

    def on_enter_exitnews(self, event):
        global news_clip, news_link, news_more, news_title
        # reset variables
        news_title.clear()
        news_link.clear()
        news_clip.clear()
        news_more = -1
        reply_token = event.reply_token
        send_text_message(reply_token, "Back to main")
        self.go_back()