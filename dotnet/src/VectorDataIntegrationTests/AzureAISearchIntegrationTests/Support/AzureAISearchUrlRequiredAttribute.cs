// Copyright (c) Microsoft. All rights reserved.

using VectorDataSpecificationTests.Xunit;

namespace AzureAISearchIntegrationTests.Support;

/// <summary>
/// Checks whether the sqlite_vec extension is properly installed, and skips the test(s) otherwise.
/// </summary>
[AttributeUsage(AttributeTargets.Method | AttributeTargets.Class | AttributeTargets.Assembly)]
public sealed class AzureAISearchUrlRequiredAttribute : Attribute, ITestCondition
{
    public ValueTask<bool> IsMetAsync() => new(AzureAISearchTestEnvironment.IsConnectionInfoDefined);

    public string Skip { get; set; } = "Service URL and API key are not configured, set AzureAISearch:ServiceUrl and AzureAISearch:ApiKey.";

    public string SkipReason
        => this.Skip;
}
