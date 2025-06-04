# Copyright (c) Microsoft. All rights reserved.

####################################################################
# Sample Quart webapp with that connects to Azure OpenAI           #
# Make sure to install `uv`, see:                                  #
# https://docs.astral.sh/uv/getting-started/installation/          #
# and rename .env.example to .env and fill in the values.          #
# Follow the guidance in README.md for more info.                  #
# To run the app, use:                                             #
# `uv run --env-file .env call_automation.py`                     #
####################################################################
#
# /// script
# requires-python = ">=3.12"
# dependencies = [
#     "Quart",
#     "azure-eventgrid",
#     "azure-communication-callautomation==1.4.0b1",
#     "semantic-kernel",
# ]
# ///
import asyncio
import base64
import logging
import os
import uuid
from datetime import datetime
from random import randint
from urllib.parse import urlencode, urlparse, urlunparse

from azure.communication.callautomation import (
    AudioFormat,
    MediaStreamingAudioChannelType,
    MediaStreamingContentType,
    MediaStreamingOptions,
    MediaStreamingTransportType,
)
from azure.communication.callautomation.aio import CallAutomationClient
from azure.eventgrid import EventGridEvent, SystemEventNames
from numpy import ndarray
from quart import Quart, Response, json, request, websocket

from semantic_kernel import Kernel
from semantic_kernel.connectors.ai import FunctionChoiceBehavior
from semantic_kernel.connectors.ai.open_ai import (
    AzureRealtimeExecutionSettings,
    AzureRealtimeWebsocket,
)
from semantic_kernel.connectors.ai.open_ai.services._open_ai_realtime import ListenEvents
from semantic_kernel.connectors.ai.realtime_client_base import RealtimeClientBase
from semantic_kernel.contents import AudioContent, RealtimeAudioEvent
from semantic_kernel.functions import kernel_function

# Callback events URI to handle callback events.
CALLBACK_URI_HOST = os.environ["CALLBACK_URI_HOST"]
CALLBACK_EVENTS_URI = CALLBACK_URI_HOST + "/api/callbacks"

acs_client = CallAutomationClient.from_connection_string(os.environ["ACS_CONNECTION_STRING"])
app = Quart(__name__)

# region: Semantic Kernel

kernel = Kernel()


class HelperPlugin:
    """Helper plugin for the Semantic Kernel."""

    @kernel_function
    def get_weather(self, location: str) -> str:
        """Get the weather for a location."""
        app.logger.info(f"@ Getting weather for {location}")
        weather_conditions = ("sunny", "hot", "cloudy", "raining", "freezing", "snowing")
        weather = weather_conditions[randint(0, len(weather_conditions) - 1)]  # nosec
        return f"The weather in {location} is {weather}."

    @kernel_function
    def get_date_time(self) -> str:
        """Get the current date and time."""
        app.logger.info("@ Getting current datetime")
        return f"The current date and time is {datetime.now().isoformat()}."

    @kernel_function
    async def goodbye(self):
        """When the user is done, say goodbye and then call this function."""
        app.logger.info("@ Goodbye has been called!")
        global call_connection_id
        await acs_client.get_call_connection(call_connection_id).hang_up(is_for_everyone=True)


kernel.add_plugin(plugin=HelperPlugin(), plugin_name="helpers", description="Helper functions for the realtime client.")

# region: Handlers for audio and data streams


async def from_realtime_to_acs(audio: ndarray):
    """Function that forwards the audio from the model to the websocket of the ACS client."""
    app.logger.debug("Audio received from the model, sending to ACS client")
    await websocket.send(
        json.dumps({"kind": "AudioData", "audioData": {"data": base64.b64encode(audio.tobytes()).decode("utf-8")}})
    )


