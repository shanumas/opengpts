# Assuming storage.py is in the same directory
from langchain_core.messages import AIMessage
from typing import List
from typing import Optional
from wapp import send_message

from storage import list_assistants, get_assistant, post_thread_messages, list_threads


def __init__(self, user_id: str):
    self.user_id = user_id

def reply_user(message: AIMessage, to_number, from_id):
    send_message(message.content, to_number, from_id)



def process_message(user_id: str, assistant_id: str,thread_id: str, message: AIMessage):
    matching_assistants = find_assistants_by_suffix(user_id, assistant_id)
    for assistant in matching_assistants:
        threads = list_threads(user_id)
        for thread in threads:
            if thread["assistant_id"] != assistant_id:
                post_thread_messages(user_id, thread["thread_id"], [message])
                send_message(message.content,"46708943293", "")


def find_assistants_by_suffix(user_id, assistant_id: str) -> List[str]:
    assistant = get_assistant(user_id, assistant_id)
    if assistant:
        suffix = assistant_id.rsplit('_', 1)[-1]  # Get the suffix after the last underscore
        assistants = list_assistants(user_id)
        matching_assistants = [
            a for a in assistants if (a["assistant_id"] != assistant_id) & (a["assistant_id"].endswith(suffix))
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

