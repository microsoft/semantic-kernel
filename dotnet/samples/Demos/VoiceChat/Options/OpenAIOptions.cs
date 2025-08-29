// Copyright (c) Microsoft. All rights reserved.

using System.ComponentModel.DataAnnotations;

public class OpenAIOptions
{
    public const string SectionName = "OpenAI";

    [Required]
    public string ApiKey { get; set; } = string.Empty;

    [Required]
    public string ChatModelId { get; set; } = "gpt-4";

    [Required]
    public string TranscriptionModelId { get; set; } = "gpt-4o-transcribe";

    [Required]
    public string SpeechModelId { get; set; } = "gpt-4o-mini-tts";
}
