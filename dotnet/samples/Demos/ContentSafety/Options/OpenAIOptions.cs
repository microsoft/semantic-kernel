// Copyright (c) Microsoft. All rights reserved.

using System.ComponentModel.DataAnnotations;

namespace ContentSafety.Options;

public class OpenAIOptions
{
    public const string SectionName = "OpenAI";

    [Required]
    public string ModelId { get; set; }

    [Required]
    public string ApiKey { get; set; }
}
