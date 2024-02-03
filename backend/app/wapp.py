import requests
import os


def send_message(message, to_number, WAPP_ID, TOKEN):

  print("TOKEN: " + TOKEN + "-, WAPP_ID: " + WAPP_ID + "-")

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
  print("URL: " + url + "-")
  data["text"]["body"] = message
  response = requests.post(url, headers=headers, json=data)
  print(response.text)