async def from_acs_to_realtime(client: RealtimeClientBase):
    """Function that forwards the audio from the ACS client to the model."""
    while True:
        try:
            # Receive data from the ACS client
            stream_data = await websocket.receive()
            data = json.loads(stream_data)
            if data["kind"] == "AudioData":
                # send it to the Realtime service
                await client.send(
                    event=RealtimeAudioEvent(
                        audio=AudioContent(data=data["audioData"]["data"], data_format="base64", inner_content=data),
                    )
                )
        except Exception:
            app.logger.info("Websocket connection closed.")
            break


async def handle_realtime_messages(client: RealtimeClientBase):
    """Function that handles the messages from the Realtime service.

    This function only handles the non-audio messages.
    Audio is done through the callback so that it is faster and smoother.
    """
    async for event in client.receive(audio_output_callback=from_realtime_to_acs):
        match event.service_type:
            case ListenEvents.SESSION_CREATED:
                app.logger.info("Session Created Message")
                app.logger.debug(f"  Session Id: {event.service_event.session.id}")
            case ListenEvents.ERROR:
                app.logger.error(f"  Error: {event.service_event.error}")
            case ListenEvents.INPUT_AUDIO_BUFFER_CLEARED:
                app.logger.info("Input Audio Buffer Cleared Message")
            case ListenEvents.INPUT_AUDIO_BUFFER_SPEECH_STARTED:
                app.logger.debug(f"Voice activity detection started at {event.service_event.audio_start_ms} [ms]")
                await websocket.send(json.dumps({"Kind": "StopAudio", "AudioData": None, "StopAudio": {}}))
            case ListenEvents.CONVERSATION_ITEM_INPUT_AUDIO_TRANSCRIPTION_COMPLETED:
                app.logger.info(f" User:-- {event.service_event.transcript}")
            case ListenEvents.CONVERSATION_ITEM_INPUT_AUDIO_TRANSCRIPTION_FAILED:
                app.logger.error(f"  Error: {event.service_event.error}")
            case ListenEvents.RESPONSE_DONE:
                app.logger.info("Response Done Message")
                app.logger.debug(f"  Response Id: {event.service_event.response.id}")
                if event.service_event.response.status_details:
                    app.logger.debug(
                        f"  Status Details: {event.service_event.response.status_details.model_dump_json()}"
                    )
            case ListenEvents.RESPONSE_AUDIO_TRANSCRIPT_DONE:
                app.logger.info(f" AI:-- {event.service_event.transcript}")


# region: Routes


# WebSocket.
@app.websocket("/ws")
async def ws():
    app.logger.info("Client connected to WebSocket")
    client = AzureRealtimeWebsocket()
    settings = AzureRealtimeExecutionSettings(
        instructions="""You are a chat bot. Your name is Mosscap and
    you have one goal: figure out what people need.
    Your full name, should you need to know it, is
    Splendid Speckled Mosscap. You communicate
    effectively, but you tend to answer with long
    flowery prose.""",
        turn_detection={"type": "server_vad"},
        voice="shimmer",
        input_audio_format="pcm16",
        output_audio_format="pcm16",
        input_audio_transcription={"model": "whisper-1"},
        function_choice_behavior=FunctionChoiceBehavior.Auto(),
    )

    # create the realtime client session
    async with client(settings=settings, create_response=True, kernel=kernel):
        # start handling the messages from the realtime client
        # and allow the callback to be used to forward the audio to the acs client
        receive_task = asyncio.create_task(handle_realtime_messages(client))
        # receive messages from the ACS client and send them to the realtime client
        await from_acs_to_realtime(client)
        receive_task.cancel()


