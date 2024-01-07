# Assuming storage.py is in the same directory
from langchain_core.messages import AIMessage
from typing import List
from typing import Optional
from wapp import send_message

from storage import list_assistants, get_assistant, post_thread_messages, list_threads


def __init__(self, user_id: str):
    self.user_id = user_id

def reply_user(message: AIMessage):
    send_message(message.content)



def process_message(user_id: str, assistant_id: str,thread_id: str, message: AIMessage):
    matching_assistants = find_assistants_by_suffix(user_id, assistant_id)
    for assistant in matching_assistants:
        threads = list_threads(user_id)
        for thread in threads:
            if thread["assistant_id"] != assistant_id:
                message_to_send = AIMessage(content='Question from brand: What is your price per TIKTOK post?')
                post_thread_messages(user_id, thread["thread_id"], [message_to_send])
                send_message(message_to_send.content)


def find_assistants_by_suffix(user_id, assistant_id: str) -> List[str]:
    assistant = get_assistant(user_id, assistant_id)
    if assistant:
        assistant_name = assistant["name"]
        suffix = assistant_name.rsplit('_', 1)[-1]  # Get the suffix after the last underscore
        assistants = list_assistants(user_id)
        matching_assistants = [
            a for a in assistants if (a["assistant_id"] != assistant_id) & (a["name"].endswith(suffix))
        ]
        return matching_assistants
    else:
        return []

def get_assistant_by_id(user_id, assistant_id: str) -> Optional[dict]:
    # Implement logic to retrieve the assistant by ID
    assistants = list_assistants(user_id)
    for assistant in assistants:
        if assistant["assistant_id"] == assistant_id:
            return assistant
    return None

