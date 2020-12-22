from transitions.extensions import GraphMachine
from urllib.request import Request, urlopen
from bs4 import BeautifulSoup as soup
from utils import send_text_message, send_button_carousel

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
            url = text.replace(" ", "%20")
            search_url = "https://myanimelist.net/search/all?q=" + url + "&cat=all"
            
            #### search in MyAnimeList
            # request to open url
            req = Request(search_url, headers={'User-Agent': 'Mozilla/5.0'})
            client = urlopen(req)
            htmlpage = client.read()
            client.close()
            # parse html and go to article tag
            wholepage = soup(htmlpage, "html.parser")
            articlepage = wholepage.article
            # take useful info
            img_url = []
            title = []
            link = []
            images = []
            divs = articlepage.findAll("div", {"class": "list di-t w100"})      # num of searches
            for div in divs:
                img_url.append(div.div.a.img["data-src"]) 
                second = div.find("div", {"class": "information di-tc va-t pt4 pl8"})
                title.append(second.a.text.strip())
                link.append(second.a["href"])
            # filter searches
            for i in range(len(title)):
                if text.lower() in title[i].lower():
                    req = Request(link[i], headers={'User-Agent': 'Mozilla/5.0'})
                    client = urlopen(req)
                    htmlpage = client.read()
                    client.close()
                    specific = soup(htmlpage, "html.parser")
                    imgtag = specific.find("img", {"alt": title[i]})
                    images.append(str(imgtag["data-src"]))
            print(len(images))

            userid = event.source.user_id
            send_button_carousel(userid, text, images, title, link)

# =================================================================
# Repeat state

    def is_going_to_repeat(self, event):
        text = event.message.text
        return text.lower() == "repeat"

    def on_enter_repeat(self, event):
        print("Enter repeat stage")
        reply_token = event.reply_token
        send_text_message(reply_token, "Can repeat now")