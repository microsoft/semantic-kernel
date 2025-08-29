// Copyright (c) Microsoft. All rights reserved.

using Microsoft.Extensions.Logging;
using Microsoft.Extensions.Options;
using OpenAI.Audio;

public class SpeechToTextService
{
    private const float TranscriptionTemperature = 0f;        // OpenAI transcription temperature for deterministic results
    private const string TranscriptionLanguage = "en";        // Language code for English transcription
    private const string TempAudioFileName = "audio.wav";     // Temporary filename for audio processing

    private readonly ILogger<SpeechToTextService> _logger;
    private readonly AudioClient _audioClient;
    private readonly AudioTranscriptionOptions _transcriptionOptions;

    public SpeechToTextService(ILogger<SpeechToTextService> logger, IOptions<OpenAIOptions> openAIOptions)
    {
        this._logger = logger;
        var options = openAIOptions.Value;
        this._audioClient = new AudioClient(options.TranscriptionModelId, options.ApiKey);

        // Initialize transcription options as a field
        this._transcriptionOptions = new AudioTranscriptionOptions
        {
            Temperature = TranscriptionTemperature,
            Language = TranscriptionLanguage,
        };
    }

    public async Task<TranscriptionEvent> TransformAsync(AudioEvent evt) =>
        new TranscriptionEvent(evt.TurnId, evt.CancellationToken, await this.TranscribeAsync(evt.Payload, evt.CancellationToken));

    private async Task<string?> TranscribeAsync(AudioData audioData, CancellationToken cancellationToken = default)
    {
        return await Tools.ExecutePipelineOperationAsync(
            operation: async () =>
            {
                var wavData = ConvertToWav(audioData);
                using var ms = new MemoryStream(wavData);
                AudioTranscription result = await this._audioClient.TranscribeAudioAsync(ms, TempAudioFileName, this._transcriptionOptions, cancellationToken);
                return result.Text;
            },
            operationName: "STT",
            logger: this._logger,
            cancellationToken: cancellationToken,
            defaultValue: string.Empty,
            resultFormatter: text => text ?? "No text transcribed"
        );
    }

    private static byte[] ConvertToWav(AudioData audioData)
    {
        using var ms = new MemoryStream();
        var waveFormat = new NAudio.Wave.WaveFormat(audioData.SampleRate, audioData.BitsPerSample, audioData.Channels);
        using (var writer = new NAudio.Wave.WaveFileWriter(ms, waveFormat))
        {
            writer.Write(audioData.Data, 0, audioData.Data.Length);
        }
        return ms.ToArray();
    }
}
