// Copyright (c) Microsoft. All rights reserved.

namespace Microsoft.SemanticKernel.Connectors.AzureCosmosDBNoSQL;

internal static class AzureCosmosDBNoSQLConstants
{
    /// <summary>Reserved key property name in Azure CosmosDB NoSQL.</summary>
    internal const string ReservedKeyPropertyName = "id";

    /// <summary>Variable name for table in Azure CosmosDB NoSQL queries.</summary>
    internal const string TableQueryVariableName = "x";
}
