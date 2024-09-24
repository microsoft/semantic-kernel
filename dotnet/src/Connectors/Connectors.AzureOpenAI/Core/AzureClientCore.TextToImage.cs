// Copyright (c) Microsoft. All rights reserved.

using Microsoft.SemanticKernel.Connectors.OpenAI;

namespace Microsoft.SemanticKernel.Connectors.AzureOpenAI;

internal partial class AzureClientCore : ClientCore
{
    protected override string GetModelId(string? settingsModelId)
    {
        return settingsModelId ?? this.DeploymentName;
    }
}
