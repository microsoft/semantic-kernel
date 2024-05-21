// Copyright (c) Microsoft. All rights reserved.

namespace Microsoft.SemanticKernel;

public class AzureOpenAIApiKeyConfig : AzureOpenAIConfig
{
    /// <summary>
    /// API key  required by the service.
    /// </summary>
    public string ApiKey { get; set; } = string.Empty;

    /// <summary>
    /// Verify that the current state is valid.
    /// </summary>
    public override void Validate()
    {
        base.Validate();

        if (string.IsNullOrWhiteSpace(this.ApiKey))
        {
            throw new ConfigurationException($"Azure OpenAI: {nameof(this.ApiKey)} is empty");
        }
    }
}
