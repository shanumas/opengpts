import asyncio
import json
from typing import AsyncIterator, Sequence
from uuid import uuid4
import requests

import langsmith.client
import orjson
from fastapi import APIRouter, BackgroundTasks, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from langchain_core.messages import AIMessage, HumanMessage

from gizmo_agent import agent
from langchain.pydantic_v1 import ValidationError
from langchain.schema.messages import AnyMessage, FunctionMessage
from langchain.schema.output import ChatGeneration
from langchain.schema.runnable import RunnableConfig
from langserve.callbacks import AsyncEventAggregatorCallback
from langserve.schema import FeedbackCreateRequest
from langserve.serialization import WellKnownLCSerializer
from langserve.server import _get_base_run_id_as_str, _unpack_input
from langsmith.utils import tracing_is_enabled
from pydantic import BaseModel, Field
from sse_starlette import EventSourceResponse

from schema import OpengptsUserId
from storage import get_assistant, get_thread_messages, get_thread_messages_with_number, public_user_id, post_thread_messages, list_threads
from forwarder import process_message, reply_user
from stream import StreamMessagesHandler
import re

import copy

router = APIRouter()

_serializer = WellKnownLCSerializer()


class AgentInput(BaseModel):
  """An input into an agent."""

  messages: Sequence[AnyMessage] = Field(default_factory=list)


class CreateRunPayload(BaseModel):
  """Payload for creating a run."""

  assistant_id: str
  thread_id: str
  input: AgentInput = Field(default_factory=AgentInput)


async def _run_input_and_config(request: Request,
                                opengpts_user_id: OpengptsUserId, payload):
  try:
    body = None
    if not hasattr(payload, "Config"):
      body = payload
    else:
      body = await request.json()
  except json.JSONDecodeError:
    raise RequestValidationError(errors=["Invalid JSON body"])
  thread_ids = list_threads(opengpts_user_id)
  assistant, state, *brand_state = await asyncio.gather(
      asyncio.get_running_loop().run_in_executor(None, get_assistant,
                                                 opengpts_user_id,
                                                 body["assistant_id"]),
      asyncio.get_running_loop().run_in_executor(None, get_thread_messages,
                                                 opengpts_user_id,
                                                 body["thread_id"]),
      *[
          asyncio.get_running_loop().run_in_executor(
              None, get_thread_messages_with_number, opengpts_user_id,
              thread_id["thread_id"]) for thread_id in thread_ids
          if thread_id["thread_id"] != body["thread_id"]
      ])

  chat_history = ""
  # This condition will never happen, move this code to where tools are resolved instead
  if body["assistant_id"].startswith('personal'):
    for current_brand in brand_state:
      if current_brand is not None and current_brand["messages"] is not None:
        for message in current_brand["messages"]:
          if isinstance(message, AIMessage):
            chat_history += f'AI: {message.content}\n'
          elif isinstance(message, HumanMessage):
            chat_history += f'Human: {message.content}\n'
          else:
            chat_history += 'Unknown message type\n'

  if not assistant:
    raise HTTPException(status_code=404, detail="Assistant not found")
  config: RunnableConfig = {
      **assistant["config"],
      "configurable": {
          **assistant["config"]["configurable"], "user_id": opengpts_user_id,
          "thread_id": body["thread_id"],
          "assistant_id": body["assistant_id"],
          "chat_history": chat_history
      },
  }
  try:
    input_ = _unpack_input(
        agent.get_input_schema(config).validate(body["input"]))
  except ValidationError as e:
    raise RequestValidationError(e.errors(), body=body)

  if chat_history is not None and chat_history != "":
    config["configurable"]["type==agent/tools"] = config["configurable"][
        "type==agent/tools"] + ["ChatHistoryTool"]

  return input_, config, state["messages"], chat_history


@router.post("")
async def create_run(
    request: Request,
    payload: CreateRunPayload,  # for openapi docs
    opengpts_user_id: OpengptsUserId,
    background_tasks: BackgroundTasks):
  """Create a run."""
  input_, config, messages, chat_history = await _run_input_and_config(
      request, opengpts_user_id)
  background_tasks.add_task(agent.ainvoke, input_, config)
  return {"status": "ok"}  # TODO add a run id


