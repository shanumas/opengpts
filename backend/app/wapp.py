import requests
import os


def send_message(message, to_number, bot_number):
  WAPP_ID_NAME = "WAPP_ID_" + bot_number
  TOKEN = os.environ.get(bot_number, "")
  WAPP_ID = os.environ.get(WAPP_ID_NAME, "")

  headers = {
      'Authorization': 'Bearer ' + TOKEN,
      'Content-Type': 'application/json'
  }
  data = {
      "messaging_product": "whatsapp",
      "to": to_number,
      "type": "text",
      "text": {
          "preview_url": "true",
          "body": "Question from Artisanals: "
      }
  }
  url = "https://graph.facebook.com/v18.0/" + WAPP_ID + "/messages"
  data["text"]["body"] = message
  response = requests.post(url, headers=headers, json=data)
  print(response.text)
