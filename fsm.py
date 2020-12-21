from transitions.extensions import GraphMachine
from utils import send_text_message

class TocMachine(GraphMachine):
    def __init__(self, **machine_configs):
        self.machine = GraphMachine(model=self, **machine_configs)

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
        if(text.lower() == "exit"):
            reply_token = event.reply_token
            send_text_message(reply_token, "Reset")
            self.go_back()
        else:
            reply_token = event.reply_token
            send_text_message(reply_token, "in title state: " + event.message.text)