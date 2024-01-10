import requests



headers = {
    'Authorization': 'Bearer EAAEgVu0jNtABOwJN0F85eIhGf4vtBzG4VlnWrqANHVj3MAwz17YGOrPwp60LvRQNHNQ4QYaDtO6qskZCMq3uPnakaxP8LYZAVsjN2QTQVlAPlA5ZCx3AwMuOHsbrTBUf0OZCT1UOzJ9r3ZA9ERycSq13zyhM0dSv7EUyXJyfETNOatkVKUw5Np9OH87ZBX2JxS',
    'Content-Type': 'application/json'
}



def send_message(message, to_number, from_id):
    #data["text"]["body"] = data["text"]["body"] + ': '+message
    from_id = "189399934262514"
    data = {
        "messaging_product": "whatsapp",
        "to": to_number,
        "type": "text",
        "text": {
            "preview_url": "true",
            "body": "Question from Artisanals: "
        }
    }
    url = "https://graph.facebook.com/v18.0/"+from_id+"/messages"
    data["text"]["body"] = message
    response = requests.post(url, headers=headers, json=data)
    print(response.text)