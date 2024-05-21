// Copyright (c) Microsoft. All rights reserved.

using Azure.Core;

namespace Microsoft.SemanticKernel;

public class AzureOpenAITokenConfig : AzureOpenAIConfig
{
    /// <summary>
    /// Token credential required by the service.
    /// </summary>
    public TokenCredential? TokenCredential { get; set; }

    /// <summary>
    /// Verify that the current state is valid.
    /// </summary>
    public override void Validate()
    {
        base.Validate();

        if (this.TokenCredential is null)
        {
            throw new ConfigurationException($"Azure OpenAI: {nameof(this.TokenCredential)} is null");
        }
    }
}
