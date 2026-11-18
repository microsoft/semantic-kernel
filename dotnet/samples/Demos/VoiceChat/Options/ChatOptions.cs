// Copyright (c) Microsoft. All rights reserved.

using System.ComponentModel.DataAnnotations;

public class ChatOptions
{
    public const string SectionName = "Chat";

    [Required]
    public string SystemMessage { get; set; } = string.Empty;

    // Chat response streaming constants
    public int StreamingChunkSizeThreshold { get; set; } = 100;
    public double Temperature { get; set; } = 0.7;
    public int MaxTokens { get; set; } = 500;
    public double TopP { get; set; } = 0.9;
}
