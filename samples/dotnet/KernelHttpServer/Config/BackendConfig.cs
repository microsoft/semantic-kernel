// Copyright (c) Microsoft. All rights reserved.

namespace KernelHttpServer.Config;

public class BackendConfig
{
    public AIService AIService { get; set; }

    public string DeploymentOrModelId { get; set; } = string.Empty;

    public string Endpoint { get; set; } = string.Empty;

    public string Key { get; set; } = string.Empty;

    public string Label { get; set; } = string.Empty;

    public bool IsValid()
    {
        switch (this.AIService)
        {
            case AIService.OpenAI:
                return
                    !string.IsNullOrEmpty(this.Label) &&
                    !string.IsNullOrEmpty(this.DeploymentOrModelId) &&
                    !string.IsNullOrEmpty(this.Key);
            case AIService.AzureOpenAI:
                return
                    !string.IsNullOrEmpty(this.Endpoint) &&
                    !string.IsNullOrEmpty(this.Label) &&
                    !string.IsNullOrEmpty(this.DeploymentOrModelId) &&
                    !string.IsNullOrEmpty(this.Key);
        }

        return false;
    }
}
