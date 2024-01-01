import requests

url = "https://graph.facebook.com/v18.0/140653755809086/messages"

headers = {
    'Authorization': 'Bearer EAAEgVu0jNtABO7X3LCnnvbVakx5mIR5FuiZBKGim2NPiZCN4KnGytOLZAkMZBBZAiFqSXMyqMZC87kdvMFrmMpZBxRrZBMTf4mdnxopTZCBgHFe72aaNLL4csVwUJF9CZAPnZC8Ea0EoxD3WrcdgdEflHaYPSSEw4PSawZCvCNmqslkvNlYUNGW7PXjIlYZCKHpCMTCd4273X96IDfJXPxjOB',
    'Content-Type': 'application/json'
}

data = {
    "messaging_product": "whatsapp",
    "to": "46708943293",
    "type": "text",
    "text": {
        "preview_url": "true",
        "body": "Question from Artisanals: "
    }
}

def send_message(message):
    #data["text"]["body"] = data["text"]["body"] + ': '+message
    data["text"]["body"] = message
    response = requests.post(url, headers=headers, json=data)
    print(response.text)