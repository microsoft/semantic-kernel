// Copyright (c) Microsoft. All rights reserved.

namespace SemanticKernel.Service.Config;

public sealed class AzureSpeechOptions
{
    public const string PropertyName = "AzureSpeech";

    public string Region { get; set; } = string.Empty;

    public string Key { get; set; } = string.Empty;
}
