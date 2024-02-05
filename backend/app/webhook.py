from fastapi.responses import JSONResponse
import storage as storage
import runs as runs
import os
import requests


async def handle(req):
  # Parse the request body from the POST
  body = await req.json()

  # Check the Incoming webhook message
  # info on WhatsApp text message payload: https://developers.facebook.com/docs/whatsapp/cloud-api/webhooks/payload-examples#text-messages
  if body.get("object"):
    print('post request reached')
    receiver = body["entry"][0]["changes"][0]["value"]["metadata"][
        "display_phone_number"]
    print("Receiver: " + receiver)

    # Handle only public at the moment
    # Check if this is a brand-bot number
    if receiver not in ["353892619074", "353892619075", "447587607789"]:
      return JSONResponse(content={"message": "error | unexpected body"},
                          status_code=400)

    USER_ID = os.environ.get(receiver + "_USER")
    WAPP_ID = os.environ.get(receiver + "_WAPP_ID")
    TOKEN = os.environ.get(receiver + "_TOKEN")

    print('publicBot reached: : ' + receiver)
    print('publicBot reached: USER_ID: ' + USER_ID)
    print('publicBot reached: WAPP_ID: ' + WAPP_ID)
    print('publicBot reached: TOKEN: ' + TOKEN)

    if True:
      print('Incoming message: from public-bot')
      # Request is received thrice, do not know why. But "messages are empty for duplicate requests"
      if body["entry"][0]["changes"][0]["value"].get("messages"):
        text = body["entry"][0]["changes"][0]["value"]["messages"][0]["text"][
            "body"]
        await send_open_gpts(
            req,
            body["entry"][0]["changes"][0]["value"]["messages"][0]["from"],
            receiver, text, USER_ID, WAPP_ID, TOKEN)
      else:
        print('No messages received from Whatsapp')
      return JSONResponse(content={"message": "ok"}, status_code=200)
    else:
      print('Incoming message: from personal-bot')
  else:
    return JSONResponse(content={"message": "error | unexpected body"},
                        status_code=400)


async def send_open_gpts(req, sender, bot_num, text, USER_ID, WAPP_ID, TOKEN):

  public_assistant_id = f"public_{bot_num}_{USER_ID}"
  public_thread_id = f"{sender}_{USER_ID}"

  public_name = "PUBLIC"
  PUBLIC_PROMPT = os.environ.get("PUBLIC_PROMPT")

  if sender == USER_ID:
    public_thread_id = f"personal_{USER_ID}"
    public_assistant_id = f"personal_{USER_ID}"
    public_name = "PERSONAL"
    PUBLIC_PROMPT = os.environ.get("PERSONAL_PROMPT")

  headers = {
      "Content-Type": "application/json",
      "Cookie": f"opengpts_user_id={USER_ID}",
  }

  # Make sure the personal-assistant and personal-thread are already created
  personal_thread_check(USER_ID, headers, WAPP_ID, TOKEN)

  #These is public assistant stuff
  if sender != USER_ID:
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
      storage.put_assistant(USER_ID,
                            public_assistant_id,
                            name=payload['name'],
                            config=payload['config'],
                            public=payload['public'])
      print(f"Assistants PUT Request Successful: ")
    except requests.exceptions.RequestException as e:
      print(f"Error making Assistants PUT request: {e}")

    # Make sure thread is created
    payload = {
        "assistant_id": public_assistant_id,
        "name": sender,
    }

    try:
      storage.put_thread(
          USER_ID,
          public_thread_id,
          assistant_id=payload['assistant_id'],
          name=payload['name'],
      )
      print(f"Public Threads PUT Request Successful: ")
    except requests.exceptions.RequestException as e:
      print(f"Error making Public Threads PUT request: {e}")

  #This is general stuff
  # Post message
  payload = {
      "input": {
          "messages": [{
              "content": text,
              "additional_kwargs": {},
              "type": "human",
              "example": False,
          }]
      },
      "assistant_id": public_assistant_id,
      "thread_id": public_thread_id,
  }

  try:
    await runs.stream_run(req, payload, USER_ID, WAPP_ID, TOKEN)
    print("Stream request successful: " + "USERID: " + USER_ID + "PAYLOAD: ")
    print(payload)
    print("TOKEN: " + TOKEN + "-, WAPP_ID: " + WAPP_ID + "-")
  except requests.exceptions.RequestException as e:
    print(f"Error making Stream request: {e}")

  return {"message": "ok"}


def personal_thread_check(USER_ID, headers, WAPP_ID, TOKEN):
  PERSONAL_PROMPT = os.environ.get("PERSONAL_PROMPT")

  personal_assistant_id = f"personal_{USER_ID}"

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
    storage.put_assistant(USER_ID,
                          personal_assistant_id,
                          name=payload['name'],
                          config=payload['config'],
                          public=payload['public'])
    print(f"Assistants PUT Request Successful: ")
  except requests.exceptions.RequestException as e:
    print(f"Error making Assistants PUT request: {e}")

  # Make sure thread is created
  payload = {"opengpts_user_id": USER_ID}

  thisThread = None

  try:
    thisThread = storage.get_thread(USER_ID, personal_assistant_id)
  except requests.exceptions.RequestException as e:
    print(f"Get personal Thread failure: {e}")

  if thisThread is None:
    # If thread does not exist, create it
    print("Thread does not exist, creating it")

    try:
      storage.put_thread(USER_ID,
                         personal_assistant_id,
                         assistant_id=personal_assistant_id,
                         name="PERSONAL")
      print(f"Personal Thread PUT Request Successful: ")
    except requests.exceptions.RequestException as e:
      print(f"Error making Personal Thread PUT request: {e}")
