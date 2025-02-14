# Copyright (c) Microsoft. All rights reserved.

import asyncio
import os
import uuid
from logging import INFO
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
from quart import Quart, Response, json, request, websocket

from samples.demos.call_automation.create_kernel import create_kernel
from semantic_kernel import Kernel
from semantic_kernel.connectors.ai.function_choice_behavior import FunctionChoiceBehavior
from semantic_kernel.connectors.ai.open_ai import (
    AzureRealtime,
    InputAudioTranscription,
    OpenAIRealtimeExecutionSettings,
    SendEvents,
    TurnDetection,
)
from semantic_kernel.connectors.ai.realtime_client_base import RealtimeClientBase
from semantic_kernel.contents.events import RealtimeAudioEvent, RealtimeEvent

# Your ACS resource connection string
ACS_CONNECTION_STRING = os.environ["ACS_CONNECTION_STRING"]
# Callback events URI to handle callback events.
CALLBACK_URI_HOST = os.environ["CALLBACK_URI_HOST"]
CALLBACK_EVENTS_URI = CALLBACK_URI_HOST + "/api/callbacks"

acs_client = CallAutomationClient.from_connection_string(ACS_CONNECTION_STRING)
app = Quart(__name__)


@app.route("/api/incomingCall", methods=["POST"])
async def incoming_call_handler() -> Response:
    app.logger.info("incoming event data")
    for event_dict in await request.json:
        event = EventGridEvent.from_dict(event_dict)
        app.logger.info("incoming event data --> %s", event.data)
        if event.event_type == SystemEventNames.EventGridSubscriptionValidationEventName:
            app.logger.info("Validating subscription")
            validation_code = event.data["validationCode"]
            validation_response = {"validationResponse": validation_code}
            return Response(response=json.dumps(validation_response), status=200)
        if event.event_type == "Microsoft.Communication.IncomingCall":
            app.logger.info("Incoming call received: data=%s", event.data)
            if event.data["from"]["kind"] == "phoneNumber":
                caller_id = event.data["from"]["phoneNumber"]["value"]
            else:
                caller_id = event.data["from"]["rawId"]
            app.logger.info("incoming call handler caller id: %s", caller_id)
            incoming_call_context = event.data["incomingCallContext"]
            guid = uuid.uuid4()
            query_parameters = urlencode({"callerId": caller_id})
            callback_uri = f"{CALLBACK_EVENTS_URI}/{guid}?{query_parameters}"

            parsed_url = urlparse(CALLBACK_EVENTS_URI)
            websocket_url = urlunparse(("wss", parsed_url.netloc, "/ws", "", "", ""))

            app.logger.info("callback url: %s", callback_uri)
            app.logger.info("websocket url: %s", websocket_url)

            media_streaming_options = MediaStreamingOptions(
                transport_url=websocket_url,
                transport_type=MediaStreamingTransportType.WEBSOCKET,
                content_type=MediaStreamingContentType.AUDIO,
                audio_channel_type=MediaStreamingAudioChannelType.MIXED,
                start_media_streaming=True,
                enable_bidirectional=True,
                audio_format=AudioFormat.PCM24_K_MONO,
            )

            answer_call_result = await acs_client.answer_call(
                incoming_call_context=incoming_call_context,
                operation_context="incomingCall",
                callback_url=callback_uri,
                media_streaming=media_streaming_options,
            )
            app.logger.info("Answered call for connection id: %s", answer_call_result.call_connection_id)
        return Response(status=200)
    return Response(status=200)


