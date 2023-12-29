# Assuming storage.py is in the same directory
from langchain_core.messages import AIMessage
from typing import List

from storage import list_assistants, get_assistant, post_thread_messages, list_threads


def __init__(self, user_id: str):
    self.user_id = user_id


def process_message(user_id: str, assistant_id: str, message: AIMessage):
    matching_assistants = find_assistants_by_suffix(user_id, assistant_id)
    for assistant in matching_assistants:
        threads = list_threads(user_id)
        for thread in threads:
            if thread["assistant_id"] == assistant["assistant_id"]:
                post_thread_messages(user_id, thread["thread_id"], [message])


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