@app.route("/api/incomingCall", methods=["POST"])
async def incoming_call_handler() -> Response:
    for event_dict in await request.json:
        event = EventGridEvent.from_dict(event_dict)
        match event.event_type:
            case SystemEventNames.EventGridSubscriptionValidationEventName:
                app.logger.info("Validating subscription")
                validation_code = event.data["validationCode"]
                validation_response = {"validationResponse": validation_code}
                return Response(response=json.dumps(validation_response), status=200)
            case SystemEventNames.AcsIncomingCallEventName:
                app.logger.debug("Incoming call received: data=%s", event.data)
                caller_id = (
                    event.data["from"]["phoneNumber"]["value"]
                    if event.data["from"]["kind"] == "phoneNumber"
                    else event.data["from"]["rawId"]
                )
                app.logger.info("incoming call handler caller id: %s", caller_id)
                incoming_call_context = event.data["incomingCallContext"]
                guid = uuid.uuid4()
                query_parameters = urlencode({"callerId": caller_id})
                callback_uri = f"{CALLBACK_EVENTS_URI}/{guid}?{query_parameters}"

                parsed_url = urlparse(CALLBACK_EVENTS_URI)
                websocket_url = urlunparse(("wss", parsed_url.netloc, "/ws", "", "", ""))

                app.logger.debug("callback url: %s", callback_uri)
                app.logger.debug("websocket url: %s", websocket_url)

                answer_call_result = await acs_client.answer_call(
                    incoming_call_context=incoming_call_context,
                    operation_context="incomingCall",
                    callback_url=callback_uri,
                    media_streaming=MediaStreamingOptions(
                        transport_url=websocket_url,
                        transport_type=MediaStreamingTransportType.WEBSOCKET,
                        content_type=MediaStreamingContentType.AUDIO,
                        audio_channel_type=MediaStreamingAudioChannelType.MIXED,
                        start_media_streaming=True,
                        enable_bidirectional=True,
                        audio_format=AudioFormat.PCM24_K_MONO,
                    ),
                )
                app.logger.info(f"Answered call for connection id: {answer_call_result.call_connection_id}")
            case _:
                app.logger.debug("Event type not handled: %s", event.event_type)
                app.logger.debug("Event data: %s", event.data)
        return Response(status=200)
    return Response(status=200)


@app.route("/api/callbacks/<contextId>", methods=["POST"])
async def callbacks(contextId):
    for event in await request.json:
        # Parsing callback events
        global call_connection_id
        event_data = event["data"]
        call_connection_id = event_data["callConnectionId"]
        app.logger.debug(
            f"Received Event:-> {event['type']}, Correlation Id:-> {event_data['correlationId']}, CallConnectionId:-> {call_connection_id}"  # noqa: E501
        )
        match event["type"]:
            case "Microsoft.Communication.CallConnected":
                call_connection_properties = await acs_client.get_call_connection(
                    call_connection_id
                ).get_call_properties()
                media_streaming_subscription = call_connection_properties.media_streaming_subscription
                app.logger.info(f"MediaStreamingSubscription:--> {media_streaming_subscription}")
                app.logger.info(f"Received CallConnected event for connection id: {call_connection_id}")
                app.logger.debug("CORRELATION ID:--> %s", event_data["correlationId"])
                app.logger.debug("CALL CONNECTION ID:--> %s", event_data["callConnectionId"])
            case "Microsoft.Communication.MediaStreamingStarted" | "Microsoft.Communication.MediaStreamingStopped":
                app.logger.debug(
                    f"Media streaming content type:--> {event_data['mediaStreamingUpdate']['contentType']}"
                )
                app.logger.debug(
                    f"Media streaming status:--> {event_data['mediaStreamingUpdate']['mediaStreamingStatus']}"
                )
                app.logger.debug(
                    f"Media streaming status details:--> {event_data['mediaStreamingUpdate']['mediaStreamingStatusDetails']}"  # noqa: E501
                )
            case "Microsoft.Communication.MediaStreamingFailed":
                app.logger.warning(
                    f"Code:->{event_data['resultInformation']['code']}, Subcode:-> {event_data['resultInformation']['subCode']}"  # noqa: E501
                )
                app.logger.warning(f"Message:->{event_data['resultInformation']['message']}")
            case "Microsoft.Communication.CallDisconnected":
                app.logger.debug(f"Call disconnected for connection id: {call_connection_id}")
    return Response(status=200)


@app.route("/")
def home():
    return "Hello SKxACS CallAutomation!"


# region: Main


if __name__ == "__main__":
    app.logger.setLevel(logging.INFO)
    app.run(port=8080)
