from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel
import uvicorn
import os
import requests



async def handle(req):
    user_id ="46708943293"
    # Parse the request body from the POST
    body = await req.json()

    # Check the Incoming webhook message
    # info on WhatsApp text message payload: https://developers.facebook.com/docs/whatsapp/cloud-api/webhooks/payload-examples#text-messages
    if body.get("object"):
        print('post request reached')
        receiver = body["entry"][0]["changes"][0]["value"]["metadata"]["display_phone_number"]
        print(receiver)

        # Handle only public at the moment
        # Check if this is a brand-bot number
        if receiver not in ["353892619075", "447587607789"]:
            return JSONResponse(content={"message": "error | unexpected body"}, status_code=400)

        print('publicBot reached')

        if True:
            print('Incoming message: from public-bot')
            # Request is received thrice, do not know why. But "messages are empty for duplicate requests"
            if body["entry"][0]["changes"][0]["value"].get("messages"):
                text = body["entry"][0]["changes"][0]["value"]["messages"][0]["text"]["body"]
                await send_open_gpts(body["entry"][0]["changes"][0]["value"]["messages"][0]["from"], receiver, text)
            else:
                print('No messages received from Whatsapp')
            return JSONResponse(content={"message": "ok"}, status_code=200)
        else:
            print('Incoming message: from personal-bot')
    else:
        return JSONResponse(content={"message": "error | unexpected body"}, status_code=400)


async def send_open_gpts(sender, bot_num, text):
    user_id = "46708943293"
    base_url = os.getenv("NGROK")

    public_assistant_id = f"public_{bot_num}_{user_id}"
    public_thread_id = f"{sender}_{user_id}"

    public_name = "PUBLIC"
    PUBLIC_PROMPT = os.getenv("PUBLIC_PROMPT", "You are a helpful assistant.")

    if sender == user_id:
        public_thread_id = f"personal_{user_id}"
        public_assistant_id = f"personal_{user_id}"
        public_name = "PERSONAL"
        PUBLIC_PROMPT = os.getenv("PERSONAL_PROMPT", "You are a helpful assistant.")

    assistants_url = f"{base_url}/assistants/{public_assistant_id}"
    threads_url = f"{base_url}/threads/{public_thread_id}"
    stream_url = f"{base_url}/runs/stream"

    headers = {
        "Content-Type": "application/json",
        "Cookie": f"opengpts_user_id={user_id}",
    }

    # Make sure the personal-assistant and personal-thread are already created
    personal_thread_check(base_url, user_id, headers)

    # Make sure assistant is created
    payload = {
        "name": public_name,
        "config": {
            "configurable": {
                "thread_id": public_thread_id,
                "type": "agent",
                "type==agent/agent_type": "GPT 3.5 Turbo",
                "type==agent/system_message": PUBLIC_PROMPT,
                "type==agent/tools": [],
                "type==dungeons_and_dragons/llm": "gpt-35-turbo",
            }
        },
        "public": True,
    }

    try:
        response = requests.put(assistants_url, json=payload, headers=headers)
        response.raise_for_status()
        print(f"Assistants PUT Request Successful: {response.json()}")
    except requests.exceptions.RequestException as e:
        print(f"Error making Assistants PUT request: {e}")

    # Make sure thread is created
    payload = {
        "assistant_id": public_assistant_id,
        "name": sender,
    }

    try:
        response = requests.put(threads_url, json=payload, headers=headers)
        response.raise_for_status()
        print(f"Public Threads PUT Request Successful: {response.json()}")
    except requests.exceptions.RequestException as e:
        print(f"Error making Public Threads PUT request: {e}")

    # Post message
    payload = {
        "input": {
            "messages": [
                {
                    "content": text,
                    "additional_kwargs": {},
                    "type": "human",
                    "example": False,
                }
            ]
        },
        "assistant_id": public_assistant_id,
        "thread_id": public_thread_id,
    }

    try:
        response = requests.post(stream_url, json=payload, headers=headers)
        response.raise_for_status()
        print("Stream request successful")
    except requests.exceptions.RequestException as e:
        print(f"Error making Stream request: {e}")

    return {"message": "ok"}


def personal_thread_check(base_url, user_id, headers):
    PERSONAL_PROMPT = os.getenv("PERSONAL_PROMPT", "You are a helpful assistant.")

    personal_assistant_id = f"personal_{user_id}"
    personal_assistant_url = f"{base_url}/assistants/{personal_assistant_id}"
    personal_thread_url = f"{base_url}/threads/{personal_assistant_id}"

    # Make sure assistant is created
    payload = {
        "name": "PERSONAL",
        "config": {
            "configurable": {
                "thread_id": "personal",
                "type": "agent",
                "type==agent/agent_type": "GPT 3.5 Turbo",
                "type==agent/system_message": PERSONAL_PROMPT,
                "type==agent/tools": [],
                "type==dungeons_and_dragons/llm": "gpt-35-turbo",
            }
        },
        "public": True,
    }

    try:
        response = requests.put(personal_assistant_url, json=payload, headers=headers)
        response.raise_for_status()
        print(f"Assistants PUT Request Successful: {response.json()}")
    except requests.exceptions.RequestException as e:
        print(f"Error making Assistants PUT request: {e}")

    # Make sure thread is created
    payload = {"opengpts_user_id": user_id}

    try:
        response = requests.get(personal_thread_url, json=payload, headers=headers)
        response.raise_for_status()
        print(f"Get personal Thread Successful: {response.json()}")
    except requests.exceptions.RequestException as e:
        print(f"Get personal Thread failure: {e}")

        # If thread does not exist, create it
        if response.status_code == 422:
            print("Thread does not exist, creating it")
            threads_payload = {
                "assistant_id": personal_assistant_id,
                "name": "PERSONAL",
            }

            try:
                response = requests.put(personal_thread_url, json=threads_payload, headers=headers)
                response.raise_for_status()
                print(f"Personal Thread PUT Request Successful: {response.json()}")
            except requests.exceptions.RequestException as e:
                print(f"Error making Personal Thread PUT request: {e}")



