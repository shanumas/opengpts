import requests

url = "https://graph.facebook.com/v18.0/189399934262514/messages"

headers = {
    'Authorization': 'Bearer EAAEgVu0jNtABOwJN0F85eIhGf4vtBzG4VlnWrqANHVj3MAwz17YGOrPwp60LvRQNHNQ4QYaDtO6qskZCMq3uPnakaxP8LYZAVsjN2QTQVlAPlA5ZCx3AwMuOHsbrTBUf0OZCT1UOzJ9r3ZA9ERycSq13zyhM0dSv7EUyXJyfETNOatkVKUw5Np9OH87ZBX2JxS',
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