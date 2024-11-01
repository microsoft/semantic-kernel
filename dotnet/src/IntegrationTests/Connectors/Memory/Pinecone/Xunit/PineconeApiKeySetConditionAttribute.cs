// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Threading.Tasks;

namespace SemanticKernel.IntegrationTests.Connectors.Memory.Pinecone.Xunit;

[AttributeUsage(AttributeTargets.Method | AttributeTargets.Class)]
public sealed class PineconeApiKeySetConditionAttribute : Attribute, ITestCondition
{
    public ValueTask<bool> IsMetAsync()
    {
        var isMet = PineconeUserSecretsExtensions.ContainsPineconeApiKey();

        return ValueTask.FromResult(isMet);
    }

    public string SkipReason
        => $"Pinecone API key was not specified in user secrets. Use the following command to set it: dotnet user-secrets set \"{PineconeUserSecretsExtensions.PineconeApiKeyUserSecretEntry}\" \"your_Pinecone_API_key\"";
}
