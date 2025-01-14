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

Multiple model providers are starting to enable realtime voice-to-voice communication with their models, this includes OpenAI with their [Realtime API](https://openai.com/index/introducing-the-realtime-api/) and [Google Gemini](https://ai.google.dev/api/multimodal-live). These API's promise some very interesting new ways of using LLM's in different settings, which we want to enable with Semantic Kernel. The key addition that Semantic Kernel brings into this system is the ability to (re)use Semantic Kernel function as tools with these API's. 

The way these API's work at this time is through either Websockets or WebRTC. 

In both cases there are events being sent to and from the service, some events contain content, text, audio, or video (so far only sending, not receiving), while some events are "control" events, like content created, function call requested, etc. Sending events include, sending content, either voice, text or function call output, or events, like committing the input audio and requesting a response. 

### Websocket
Websocket has been around for a while and is a well known technology, it is a full-duplex communication protocol over a single, long-lived connection. It is used for sending and receiving messages between client and server in real-time. Each event can contain a message, which might contain a content item, or a control event.

### WebRTC
WebRTC is a Mozilla project that provides web browsers and mobile applications with real-time communication via simple application programming interfaces (APIs). It allows audio and video communication to work inside web pages by allowing direct peer-to-peer communication, eliminating the need to install plugins or download native apps. It is used for sending and receiving audio and video streams, and can be used for sending messages as well. The big difference compared to websockets is that it does explicitly create a channel for audio and video, and a separate channel for "data", which are events but also things like Function calls.

Both the OpenAI and Google realtime api's are in preview/beta, this means there might be breaking changes in the way they work coming in the future, therefore the clients built to support these API's are going to be experimental until the API's stabilize.

One feature that we need to consider if and how to deal with is whether or not a service uses Voice Activated Detection, OpenAI supports turning that off and allows parameters for how it behaves, while Google has it on by default and it cannot be configured.

### Event types (websocket and partially webrtc)

Client side events:
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

Server side events:
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


## Decision Drivers

- Simple programming model that is likely able to handle future realtime api's and evolution of the existing ones.
- Support for the most common scenario's and content, extensible for the rest.
- Natively integrated with Semantic Kernel especially for content types and function calling.
- Support multiple types of connections, like websocket and WebRTC
  
## Decision driver questions
- For WebRTC, a audio device can be passed, should this be a requirement for the client also for websockets?

## Considered Options

Both the sending and receiving side of these integrations need to decide how to deal with the api's.

- Treat content events separate from control events
- Treat everything as content items
- Treat everything as events

### Treat content events separate from control events
This would mean there are two mechanisms in the clients, one deals with content, and one with control events.

- Pro:
    - strongly typed responses for known content
    - easy to use as the main interactions are clear with familiar SK content types, the rest goes through a separate mechanism
    - this might fit better with something like WebRTC that has distinct channels for audio and video vs a data stream for all other events
- Con:
    - new content support requires updates in the codebase and can be considered breaking (potentially sending additional types back)
    - additional complexity in dealing with two streams of data

### Treat everything as content items


## Decision Outcome

Chosen option: "{title of option 1}", because
{justification. e.g., only option, which meets k.o. criterion decision driver | which resolves force {force} | … | comes out best (see below)}.

<!-- This is an optional element. Feel free to remove. -->

### Consequences

- Good, because {positive consequence, e.g., improvement of one or more desired qualities, …}
- Bad, because {negative consequence, e.g., compromising one or more desired qualities, …}
- … <!-- numbers of consequences can vary -->

<!-- This is an optional element. Feel free to remove. -->

## Validation

{describe how the implementation of/compliance with the ADR is validated. E.g., by a review or an ArchUnit test}

<!-- This is an optional element. Feel free to remove. -->

## Pros and Cons of the Options

### {title of option 1}

<!-- This is an optional element. Feel free to remove. -->

{example | description | pointer to more information | …}

- Good, because {argument a}
- Good, because {argument b}
<!-- use "neutral" if the given argument weights neither for good nor bad -->
- Neutral, because {argument c}
- Bad, because {argument d}
- … <!-- numbers of pros and cons can vary -->

### {title of other option}

{example | description | pointer to more information | …}

- Good, because {argument a}
- Good, because {argument b}
- Neutral, because {argument c}
- Bad, because {argument d}
- …

<!-- This is an optional element. Feel free to remove. -->

## More Information

{You might want to provide additional evidence/confidence for the decision outcome here and/or
document the team agreement on the decision and/or
define when this decision when and how the decision should be realized and if/when it should be re-visited and/or
how the decision is validated.
Links to other decisions and resources might appear here as well.}
