// Copyright (c) Microsoft. All rights reserved.

using System.ComponentModel.DataAnnotations;

namespace ContentSafety.Options;

public class AzureOpenAIOptions
{
    public const string SectionName = "AzureOpenAI";

    [Required]
    public string DeploymentName { get; set; }

    [Required]
    public string Endpoint { get; set; }

    [Required]
    public string ApiKey { get; set; }
}
