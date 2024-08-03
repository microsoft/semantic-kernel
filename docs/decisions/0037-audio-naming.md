---
# These are optional elements. Feel free to remove any of them.
status: proposed
contact: dmytrostruk
date: 2023-02-22
deciders: sergeymenshykh, markwallace, rbarreto, dmytrostruk
---

# Audio Abstraction and Implementation naming

## Context and Problem Statement

### Abstraction

Today we have following interfaces to work with audio:

- IAudioToTextService
- ITextToAudioService

`IAudioToTextService` accepts audio as input and returns text as output and `ITextToAudioService` accepts text as input and returns audio as output.

The naming of these abstractions does not indicate the nature of audio conversion. For example, `IAudioToTextService` interface does not indicate whether it's audio transcription or audio translation. This may be a problem and at the same time an advantage.

By having general text-to-audio and audio-to-text interfaces, it is possible to cover different types of audio conversion (transcription, translation, speech recognition, music recognition etc) using the same interface, because at the end it's just text-in/audio-out contract and vice versa. In this case, we can avoid creating multiple audio interfaces, which possibly may contain exactly the same method signature.

On the other hand, it may be a problem in case when there is a need to differentiate between specific abstractions of audio conversion inside user application or Kernel itself in the future.

### Implementation

Another problem is with audio implementation naming for OpenAI:

- AzureOpenAIAudioToTextService
- OpenAIAudioToTextService
- AzureOpenAITextToAudioService
- OpenAITextToAudioService

In this case, the naming is incorrect, because it does not use official naming from OpenAI docs, which may be confusing. For example, audio-to-text conversion is called [Speech to text](https://platform.openai.com/docs/guides/speech-to-text).

However, renaming `OpenAIAudioToTextService` to `OpenAISpeechToTextService` might not be enough, because speech to text API has 2 different endpoints - `transcriptions` and `translations`. Current OpenAI audio connector uses `transcriptions` endpoint, but the name `OpenAISpeechToTextService` won't reflect that. A possible name could be `OpenAIAudioTranscriptionService`.

## Considered Options

### [Abstraction - Option #1]

Keep the naming as it is for now (`IAudioToTextService`, `ITextToAudioService`) and use these interfaces for all audio-related connectors, until we see that some specific audio conversion won't fit into existing interface signature.

The main question for this option would be - could there be any possibility that it will be required to differentiate between audio conversion types (transcription, translation etc.) in business logic and/or Kernel itself?

Probably yes, when the application wants to use both `transcription` and `translation` in the logic. It won't be clear which audio interface should be injected to perform concrete conversion.

In this case, it's still possible to keep current interface names, but create child interfaces to specify concrete audio conversion type, for example:

```csharp
public interface IAudioTranscriptionService : IAudioToTextService {}
public interface IAudioTranslationService : IAudioToTextService {}
```

The disadvantage of it is that most probably these interfaces will be empty. The main purpose would be the ability to differentiate when using both of them.

### [Abstraction - Option #2]

Rename `IAudioToTextService` and `ITextToAudioService` to more concrete type of conversion (e.g. `ITextToSpeechService`) and for any other type of audio conversion - create a separate interface, which potentially could be exactly the same except naming.

The disadvantage of this approach is that even for the same type of conversion (e.g speech-to-text), it will be hard to pick a good name, because in different AI providers this capability is named differently, so it will be hard to avoid inconsistency. For example, in OpenAI it's [Audio transcription](https://platform.openai.com/docs/api-reference/audio/createTranscription) while in Hugging Face it's [Automatic Speech Recognition](https://huggingface.co/models?pipeline_tag=automatic-speech-recognition).

The advantage of current name (`IAudioToTextService`) is that it's more generic and cover both Hugging Face and OpenAI services. It's named not after AI capability, but rather interface contract (audio-in/text-out).

### [Implementation]

As for implementations, there are two options as well - keep it as it is or rename classes based on how the capability is called by AI provider and most probably renaming is the best choice here, because from the user point of view, it will be easier to understand which concrete OpenAI capability is used (e.g. `transcription` or `translation`), so it will be easier to find related documentation about it and so on.

Proposed renaming:

- AzureOpenAIAudioToTextService -> AzureOpenAIAudioTranscriptionService
- OpenAIAudioToTextService -> OpenAIAudioTranscriptionService
- AzureOpenAITextToAudioService -> AzureOpenAITextToSpeechService
- OpenAITextToAudioService -> OpenAITextToSpeechService

## Naming comparison

| AI Provider  | Audio conversion    | Proposed Interface         | Proposed Implementation             |
| ------------ | ------------------- | -------------------------- | ----------------------------------- |
| Microsoft    | Speech-to-text      | IAudioTranscriptionService | MicrosoftSpeechToTextService        |
| Hugging Face | Speech recognition  | IAudioTranscriptionService | HuggingFaceSpeechRecognitionService |
| AssemblyAI   | Transcription       | IAudioTranscriptionService | AssemblyAIAudioTranscriptionService |
| OpenAI       | Audio transcription | IAudioTranscriptionService | OpenAIAudioTranscriptionService     |
| Google       | Speech-to-text      | IAudioTranscriptionService | GoogleSpeechToTextService           |
| Amazon       | Transcription       | IAudioTranscriptionService | AmazonAudioTranscriptionService     |
| Microsoft    | Speech translation  | IAudioTranslationService   | MicrosoftSpeechTranslationService   |
| OpenAI       | Audio translation   | IAudioTranslationService   | OpenAIAudioTranslationService       |
| Meta         | Text-to-music       | ITextToMusicService        | MetaTextToMusicService              |
| Microsoft    | Text-to-speech      | ITextToSpeechService       | MicrosoftTextToSpeechService        |
| OpenAI       | Text-to-speech      | ITextToSpeechService       | OpenAITextToSpeechService           |
| Google       | Text-to-speech      | ITextToSpeechService       | GoogleTextToSpeechService           |
| Amazon       | Text-to-speech      | ITextToSpeechService       | AmazonTextToSpeechService           |
| Hugging Face | Text-to-speech      | ITextToSpeechService       | HuggingFaceTextToSpeechService      |
| Meta         | Text-to-sound       | TBD                        | TBD                                 |
| Hugging Face | Text-to-audio       | TBD                        | TBD                                 |
| Hugging Face | Audio-to-audio      | TBD                        | TBD                                 |

## Decision Outcome

Rename already existing audio connectors to follow provided naming in `Naming comparison` table and use the same naming for future audio abstractions and implementations.
