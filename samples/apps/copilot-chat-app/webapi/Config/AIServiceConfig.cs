// Copyright (c) Microsoft. All rights reserved.

// TODO: align with SK naming and expand to have all fields from both AzureOpenAIConfig and OpenAIConfig
// Or actually split this into two classes

namespace SemanticKernel.Service.Config;

#pragma warning disable CA1812 // Avoid uninstantiated internal classes - Instantiated by deserializing JSON
internal class AIServiceConfig
#pragma warning restore CA1812 // Avoid uninstantiated internal classes
{
    public const string OpenAI = "OPENAI";
    public const string AzureOpenAI = "AZUREOPENAI";

    public string Label { get; set; } = string.Empty;
    public string AIService { get; set; } = string.Empty;
    public string DeploymentOrModelId { get; set; } = string.Empty;
    public string Endpoint { get; set; } = string.Empty;
    public string Key { get; set; } = string.Empty;

    // TODO: add orgId and pass it all the way down

    public bool IsValid()
    {
        switch (this.AIService.ToUpperInvariant())
        {
            case OpenAI:
                return
                    !string.IsNullOrEmpty(this.Label) &&
                    !string.IsNullOrEmpty(this.DeploymentOrModelId) &&
                    !string.IsNullOrEmpty(this.Key);

            case AzureOpenAI:
                return
                    !string.IsNullOrEmpty(this.Endpoint) &&
                    !string.IsNullOrEmpty(this.Label) &&
                    !string.IsNullOrEmpty(this.DeploymentOrModelId) &&
                    !string.IsNullOrEmpty(this.Key);
            default:
                break;
        }

        return false;
    }
}
