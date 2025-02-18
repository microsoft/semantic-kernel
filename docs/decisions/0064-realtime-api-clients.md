---
# These are optional elements. Feel free to remove any of them.
status: {proposed }
contact: {Eduard van Valkenburg}
date: { 2025-01-31 }
deciders: { Eduard van Valkenburg, Mark Wallace, Ben Thomas, Shawn Henry }
consulted: { Weslie Steyn, Roger Barreto, Ben Thomas, Mark Wallace, Sergey Menshykh, Evan Mattson }
informed: { Tao Chen, Dmytro Struk }
---

# Multi-modal Realtime API Clients

## Context and Problem Statement

Multiple model providers are starting to enable realtime voice-to-voice or even multi-modal, realtime, two-way communication with their models, this includes OpenAI with their [Realtime API](https://openai.com/index/introducing-the-realtime-api/) and [Google Gemini](https://ai.google.dev/api/multimodal-live). These API's promise some very interesting new ways of using LLM's for different scenario's, which we want to enable with Semantic Kernel.

The key feature that Semantic Kernel brings into this system is the ability to (re)use Semantic Kernel function as tools with these API's. There are also options for Google to use video and images as input, this will likely not be implemented first, but the abstraction should be able to deal with it.

At this time, the protocols that these API's use are Websockets and WebRTC.

In both cases there are events being sent to and from the service, some events contain content, text, audio, or video (so far only sending, not receiving), while some events are "control" events, like content created, function call requested, etc. Sending events include, sending content, either voice, text or function call output, or events, like committing the input audio and requesting a response. 

### Websocket
Websocket has been around for a while and is a well known technology, it is a full-duplex communication protocol over a single, long-lived connection. It is used for sending and receiving messages between client and server in real-time. Each event can contain a message, which might contain a content item, or a control event. Audio is sent as a base64 encoded string that is part of a event.

### WebRTC
WebRTC is a Mozilla project that provides web browsers and mobile applications with real-time communication via simple APIs. It allows audio and video communication to work inside web pages and other applications by allowing direct peer-to-peer communication, eliminating the need to install plugins or download native apps. It is used for sending and receiving audio and video streams, and can be used for sending (data-)messages as well. The big difference compared to websockets is that it explicitly create a channel for audio and video, and a separate channel for "data", which are events and in this space that contains all non-AV content, text, function calls, function results and control events, like errors or acknowledgements.

Both the OpenAI and Google realtime api's are in preview/beta, this means there might be breaking changes in the way they work coming in the future, therefore the clients built to support these API's are going to be experimental until the API's stabilize.

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
- Abstract away the underlying protocols, so that developers can build applications that implement whatever protocol they want to support, without having to change the client code when changing models or protocols.
  - There are some limitations expected here as i.e. WebRTC requires different information at session create time than websockets.
- Simple programming model that is likely able to handle future realtime api's and the evolution of the existing ones.
- Whenever possible we transform incoming content into Semantic Kernel content, but surface everything, so it's extensible for developers and in the future.

There are multiple areas where we need to make decisions, these are:
- Content and Events
- Programming model
- Audio speaker/microphone handling
- Interface design and naming

# Content and Events

## Considered Options - Content and Events
Both the sending and receiving side of these integrations need to decide how to deal with the events.

1. Treat content separate from control
1. Treat everything as content items
1. Treat everything as events

### 1. Treat content separate from control
This would mean there are two mechanisms in the clients, one deals with content, and one with control events.

- Pro:
    - strongly typed responses for known content
    - easy to use as the main interactions are clear with familiar SK content types, the rest goes through a separate mechanism
- Con:
    - new content support requires updates in the codebase and can be considered breaking (potentially sending additional types back)
    - additional complexity in dealing with two streams of data
    - some items, such as Function calls can be considered both content and control, control when doing auto-function calling, but content when the developer wants to deal with it themselves

### 2. Treat everything as content items
This would mean that all events are turned into Semantic Kernel content items, and would also mean that we need to define additional content types for the control events.

- Pro:
  - everything is a content item, so it's easy to deal with
- Con:
  - new content type needed for control events

### 3. Treat everything as events
This would introduce events, each event has a type, those can be core content types, like audio, video, image, text, function call or function response, as well as a generic event for control events without content. Each event has a SK type, from above as well as a service_event field that contains the event type from the service. Finally the event has a content field, which corresponds to the type, and for the generic event contains the raw event from the service.

- Pro:
  - no transformation needed for service events
  - easy to maintain and extend
- Con:
  - new concept introduced
  - might be confusing to have contents with and without SK type

## Decision Outcome - Content and Events

Chosen option: 3 Treat Everything as Events

This option was chosen to allow abstraction away from the raw events, while still allowing the developer to access the raw events if needed. 
A set of events are defined, for basic types, like 'audio', 'text', 'function_call', 'function_result', it then has two other fields, service_event which is filled with the event type from the service and a field for the actual content, with a name that corresponds to the event type, the actual content should use the inner_content field to capture the raw event.

It might also be possible that a single event from the service contains multiple content items, for instance a response might contain both text and audio, in that case multiple events will be emitted. It might also be that a single service event is represented twice, i.e. once as a AudioEvent and once as a ServiceEvent, this once again gives the most flexibility to the developer.

```python
AudioEvent(
  event_type="audio",
  service_event="response.audio.delta",
  audio: AudioContent(...)
)
```

```python
TextEvent(
  event_type="text",
  service_event="response.text.delta",
  text: TextContent(...)
)
```

```python
FunctionCallEvent(
  event_type="function_call",
  service_event="response.function_call_arguments.delta",
  function_call: FunctionCallContent(...)
)
```

```python
FunctionResultEvent(
  event_type="function_result",
  service_event="response.output_item.added",
  function_result: FunctionResultContent(...)
)
```

```python
ImageEvent(
  event_type="image",
  service_event="response.image.delta",
  image: ImageContent(...)
)
```

Next to these we will have a generic event, called ServiceEvent, this is the catch-all, which has event_type: "service", the service_event field filled with the event type from the service and a field called 'event' which contains the raw event from the service.

```python
ServiceEvent(
  event_type="service",
  service_event="conversation.item.create",
  event: { ... }
)
```

This allows you to easily do pattern matching on the event_type, and then use the service_event to filter on the specific event type for service events, or just grab the contents for the other ones.

Collectively these are known as *RealtimeEvents*, and are returned as an async generator from the client, so you can easily loop over them. And they are passed to the send method.

One open item is whether to include a extra field in these types for tracking related pieces, however this becomes problematic because the way those are generated differs per service and is quite complex, for instance the OpenAI API returns a piece of audio transcript with the following ids: 
- `event_id`: the unique id of the event
- `response_id`: the id of the response
- `item_id`: the id of the item
- `output_index`: the index of the output item in the response
- `content_index`: The index of the content part in the item's content array

While Google has ID's only in some content items, like function calls, but not for audio or text content.

Since the id's are always available through the raw event (either as inner_content or as .event), it is not necessary to add them to the content types, and it would make the content types more complex and harder to reuse across services.

### Rejected ideas
Wrapping content in a `(Streaming)ChatMessageContent` first, this will add another layer of complexity and since a CMC can contain multiple items, to access audio, would look like this: `event.content.items[0].audio.data`, which is not as clear as `event.audio.data`.

# Programming model

## Considered Options - Programming model
The programming model for the clients needs to be simple and easy to use, while also being able to handle the complexity of the realtime api's.

_In this section we will refer to events for both content and events, regardless of the decision made in the previous section._

This is mostly about the receiving side of things, sending is much simpler.

1. Event handlers, developers register handlers for specific events, and the client calls these handlers when an event is received
   - 1a: Single event handlers, where each event is passed to the handler
   - 1b: Multiple event handlers, where each event type has its own handler(s)
2. Event buffers/queues that are exposed to the developer, start sending and start receiving methods, that just initiate the sending and receiving of events and thereby the filling of the buffers
3. AsyncGenerator that yields Events

### 1. Event handlers, developers register handlers for specific events, and the client calls these handlers when an event is received
This would mean that the client would have a mechanism to register event handlers, and the integration would call these handlers when an event is received. For sending events, a function would be created that sends the event to the service.

- Pro:
  - no need to deal with complex things like async generators and easier to keep track of what events you want to respond to
- Con:
  - can become cumbersome, and in 1b would require updates to support new events
  - things like ordering (which event handler is called first) are unclear to the developer

### 2. Event buffers/queues that are exposed to the developer, start sending and start receiving methods, that just initiate the sending and receiving of events and thereby the filling of the buffers
This would mean that there are two queues, one for sending and one for receiving, and the developer can listen to the receiving queue and send to the sending queue. Internal things like parsing events to content types and auto-function calling are processed first, and the result is put in the queue, the content type should use inner_content to capture the full event and these might add a message to the send queue as well.

- Pro:
  - simple to use, just start sending and start receiving
  - easy to understand, as queues are a well known concept
  - developers can just skip events they are not interested in
- Con:
  - potentially causes audio delays because of the queueing mechanism

### 2b. Same as option 2, but with priority handling of audio content
This would mean that the audio content is handled first and sent to a callback directly so that the developer can play it or send it onward as soon as possible, and then all other events are processed (like text, function calls, etc) and put in the queue.

- Pro:
  - mitigates audio delays
  - easy to understand, as queues are a well known concept
  - developers can just skip events they are not interested in
- Con:
  - Two separate mechanisms used for audio content and events

### 3. AsyncGenerator that yields Events
This would mean that the clients implement a function that yields events, and the developer can loop through it and deal with events as they come.

- Pro:
  - easy to use, just loop through the events
  - easy to understand, as async generators are a well known concept
  - developers can just skip events they are not interested in
- Con:
  - potentially causes audio delays because of the async nature of the generator
  - lots of events types mean a large single set of code to handle it all

### 3b. Same as option 3, but with priority handling of audio content
This would mean that the audio content is handled first and sent to a callback directly so that the developer can play it or send it onward as soon as possible, and then all other events are parsed and yielded.

- Pro:
  - mitigates audio delays
  - easy to understand, as async generators are a well known concept
- Con:
  - Two separate mechanisms used for audio content and events
  
## Decision Outcome - Programming model

Chosen option: 3b AsyncGenerator that yields Events combined with priority handling of audio content through a callback

This makes the programming model very easy, a minimal setup that should work for every service and protocol would look like this:
```python
async for event in realtime_client.start_streaming():
    match event.event_type:
        case "audio":
            await audio_player.add_audio(event.audio)
        case "text":
            print(event.text.text)
```

# Audio speaker/microphone handling

## Considered Options - Audio speaker/microphone handling

1. Create abstraction in SK for audio handlers, that can be passed into the realtime client to record and play audio
2. Send and receive AudioContent to the client, and let the client handle the audio recording and playing

### 1. Create abstraction in SK for audio handlers, that can be passed into the realtime client to record and play audio
This would mean that the client would have a mechanism to register audio handlers, and the integration would call these handlers when audio is received or needs to be sent. A additional abstraction for this would have to be created in Semantic Kernel (or potentially taken from a standard).

- Pro:
  - simple/local audio handlers can be shipped with SK making it easy to use
  - extensible by third parties to integrate into other systems (like Azure Communications Service)
  - could mitigate buffer issues by prioritizing audio content being sent to the handlers
- Con:
  - extra code in SK that needs to be maintained, potentially relying on third party code
  - audio drivers can be platform specific, so this might not work well or at all on all platforms

### 2. Send and receive AudioContent to the client, and let the client handle the audio recording and playing
This would mean that the client would receive AudioContent items, and would have to deal with them itself, including recording and playing the audio.

- Pro:
  - no extra code in SK that needs to be maintained
- Con:
  - extra burden on the developer to deal with the audio 
  - harder to get started with

## Decision Outcome - Audio speaker/microphone handling

Chosen option: Option 2: there are vast difference in audio format, frame duration, sample rate and other audio settings, that a default that works *always* is not feasible, and the developer will have to deal with this anyway, so it's better to let them deal with it from the start, we will add sample audio handlers to the samples to still allow people to get started with ease. 

# Interface design

The following methods will need to be supported:
- create session
- update session
- close session
- listen for/receive events
- send events

## Considered Options - Interface design

1. Use a single class for everything
2. Split the service class from a session class.

### 1. Use a single class for everything

Each implementation would have to implements all of the above methods. This means that non-protocol specific elements are in the same class as the protocol specific elements and will lead to code duplication between them.

### 2. Split the service class from a session class.

Two interfaces are created:
- Service: create session, update session, delete session, maybe list sessions?
- Session: listen for/receive events, send events, update session, close session

Currently neither the google or the openai api's support restarting sessions, so the advantage of splitting is mostly a implementation question but will not add any benefits to the developer. This means that the split would be far simpler:
- Service: create session
- Session: listen for/receive events, send events, update session, close session

## Naming

The send and listen/receive methods need to be clear in the way their are named and this can become confusing when dealing with these api's. The following options are considered:

Options for sending events to the service from your code:
- google uses .send in their client.
- OpenAI uses .send in their client as well
- send or send_message is used in other clients, like Azure Communication Services

Options for listening for events from the service in your code:
- google uses .receive in their client.
- openai uses .recv in their client.
- others use receive or receive_messages in their clients.

### Decision Outcome - Interface design

Chosen option: Use a single class for everything
Chosen for send and receive as verbs.

This means that the interface will look like this:
```python

class RealtimeClient:
    async def create_session(self, settings: PromptExecutionSettings, chat_history: ChatHistory, **kwargs) -> None:
        ...

    async def update_session(self, settings: PromptExecutionSettings, chat_history: ChatHistory, **kwargs) -> None:
        ...

    async def close_session(self, **kwargs) -> None:
        ...

    async def receive(self, **kwargs) -> AsyncGenerator[RealtimeEvent, None]:
        ...

    async def send(self, event: RealtimeEvent) -> None:
        ...
```

In most cases, create_session should call update_session with the same parameters, since update session can also be done separately later on with the same inputs.

For Python a default __aenter__ and __aexit__ method should be added to the class, so it can be used in a with statement, which calls create_session and close_session respectively.

It is advisable, but not required, to implement the send method through a buffer/queue so that events can be 'sent' before the sessions has been established without losing them or raising exceptions, this might take a few seconds and in that time a single send call would block the application.

The send method should handle all events types, but it might have to handle the same thing in two ways, for instance:
```python
audio = AudioContent(...)

await client.send(AudioEvent(event_type='audio', audio=audio))
```

should be equivalent to (for the OpenAI API):
```python
audio = AudioContent(...)

await client.send(ServiceEvent(event_type='service', service_event='input_audio_buffer.append', event=audio))
```

The first version allows one to have the exact same code for all services, while the second version is also correct and should be handled correctly as well, this once again allows for flexibility and simplicity, when audio needs to be sent to with a different event type, that is still possible in the second way, while the first uses the "default" event type for that particular service, this would be required to seed the conversation with completed audio snippets from a previous session, rather then just the transcripts, the completed audio, needs to be of event type 'conversation.item.create' for OpenAI, while a streamed 'frame' of audio would be 'input_audio_buffer.append' and that would be the default to use.

