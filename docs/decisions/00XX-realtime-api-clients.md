---
# These are optional elements. Feel free to remove any of them.
status: {proposed }
contact: {Eduard van Valkenburg}
date: {2025-01-10}
deciders: { Eduard van Valkenburg, Mark Wallace, Ben Thomas, Roger Barreto}
consulted: 
informed: 
---

# Realtime API Clients

## Context and Problem Statement

Multiple model providers are starting to enable realtime voice-to-voice or even multi-model-to-voice communication with their models, this includes OpenAI with their [Realtime API](https://openai.com/index/introducing-the-realtime-api/) and [Google Gemini](https://ai.google.dev/api/multimodal-live). These API's promise some very interesting new ways of using LLM's in different settings, which we want to enable with Semantic Kernel.
 The key feature that Semantic Kernel brings into this system is the ability to (re)use Semantic Kernel function as tools with these API's. There are also options for Google to use video and images as input, but for now we are focusing on the voice-to-voice part, while keeping in mind that video is coming.

The protocols that these API's use at this time are Websockets and WebRTC.

In both cases there are events being sent to and from the service, some events contain content, text, audio, or video (so far only sending, not receiving), while some events are "control" events, like content created, function call requested, etc. Sending events include, sending content, either voice, text or function call output, or events, like committing the input audio and requesting a response. 

### Websocket
Websocket has been around for a while and is a well known technology, it is a full-duplex communication protocol over a single, long-lived connection. It is used for sending and receiving messages between client and server in real-time. Each event can contain a message, which might contain a content item, or a control event. Audio is sent as a base64 encoded string.

### WebRTC
WebRTC is a Mozilla project that provides web browsers and mobile applications with real-time communication via simple application programming interfaces (APIs). It allows audio and video communication to work inside web pages and other applications by allowing direct peer-to-peer communication, eliminating the need to install plugins or download native apps. It is used for sending and receiving audio and video streams, and can be used for sending (data-)messages as well. The big difference compared to websockets is that it explicitly create a channel for audio and video, and a separate channel for "data", which are events but in this space also things like Function calls.

Both the OpenAI and Google realtime api's are in preview/beta, this means there might be breaking changes in the way they work coming in the future, therefore the clients built to support these API's are going to be experimental until the API's stabilize.

One feature that we need to consider if and how to deal with is whether or not a service uses Voice Activated Detection, OpenAI supports turning that off and allows parameters for how it behaves, while Google has it on by default and it cannot be configured.

### Event types (Websocket and partially WebRTC)

#### Client side events:
| **Content/Control event** | **Event Description**             | **OpenAI Event**             | **Google Event**                   |
| ------------------------- | --------------------------------- | ---------------------------- | ---------------------------------- |
| Control                   | Configure session                 | `session.update`             | `BidiGenerateContentSetup`         |
| Content                   | Send voice input                  | `input_audio_buffer.append`  | `BidiGenerateContentRealtimeInput` |
| Control                   | Commit input and request response | `input_audio_buffer.commit`  | `-`                                |
| Control                   | Clean audio input buffer          | `input_audio_buffer.clear`   | `-`                                |
| Content                   | Send text input                   | `conversation.item.create`   | `BidiGenerateContentClientContent` |
| Control                   | Interrupt audio                   | `conversation.item.truncate` | `-`                                |
| Control                   | Delete content                    | `conversation.item.delete`   | `-`                                |
| Control                   | Respond to function call request  | `conversation.item.create`   | `BidiGenerateContentToolResponse`  |
| Control                   | Ask for response                  | `response.create`            | `-`                                |
| Control                   | Cancel response                   | `response.cancel`            | `-`                                |

#### Server side events:
| **Content/Control event** | **Event Description**                  | **OpenAI Event**                                        | **Google Event**                          |
| ------------------------- | -------------------------------------- | ------------------------------------------------------- | ----------------------------------------- |
| Control                   | Error                                  | `error`                                                 | `-`                                       |
| Control                   | Session created                        | `session.created`                                       | `BidiGenerateContentSetupComplete`        |
| Control                   | Session updated                        | `session.updated`                                       | `BidiGenerateContentSetupComplete`        |
| Control                   | Conversation created                   | `conversation.created`                                  | `-`                                       |
| Control                   | Input audio buffer committed           | `input_audio_buffer.committed`                          | `-`                                       |
| Control                   | Input audio buffer cleared             | `input_audio_buffer.cleared`                            | `-`                                       |
| Control                   | Input audio buffer speech started      | `input_audio_buffer.speech_started`                     | `-`                                       |
| Control                   | Input audio buffer speech stopped      | `input_audio_buffer.speech_stopped`                     | `-`                                       |
| Content                   | Conversation item created              | `conversation.item.created`                             | `-`                                       |
| Content                   | Input audio transcription completed    | `conversation.item.input_audio_transcription.completed` |                                           |
| Content                   | Input audio transcription failed       | `conversation.item.input_audio_transcription.failed`    |                                           |
| Control                   | Conversation item truncated            | `conversation.item.truncated`                           | `-`                                       |
| Control                   | Conversation item deleted              | `conversation.item.deleted`                             | `-`                                       |
| Control                   | Response created                       | `response.created`                                      | `-`                                       |
| Control                   | Response done                          | `response.done`                                         | `-`                                       |
| Content                   | Response output item added             | `response.output_item.added`                            | `-`                                       |
| Content                   | Response output item done              | `response.output_item.done`                             | `-`                                       |
| Content                   | Response content part added            | `response.content_part.added`                           | `-`                                       |
| Content                   | Response content part done             | `response.content_part.done`                            | `-`                                       |
| Content                   | Response text delta                    | `response.text.delta`                                   | `BidiGenerateContentServerContent`        |
| Content                   | Response text done                     | `response.text.done`                                    | `-`                                       |
| Content                   | Response audio transcript delta        | `response.audio_transcript.delta`                       | `BidiGenerateContentServerContent`        |
| Content                   | Response audio transcript done         | `response.audio_transcript.done`                        | `-`                                       |
| Content                   | Response audio delta                   | `response.audio.delta`                                  | `BidiGenerateContentServerContent`        |
| Content                   | Response audio done                    | `response.audio.done`                                   | `-`                                       |
| Content                   | Response function call arguments delta | `response.function_call_arguments.delta`                | `BidiGenerateContentToolCall`             |
| Content                   | Response function call arguments done  | `response.function_call_arguments.done`                 | `-`                                       |
| Control                   | Function call cancelled                | `-`                                                     | `BidiGenerateContentToolCallCancellation` |
| Control                   | Rate limits updated                    | `rate_limits.updated`                                   | `-`                                       |


## Overall Decision Drivers
- Simple programming model that is likely able to handle future realtime api's and the evolution of the existing ones.
- Whenever possible we transform incoming content into Semantic Kernel content, but surface everything, so it's extensible
- Protocol agnostic, should be able to use different types of protocols under the covers, like websocket and WebRTC, without changing the client code (unless the protocol requires it), there will be slight differences in behavior depending on the protocol.

There are multiple areas where we need to make decisions, these are:
- Content and Events
- Programming model
- Audio speaker/microphone handling

# Content and Events

## Considered Options - Content and Events
Both the sending and receiving side of these integrations need to decide how to deal with the events.

1. Treat content events separate from control events
1. Treat everything as content items
1. Treat everything as events

### 1. Treat content events separate from control events
This would mean there are two mechanisms in the clients, one deals with content, and one with control events.

- Pro:
    - strongly typed responses for known content
    - easy to use as the main interactions are clear with familiar SK content types, the rest goes through a separate mechanism
- Con:
    - new content support requires updates in the codebase and can be considered breaking (potentially sending additional types back)
    - additional complexity in dealing with two streams of data

### 2. Treat everything as content items
This would mean that all events are turned into Semantic Kernel content items, and would also mean that we need to define additional content types for the control events.

- Pro:
  - everything is a content item, so it's easy to deal with
- Con:
  - overkill for simple control events

### 3. Treat everything as events
This would mean that all events are retained and returned to the developer as is, without any transformation.

- Pro:
  - no transformation needed
  - easy to maintain
- Con:
  - nothing easing the burden on the developer, they need to deal with the raw events
  - no way to easily switch between one provider and another

## Decision Outcome - Content and Events

Chosen option: ...

# Programming model

## Considered Options - Programming model
The programming model for the clients needs to be simple and easy to use, while also being able to handle the complexity of the realtime api's.

_In this section we will refer to events for both content and events, regardless of the decision made in the previous section._

1. Async generator for receiving events, that yields contents, combined with a event handler/callback mechanism for receiving events and a function for sending events
   - 1a: Single event handlers, where each event is passed to the handler
   - 1b: Multiple event handlers, where each event type has its own handler
2. Event buffers/queues that are exposed to the developer, start sending and start receiving methods, that just initiate the sending and receiving of events and thereby the filling of the buffers

### 1. Async generator for receiving events, that yields contents, combined with a event handler/callback mechanism for receiving events and a function for sending events
This would mean that the client would have a mechanism to register event handlers, and the integration would call these handlers when an event is received. For sending events, a function would be created that sends the event to the service.

- Pro:
  - without any additional setup you get content back, just as with "regular" chat models
  - event handlers are mostly for more complex interactions, so ok to be slightly more complex
- Con:
  - developer judgement needs to be made (or exposed with parameters) on what is returned through the async generator and what is passed to the event handlers

### 2. Event buffers/queues that are exposed to the developer, start sending and start receiving methods, that just initiate the sending and receiving of events and thereby the filling of the buffers
This would mean that the there are two queues, one for sending and one for receiving, and the developer can listen to the receiving queue and send to the sending queue. Internal things like parsing events to content types and auto-function calling are processed first, and the result is put in the queue, the content type should use inner_content to capture the full event and these might add a message to the send queue as well.

- Pro:
  - simple to use, just start sending and start receiving
  - easy to understand, as queues are a well known concept
  - developers can just skip events they are not interested in
- Con:
  - potentially causes audio delays because of the queueing mechanism

### 2b. Same as option 2, but with priority handling of audio content
This would mean that the audio content is handled, and passed to the developer code, and then all other events are processed.

- Pro:
  - mitigates audio delays
  - easy to understand, as queues are a well known concept
  - developers can just skip events they are not interested in
- Con:
  - Two separate mechanisms used for audio content and events

## Decision Outcome - Programming model

Chosen option: ...

# Audio speaker/microphone handling

## Considered Options - Audio speaker/microphone handling

1. Create abstraction in SK for audio handlers, that can be passed into the realtime client to record and play audio
2. Send and receive AudioContent (potentially wrapped in StreamingChatMessageContent) to the client, and let the client handle the audio recording and playing

### 1. Create abstraction in SK for audio handlers, that can be passed into the realtime client to record and play audio
This would mean that the client would have a mechanism to register audio handlers, and the integration would call these handlers when audio is received or needs to be sent. A additional abstraction for this would have to be created in Semantic Kernel (or potentially taken from a standard).

- Pro:
  - simple/local audio handlers can be shipped with SK making it easy to use
  - extensible by third parties to integrate into other systems (like Azure Communications Service)
  - could mitigate buffer issues by prioritizing audio content being sent to the handlers
- Con:
  - extra code in SK that needs to be maintained, potentially relying on third party code

### 2. Send and receive AudioContent (wrapped in StreamingChatMessageContent) to the client, and let the client handle the audio recording and playing
This would mean that the client would receive AudioContent items, and would have to deal with them itself, including recording and playing the audio.

- Pro:
  - no extra code in SK that needs to be maintained
- Con:
  - extra burden on the developer to deal with the audio 
  - harder to get started with

## Decision Outcome - Audio speaker/microphone handling

Chosen option: ...
