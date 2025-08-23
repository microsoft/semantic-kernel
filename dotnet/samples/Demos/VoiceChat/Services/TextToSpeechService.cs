// Copyright (c) Microsoft. All rights reserved.

using Microsoft.Extensions.Logging;
using Microsoft.Extensions.Options;
using OpenAI.Audio;

public class TextToSpeechService
{
    // Text-to-Speech synthesis constants
    private static readonly GeneratedSpeechVoice DefaultSpeechVoice = GeneratedSpeechVoice.Alloy;  // OpenAI voice selection for TTS

    private readonly ILogger<TextToSpeechService> _logger;
    private readonly AudioClient _audioClient;

    public TextToSpeechService(ILogger<TextToSpeechService> logger, IOptions<OpenAIOptions> openAIOptions)
    {
        this._logger = logger;
        var options = openAIOptions.Value;
        this._audioClient = new AudioClient(options.SpeechModelId, options.ApiKey);
    }

    // Pipeline integration method for transforming chat events into speech events.
    public async Task<SpeechEvent> TransformAsync(ChatEvent evt) =>
        new SpeechEvent(evt.TurnId, evt.CancellationToken, await this.SynthesizeAsync(evt.Payload, evt.CancellationToken));

    // Synthesizes speech from text using OpenAI's TTS API.
    private Task<byte[]> SynthesizeAsync(string text, CancellationToken token) =>
        Tools.ExecutePipelineOperationAsync(
            operation: async () =>
            {
                BinaryData speech = await this._audioClient.GenerateSpeechAsync(text, DefaultSpeechVoice, null, token);
                return speech.ToArray();
            },
            operationName: "TTS",
            logger: this._logger,
            cancellationToken: token,
            defaultValue: Array.Empty<byte>(),
            resultFormatter: audioData => $"text: {text}. Audio size: {audioData.Length} bytes"
        );
}
