// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Threading.Tasks;
using SemanticKernel.IntegrationTests.Connectors.Memory.Xunit;

namespace SemanticKernel.IntegrationTests.Connectors.Memory.AzureAISearch;

/// <summary>
/// Attribute to use to skip tests if the settings for Azure AI Search is not set.
/// </summary>
[AttributeUsage(AttributeTargets.Method | AttributeTargets.Class)]
public sealed class AzureAISearchConfigConditionAttribute : Attribute, ITestCondition
{
    public ValueTask<bool> IsMetAsync()
    {
        var config = AzureAISearchVectorStoreFixture.GetAzureAISearchConfiguration();
        var isMet = config is not null && !string.IsNullOrWhiteSpace(config?.ServiceUrl) && !string.IsNullOrWhiteSpace(config?.ApiKey);

        return ValueTask.FromResult(isMet);
    }

    public string SkipReason
        => "Azure AI Search ServiceUrl or ApiKey was not specified in user secrets. Use the following command to set them: dotnet user-secrets set \"AzureAISearch:ServiceUrl\" \"your_service_url\" and dotnet user-secrets set \"AzureAISearch:ApiKey\" \"your_api_key\"";
}
