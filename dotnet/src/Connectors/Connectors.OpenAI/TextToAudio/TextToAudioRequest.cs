// Copyright (c) Microsoft. All rights reserved.

using System.Text.Json.Serialization;

namespace Microsoft.SemanticKernel.Connectors.OpenAI;

/// <summary>
/// OpenAI text-to-audio request model, see <see href="https://platform.openai.com/docs/api-reference/audio/createSpeech"/>.
/// </summary>
internal sealed class TextToAudioRequest
{
    [JsonPropertyName("model")]
    public string Model { get; set; }

    [JsonPropertyName("input")]
    public string Input { get; set; }

    [JsonPropertyName("voice")]
    public string Voice { get; set; }

    [JsonPropertyName("response_format")]
    public string ResponseFormat { get; set; } = "mp3";

    [JsonPropertyName("speed")]
    public float Speed { get; set; } = 1.0f;

    public TextToAudioRequest(string model, string input, string voice)
    {
        this.Model = model;
        this.Input = input;
        this.Voice = voice;
    }
}
