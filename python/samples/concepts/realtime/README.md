# Realtime Multi-modal API Samples

These samples are more complex then most because of the nature of these API's. They are designed to be run in real-time and require a microphone and speaker to be connected to your computer.

To run these samples, you will need to have the following setup:

- Environment variables for OpenAI (websocket or WebRTC), with your key and OPENAI_REALTIME_MODEL_ID set.
- Environment variables for Azure (websocket only), set with your endpoint, optionally a key and AZURE_OPENAI_REALTIME_DEPLOYMENT_NAME set. The API version needs to be at least `2024-10-01-preview`.
- To run the sample with a simple version of a class that handles the incoming and outgoing sound you need to install the following packages in your environment:
  - semantic-kernel[realtime]
  - pyaudio
  - sounddevice
  - pydub
    e.g. pip install pyaudio sounddevice pydub semantic-kernel[realtime]

The samples all run as python scripts, that can either be started directly or through your IDE.

All demos have a similar output, where the instructions are printed, each new *response item* from the API is put into a new `Mosscap (transcript):` line. The nature of these api's is such that the transcript arrives before the spoken audio, so if you interrupt the audio the transcript will not match the audio.

The realtime api's work by sending event from the server to you and sending events back to the server, this is fully asynchronous. The samples show you can listen to the events being sent by the server and some are handled by the code in the samples, others are not. For instance one could add a clause in the match case in the receive loop that logs the usage that is part of the `response.done` event.

For more info on the events, go to our documentation, as well as the documentation of [OpenAI](https://platform.openai.com/docs/guides/realtime) and [Azure](https://learn.microsoft.com/en-us/azure/ai-services/openai/realtime-audio-quickstart?tabs=keyless%2Cmacos&pivots=programming-language-python).

## Simple chat samples

### [Simple chat with realtime websocket](./simple_realtime_chat_websocket.py)

This sample uses the websocket api with Azure OpenAI to run a simple interaction based on voice. If you want to use this sample with OpenAI, just change AzureRealtimeWebsocket into OpenAIRealtimeWebsocket.

### [Simple chat with realtime WebRTC](./simple_realtime_chat_webrtc.py)

This sample uses the WebRTC api with OpenAI to run a simple interaction based on voice. Because of the way the WebRTC protocol works this needs a different player and recorder than the websocket version.

## Function calling samples

The following two samples use function calling with the following functions:

- get_weather: This function will return the weather for a given city, it is randomly generated and not based on any real data.
- get_time: This function will return the current time and date.
- goodbye: This function will end the conversation.

A line is logged whenever one of these functions is called.

### [Chat with function calling Websocket](./realtime_agent_with_function_calling_websocket.py)

This sample uses the websocket api with Azure OpenAI to run a voice agent, capable of taking actions on your behalf.

### [Chat with function calling WebRTC](./realtime_agent_with_function_calling_webrtc.py)

This sample uses the WebRTC api with OpenAI to run a voice agent, capable of taking actions on your behalf.
