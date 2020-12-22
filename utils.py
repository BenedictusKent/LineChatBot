import os
from urllib.request import Request, urlopen
from bs4 import BeautifulSoup as soup
from linebot import LineBotApi, WebhookParser
from linebot.models import MessageEvent, TextMessage, TextSendMessage
from linebot.models import CarouselTemplate, MessageTemplateAction, TemplateSendMessage, CarouselColumn


channel_access_token = os.getenv("LINE_CHANNEL_ACCESS_TOKEN", None)


def send_text_message(reply_token, text):
    line_bot_api = LineBotApi(channel_access_token)
    line_bot_api.reply_message(reply_token, TextSendMessage(text=text))

    return "OK"

def send_button_carousel(id, user_text, img_url, anime_title, next_link):
    line_bot_api = LineBotApi(channel_access_token)
    
    cols = []
    number = 1
    for i in range(len(anime_title)):
        if user_text.lower() in anime_title[i].lower():
            temp = "Anime " + str(number)
            cols.append(
                CarouselColumn(
                    thumbnail_image_url=img_url[number-1],
                    title=temp,
                    text=anime_title[i],
                    actions=[
                        MessageTemplateAction(
                            label='Learn more',
                            text='See anime ' + str(number)
                        )
                    ]
                )
            )
            number += 1

    message = TemplateSendMessage(
        alt_text='Carousel template',
        template=CarouselTemplate(
            columns=cols
        )
    )

    line_bot_api.push_message(id, message)

    return "OK"

"""
def send_image_url(id, img_url):
    pass

def send_button_message(id, text, buttons):
    pass
"""