@router.post("/stream")
async def stream_run(
    request: Request,
    payload: CreateRunPayload,  # for openapi docs
    opengpts_user_id: OpengptsUserId,
    WAPP_ID,
    TOKEN):
  """Create a run."""
  input_, config, messages, chat_history = await _run_input_and_config(
      request, opengpts_user_id, payload)
  #messages = messages + [HumanMessage(content="Consider also this chat history to answer my questions"+chat_history)]
  streamer = StreamMessagesHandler(messages + input_["messages"])
  event_aggregator = AsyncEventAggregatorCallback()
  config["callbacks"] = [streamer, event_aggregator]

  body = None

  if not hasattr(payload, "Config"):
    body = payload
  else:
    body = await request.json()

  sender_number = body["thread_id"].split('_')[0] if body["thread_id"].split(
      '_')[0] != 'personal' else body["thread_id"].split('_')[1]
  bot_num = body["thread_id"].split('_')[1]

  # Call the runnable in streaming mode,
  # add each chunk to the output stream
  async def consume_astream() -> None:
    try:
      async for chunk in agent.astream(input_, config):
        await streamer.send_stream.send(chunk)
        # hack: function messages aren't generated by chat model
        # so the callback handler doesn't know about them
        if chunk["messages"]:
          message = chunk["messages"][-1]
          reply_message = message
          #If this is a question to other party
          if (message.content.startswith("*")):
            #Uma - Push last AIMessage to other thread(brand or creator)
            #Add brand number for creator's reference and to use in creator-bot to reply to the brand-number
            #Remove the * character
            message_to_forward = message.content[1:]
            message_to_forward += 'brand_number: ' + sender_number
            modified_message = AIMessage(content=message_to_forward)
            #Forward question to other party
            process_message(opengpts_user_id, body["assistant_id"],
                            body["thread_id"], modified_message, bot_num,
                            WAPP_ID, TOKEN)
            #Change the reply_message if this is a forwarding message to creator
            reply_message.content = "Great, I'll forward this to the creator and get back to you regarding next steps."

          if (message.content.startswith("brand_number:")):
            # Uma - Push last AIMessage to other thread(brand or creator)
            # Add brand number for creator's reference and to use in creator-bot to reply to the brand-number
            # Remove the * character
            match = re.search(r'brand_number: (\d+): (.+)', message.content)
            if match:
              brand_number = match.group(1)
              extracted_text = match.group(2)
              modified_message = AIMessage(content=extracted_text)
              # Forward question to other party
              process_message(opengpts_user_id, body["assistant_id"],
                              body["thread_id"], modified_message,
                              brand_number, WAPP_ID, TOKEN)
              # Change the reply_message if this is a forwarding message to creator
              reply_message.content = "Great, I'll forward this to the brand and get back to you regarding next steps."
            else:
              print("Cannot froward from creator to brand: " + message.content)

          #Uma - Reply to user on whatsapp, thred is update by default by opengpts
          if not message.content.startswith("[Document"):
            reply_user(reply_message, sender_number, bot_num, WAPP_ID, TOKEN)

          if isinstance(message, FunctionMessage):
            streamer.output[uuid4()] = ChatGeneration(message=message)
    except Exception as e:
      await streamer.send_stream.send(e)
    finally:
      await streamer.send_stream.aclose()

  # Start the runnable in the background
  task = asyncio.create_task(consume_astream())

  # Consume the stream into an EventSourceResponse
  async def _stream() -> AsyncIterator[dict]:
    has_sent_metadata = False

    async for chunk in streamer.receive_stream:
      if isinstance(chunk, BaseException):
        yield {
            "event":
            "error",
            # Do not expose the error message to the client since
            # the message may contain sensitive information.
            # We'll add client side errors for validation as well.
            "data":
            orjson.dumps({
                "status_code": 500,
                "message": "Internal Server Error"
            }).decode(),
        }
        raise chunk
      else:
        if not has_sent_metadata and event_aggregator.callback_events:
          yield {
              "event":
              "metadata",
              "data":
              orjson.dumps({
                  "run_id": _get_base_run_id_as_str(event_aggregator)
              }).decode(),
          }
          has_sent_metadata = True

        yield {
            # EventSourceResponse expects a string for data
            # so after serializing into bytes, we decode into utf-8
            # to get a string.
            "data": _serializer.dumps(chunk).decode("utf-8"),
            "event": "data",
        }

    # Send an end event to signal the end of the stream
    yield {"event": "end"}
    # Wait for the runnable to finish
    await task

  return EventSourceResponse(_stream())


@router.get("/input_schema")
async def input_schema() -> dict:
  """Return the input schema of the runnable."""
  return agent.get_input_schema().schema()


@router.get("/output_schema")
async def output_schema() -> dict:
  """Return the output schema of the runnable."""
  return agent.get_output_schema().schema()


@router.get("/config_schema")
async def config_schema() -> dict:
  """Return the config schema of the runnable."""
  return agent.config_schema().schema()


if tracing_is_enabled():
  langsmith_client = langsmith.client.Client()

  @router.post("/feedback")
  def create_run_feedback(feedback_create_req: FeedbackCreateRequest) -> dict:
    """
        Send feedback on an individual run to langsmith

        Note that a successful response means that feedback was successfully
        submitted. It does not guarantee that the feedback is recorded by
        langsmith. Requests may be silently rejected if they are
        unauthenticated or invalid by the server.
        """

    langsmith_client.create_feedback(
        feedback_create_req.run_id,
        feedback_create_req.key,
        score=feedback_create_req.score,
        value=feedback_create_req.value,
        comment=feedback_create_req.comment,
        source_info={
            "from_langserve": True,
        },
    )

    return {"status": "ok"}
