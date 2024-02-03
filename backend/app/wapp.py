import requests
import os


def send_message(message, to_number):
  USER_ID = os.environ.get("USERID", "")
  TOKEN_NAME = USER_ID
  WAPP_ID_NAME = "WAPP_ID_" + USER_ID
  TOKEN = os.environ.get(TOKEN_NAME, "")
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
