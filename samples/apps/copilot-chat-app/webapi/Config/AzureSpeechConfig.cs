// Copyright (c) Microsoft. All rights reserved.

namespace SemanticKernel.Service.Config;

#pragma warning disable CA1812 // Avoid uninstantiated internal classes - Instantiated by deserializing JSON
internal class AzureSpeechConfig
#pragma warning restore CA1812 // Avoid uninstantiated internal classes
{
    public string Label { get; set; } = string.Empty;
    public string Region { get; set; } = string.Empty;
    public string Key { get; set; } = string.Empty;

    public bool IsValid()
    {
        return
            !string.IsNullOrEmpty(this.Label) &&
            !string.IsNullOrEmpty(this.Region) &&
            !string.IsNullOrEmpty(this.Key);
    }
}