@app.route("/api/callbacks/<contextId>", methods=["POST"])
async def callbacks(contextId):
    for event in await request.json:
        # Parsing callback events
        global call_connection_id
        event_data = event["data"]
        call_connection_id = event_data["callConnectionId"]
        app.logger.info(
            f"Received Event:-> {event['type']}, Correlation Id:-> {event_data['correlationId']}, CallConnectionId:-> {call_connection_id}"  # noqa: E501
        )
        if event["type"] == "Microsoft.Communication.CallConnected":
            call_connection_properties = await acs_client.get_call_connection(call_connection_id).get_call_properties()
            media_streaming_subscription = call_connection_properties.media_streaming_subscription
            app.logger.info(f"MediaStreamingSubscription:--> {media_streaming_subscription}")
            app.logger.info(f"Received CallConnected event for connection id: {call_connection_id}")
            app.logger.info("CORRELATION ID:--> %s", event_data["correlationId"])
            app.logger.info("CALL CONNECTION ID:--> %s", event_data["callConnectionId"])
        elif (
            event["type"] == "Microsoft.Communication.MediaStreamingStarted"
            or event["type"] == "Microsoft.Communication.MediaStreamingStopped"
        ):
            app.logger.info(f"Media streaming content type:--> {event_data['mediaStreamingUpdate']['contentType']}")
            app.logger.info(f"Media streaming status:--> {event_data['mediaStreamingUpdate']['mediaStreamingStatus']}")
            app.logger.info(
                f"Media streaming status details:--> {event_data['mediaStreamingUpdate']['mediaStreamingStatusDetails']}"  # noqa: E501
            )
        elif event["type"] == "Microsoft.Communication.MediaStreamingFailed":
            app.logger.info(
                f"Code:->{event_data['resultInformation']['code']}, Subcode:-> {event_data['resultInformation']['subCode']}"  # noqa: E501
            )
            app.logger.info(f"Message:->{event_data['resultInformation']['message']}")
        elif event["type"] == "Microsoft.Communication.CallDisconnected":
            pass
    return Response(status=200)


# WebSocket.
@app.websocket("/ws")
async def ws():
    print("Client connected to WebSocket")
    kernel = create_kernel()

    client = AzureRealtime("websocket")
    settings = OpenAIRealtimeExecutionSettings(
        instructions="""You are a chat bot. Your name is Mosscap and
    you have one goal: figure out what people need.
    Your full name, should you need to know it, is
    Splendid Speckled Mosscap. You communicate
    effectively, but you tend to answer with long
    flowery prose.""",
        turn_detection=TurnDetection(type="server_vad"),
        voice="shimmer",
        input_audio_format="pcm16",
        output_audio_format="pcm16",
        input_audio_transcription=InputAudioTranscription(model="whisper-1"),
        function_choice_behavior=FunctionChoiceBehavior.Auto(),
    )
    receive_task = asyncio.create_task(receive_messages(client, settings, kernel))
    while True:
        try:
            # Receive data from the client
            stream_data = await websocket.receive()
            data = json.loads(stream_data)
            kind = data["kind"]
            if kind == "AudioData":
                await client.send(
                    event=RealtimeEvent(
                        service_type=SendEvents.INPUT_AUDIO_BUFFER_APPEND,
                        service_event={"audio": data["audioData"]["data"]},
                    )
                )
        except Exception:
            print("Websocket connection closed.")
            break
    receive_task.cancel()


async def receive_messages(
    client: RealtimeClientBase,
    settings: OpenAIRealtimeExecutionSettings,
    kernel: Kernel,
):
    async with client(
        settings=settings,
        create_response=True,
        kernel=kernel,
    ):
        async for event in client.receive():
            match event:
                case RealtimeAudioEvent():
                    await websocket.send(
                        json.dumps({"kind": "AudioData", "audioData": {"data": event.service_event.delta}})
                    )
                case _:
                    match event.service_type:
                        case "session.created":
                            print("Session Created Message")
                            print(f"  Session Id: {event.service_event.session.id}")
                            pass
                        case "error":
                            print(f"  Error: {event.service_event.error}")
                            pass
                        case "input_audio_buffer.cleared":
                            print("Input Audio Buffer Cleared Message")
                            pass
                        case "input_audio_buffer.speech_started":
                            print(f"Voice activity detection started at {event.service_event.audio_start_ms} [ms]")
                            await websocket.send(json.dumps({"Kind": "StopAudio", "AudioData": None, "StopAudio": {}}))
                            pass
                        case "input_audio_buffer.speech_stopped":
                            pass
                        case "conversation.item.input_audio_transcription.completed":
                            print(f" User:-- {event.service_event.transcript}")
                        case "conversation.item.input_audio_transcription.failed":
                            print(f"  Error: {event.service_event.error}")
                        case "response.done":
                            print("Response Done Message")
                            print(f"  Response Id: {event.service_event.response.id}")
                            if event.service_event.response.status_details:
                                print(
                                    f"  Status Details: {event.service_event.response.status_details.model_dump_json()}"
                                )
                        case "response.audio_transcript.done":
                            print(f" AI:-- {event.service_event.transcript}")

                        case _:
                            pass


@app.route("/")
def home():
    return "Hello ACS CallAutomation!"


if __name__ == "__main__":
    app.logger.setLevel(INFO)
    app.run(port=8080)
