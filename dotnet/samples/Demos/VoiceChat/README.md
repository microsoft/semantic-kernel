# Voice Chat

This sample demonstrates a simple voice chat application built with Semantic Kernel and OpenAI’s API for speech-to-text (STT), chat completion, and text-to-speech (TTS).

It captures audio from the microphone, processes it through a pipeline, and plays back the AI-generated responses:

Microphone → VAD → STT → Chat (Semantic Kernel) → TTS → Speaker

## Purpose

This is not a complete application, but a **starting point** that shows how an audio pipeline can be built using Semantic Kernel and the .NET DataFlow library.  
It’s intended to help you understand how to structure audio processing with SK, rather than provide a production-ready chat app.

## Voice Activity Detection

This demo uses **WebRTC VAD** to detect when the user starts and stops speaking.  
Other model-based approaches can also be used, such as **[Silero VAD](https://github.com/snakers4/silero-vad/tree/master/examples/csharp)**, which may provide higher accuracy.  

## Known Limitations

- **Latency**  
  This demo processes audio in discrete steps (non-streaming). Response times are therefore large, sometimes over 20 seconds.  
  To reduce latency, you should use **streaming STT and TTS services** (see below).  

- **OpenAI Free Tier Rate Limits**  
  Very high latencies can also be caused by OpenAI’s rate limits, especially on free-tier accounts. See the OpenAI [rate limits documentation](https://platform.openai.com/docs/guides/rate-limits) for more details.  

- **Latency Resources**  
  For more on latency in voice AI pipelines, see this resource: [Latency in LLM Voice Pipelines](https://voiceaiandvoiceagents.com/#latency-llm).

## Suggested Streaming Services

To reduce latency in real-world scenarios, you can integrate with streaming speech services such as:

- **Speech-to-Text (STT)**
  - [OpenAI Realtime API (Whisper streaming)](https://platform.openai.com/docs/guides/realtime)  
  - [Azure Cognitive Services Speech-to-Text](https://learn.microsoft.com/azure/cognitive-services/speech-service/speech-to-text)  
  - [Deepgram Streaming STT](https://developers.deepgram.com/docs/streaming)  
  - [AssemblyAI Streaming STT](https://www.assemblyai.com/docs/real-time-speech-recognition)  

- **Text-to-Speech (TTS)**
  - [OpenAI Realtime API (TTS streaming)](https://platform.openai.com/docs/guides/realtime)  
  - [Azure Cognitive Services Text-to-Speech](https://learn.microsoft.com/azure/cognitive-services/speech-service/text-to-speech)  
  - [Amazon Polly Neural TTS](https://docs.aws.amazon.com/polly/latest/dg/what-is.html)  

## How to Run

1. Store your API key securely with [.NET user-secrets](https://learn.microsoft.com/aspnet/core/security/app-secrets):

       dotnet user-secrets set "OpenAI:ApiKey" "your-openai-api-key"

2. Build and run the sample:

       dotnet run --project samples/Demos/VoiceChat

3. Speak into your microphone and listen for the AI response through your speakers.
