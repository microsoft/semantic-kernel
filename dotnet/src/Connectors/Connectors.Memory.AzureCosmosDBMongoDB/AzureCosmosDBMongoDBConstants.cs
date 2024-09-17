// Copyright (c) Microsoft. All rights reserved.

namespace Microsoft.SemanticKernel.Connectors.AzureCosmosDBMongoDB;

/// <summary>
/// Constants for Azure CosmosDB MongoDB vector store implementation.
/// </summary>
internal static class AzureCosmosDBMongoDBConstants
{
    /// <summary>Reserved key property name in Azure CosmosDB MongoDB.</summary>
    internal const string MongoReservedKeyPropertyName = "_id";

    /// <summary>Reserved key property name in data model.</summary>
    internal const string DataModelReservedKeyPropertyName = "Id";
}
