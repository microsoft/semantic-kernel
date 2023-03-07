// Copyright (c) Microsoft. All rights reserved.

namespace SemanticKernelFunction.Config;

public class ApiKeyConfig
{
    public CompletionService CompletionBackend { get; set; }

    public string DeploymentOrModelId { get; set; } = string.Empty;

    public string Endpoint { get; set; } = string.Empty;

    public string Key { get; set; } = string.Empty;

    public string Label { get; set; } = string.Empty;

    public bool IsValid()
    {
        switch (this.CompletionBackend)
        {
            case CompletionService.OpenAI:
                return
                    !string.IsNullOrEmpty(this.Label) &&
                    !string.IsNullOrEmpty(this.DeploymentOrModelId) &&
                    !string.IsNullOrEmpty(this.Key);
            case CompletionService.AzureOpenAI:
                return
                    !string.IsNullOrEmpty(this.Endpoint) &&
                    !string.IsNullOrEmpty(this.Label) &&
                    !string.IsNullOrEmpty(this.DeploymentOrModelId) &&
                    !string.IsNullOrEmpty(this.Key);
        }

        return false;
    }
}
