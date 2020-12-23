import os
from urllib.request import Request, urlopen
from bs4 import BeautifulSoup as soup
from linebot import LineBotApi, WebhookParser
from linebot.models import MessageEvent, TextMessage, TextSendMessage
from linebot.models import CarouselTemplate, MessageTemplateAction, TemplateSendMessage, CarouselColumn
from linebot.models import ButtonsTemplate

channel_access_token = os.getenv("LINE_CHANNEL_ACCESS_TOKEN", None)


def send_text_message(reply_token, text):
    line_bot_api = LineBotApi(channel_access_token)
    line_bot_api.reply_message(reply_token, TextSendMessage(text=text))

    return "OK"

def send_button_carousel(id, user_text, img_url, anime_title, next_link, load):
    line_bot_api = LineBotApi(channel_access_token)
    
    cols = []
    if(load == 0):
        number = 0
        if(len(anime_title) > 5):
            end = 5
        else:
            end = len(anime_title)
    else:
        number = 5
        end = len(anime_title)

    for i in range(number, end):
        temp = "Anime " + str(number+1)
        cols.append(
            CarouselColumn(
                thumbnail_image_url=img_url[number],
                title=temp,
                text=anime_title[i],
                actions=[
                    MessageTemplateAction(
                        label='Learn more',
                        text=str(number)
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

def send_button_message(id, img_url, anime_title, label, chat):
    line_bot_api = LineBotApi(channel_access_token)

    acts = []
    for i, lab in enumerate(label):
        acts.append(
            MessageTemplateAction(
                label=lab,
                text=chat[i]
            )
        )

    message = TemplateSendMessage(
        alt_text='Buttons template',
        template=ButtonsTemplate(
            thumbnail_image_url=str(img_url),
            title=str(anime_title),
            text="What do you want to see?",
            actions=acts
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
