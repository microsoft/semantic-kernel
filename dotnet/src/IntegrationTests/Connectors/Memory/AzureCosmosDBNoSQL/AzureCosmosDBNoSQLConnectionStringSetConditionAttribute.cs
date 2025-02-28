// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Threading.Tasks;
using SemanticKernel.IntegrationTests.Connectors.Memory.Xunit;

namespace SemanticKernel.IntegrationTests.Connectors.Memory.AzureCosmosDBNoSQL;

/// <summary>
/// Attribute to use to skip tests if the connection string for CosmosDB NoSQL is not set.
/// </summary>
[AttributeUsage(AttributeTargets.Method | AttributeTargets.Class)]
public sealed class AzureCosmosDBNoSQLConnectionStringSetConditionAttribute : Attribute, ITestCondition
{
    public ValueTask<bool> IsMetAsync()
    {
        var isMet = AzureCosmosDBNoSQLVectorStoreFixture.GetConnectionString() is not null;

        return ValueTask.FromResult(isMet);
    }

    public string SkipReason
        => $"CosmosDB NoSQL connection string was not specified in user secrets. Use the following command to set it: dotnet user-secrets set \"{AzureCosmosDBNoSQLVectorStoreFixture.ConnectionStringKey}\" \"your_connection_string\"";
}
