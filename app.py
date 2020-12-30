import os
import sys

from flask import Flask, jsonify, request, abort, send_file
from dotenv import load_dotenv
from linebot import LineBotApi, WebhookParser
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage

from fsm import TocMachine
from utils import send_text_message

load_dotenv()


machine = TocMachine(
    states=["main", "search", "title", "repeat", "load", "info", "synopsis", "test",
            "schedule", "status", "repeatinfo", "upcoming", "moreupcoming",
            "infofromupcoming", "date", "news", "morenews", "specific", "exitnews"],
    transitions=[
        {
            "trigger": "advance",
            "source": "main",
            "dest": "search",
            "conditions": "is_going_to_search",
        },
        {
            "trigger": "advance",
            "source": "main",
            "dest": "test",
            "conditions": "is_going_to_test",
        },
        {
            "trigger": "advance",
            "source": "main",
            "dest": "upcoming",
            "conditions": "is_going_to_upcoming",
        },
        {
            "trigger": "advance",
            "source": "main",
            "dest": "news",
            "conditions": "is_going_to_news",
        },
        {
            "trigger": "advance",
            "source": "news",
            "dest": "morenews",
            "conditions": "is_going_to_morenews",
        },
        {
            "trigger": "advance",
            "source": "morenews",
            "dest": "morenews",
            "conditions": "is_going_to_morenews",
        },
        {
            "trigger": "advance",
            "source": ["news", "morenews"],
            "dest": "specific",
            "conditions": "is_going_to_specific",
        },
        {
            "trigger": "advance",
            "source": "specific",
            "dest": "exitnews",
            "conditions": "is_going_to_exitnews",
        },
        {
            "trigger": "advance",
            "source": "upcoming",
            "dest": "moreupcoming",
            "conditions": "is_going_to_moreupcoming",
        },
        {
            "trigger": "advance",
            "source": "moreupcoming",
            "dest": "moreupcoming",
            "conditions": "is_going_to_moreupcoming",
        },
        {
            "trigger": "advance",
            "source": "search",
            "dest": "title",
            "conditions": "is_going_to_title",
        },
        {
            "trigger": "advance",
            "source": "title",
            "dest": "load",
            "conditions": "is_going_to_load",
        },
        {
            "trigger": "advance",
            "source": "load",
            "dest": "load",
            "conditions": "is_going_to_load",
        },
        {
            "trigger": "advance",
            "source": ["title", "load"],
            "dest": "repeat",
            "conditions": "is_going_to_repeat",
        },
        {
            "trigger": "advance",
            "source": "repeat",
            "dest": "title",
            "conditions": "is_going_to_title",
        },
        {
            "trigger": "advance",
            "source": ["title", "load"],
            "dest": "info",
            "conditions": "is_going_to_info",
        },
        {
            "trigger": "advance",
            "source": "info",
            "dest": "synopsis",
            "conditions": "is_going_to_synopsis",
        },
        {
            "trigger": "advance",
            "source": "info",
            "dest": "status",
            "conditions": "is_going_to_status",
        },
        {
            "trigger": "advance",
            "source": "info",
            "dest": "schedule",
            "conditions": "is_going_to_schedule",
        },
        {
            "trigger": "advance",
            "source": "info",
            "dest": "date",
            "conditions": "is_going_to_date",
        },
        {
            "trigger": "advance",
            "source": ["schedule", "status", "synopsis", "date"],
            "dest": "repeatinfo",
            "conditions": "is_going_to_repeatinfo",
        },
        {
            "trigger": "advance",
            "source": "repeatinfo",
            "dest": "info",
            "conditions": "is_going_to_info",
        },
        {
            "trigger": "advance",
            "source": ["upcoming", "moreupcoming"],
            "dest": "infofromupcoming",
            "conditions": "is_going_to_infofromupcoming",
        },
        {
            "trigger": "advance",
            "source": "infofromupcoming",
            "dest": "info",
            "conditions": "is_going_to_info",
        },
        {
            "trigger": "go_back",
            "source": ["search", "info", "moreupcoming", "status", "schedule",
                       "synopsis", "repeatinfo", "load", "repeat", "title",
                       "infofromupcoming", "date", "news", "morenews", "specific",
                       "exitnews"],
            "dest": "main",
        },
    ],
    initial="main",
    auto_transitions=False,
    show_conditions=True,
)

app = Flask(__name__, static_url_path="")


# get channel_secret and channel_access_token from your environment variable
channel_secret = os.getenv("LINE_CHANNEL_SECRET", None)
channel_access_token = os.getenv("LINE_CHANNEL_ACCESS_TOKEN", None)
if channel_secret is None:
    print("Specify LINE_CHANNEL_SECRET as environment variable.")
    sys.exit(1)
if channel_access_token is None:
    print("Specify LINE_CHANNEL_ACCESS_TOKEN as environment variable.")
    sys.exit(1)

line_bot_api = LineBotApi(channel_access_token)
parser = WebhookParser(channel_secret)


@app.route("/callback", methods=["POST"])
def callback():
    signature = request.headers["X-Line-Signature"]
    # get request body as text
    body = request.get_data(as_text=True)
    app.logger.info("Request body: " + body)

    # parse webhook body
    try:
        events = parser.parse(body, signature)
    except InvalidSignatureError:
        abort(400)

    # if event is MessageEvent and message is TextMessage, then echo text
    for event in events:
        if not isinstance(event, MessageEvent):
            continue
        if not isinstance(event.message, TextMessage):
            continue

        line_bot_api.reply_message(
            event.reply_token, TextSendMessage(text=event.message.text)
        )

    return "OK"


@app.route("/webhook", methods=["POST"])
def webhook_handler():
    signature = request.headers["X-Line-Signature"]
    # get request body as text
    body = request.get_data(as_text=True)
    app.logger.info(f"Request body: {body}")

    # parse webhook body
    try:
        events = parser.parse(body, signature)
    except InvalidSignatureError:
        abort(400)

    # if event is MessageEvent and message is TextMessage, then echo text
    for event in events:
        if not isinstance(event, MessageEvent):
            continue
        if not isinstance(event.message, TextMessage):
            continue
        if not isinstance(event.message.text, str):
            continue
        print(f"\nFSM STATE: {machine.state}")
        #print(f"REQUEST BODY: \n{body}")
        response = machine.advance(event)
        print(f"FSM STATE: {machine.state}")
        if response == False:
            send_text_message(event.reply_token, "Input unrecognized. Re-check your spelling")

    return "OK"


@app.route("/show-fsm", methods=["GET"])
def show_fsm():
    machine.get_graph().draw("fsm.png", prog="dot", format="png")
    return send_file("fsm.png", mimetype="image/png")


if __name__ == "__main__":
    port = os.environ.get("PORT", 8000)
    app.run(host="0.0.0.0", port=port, debug=True)
