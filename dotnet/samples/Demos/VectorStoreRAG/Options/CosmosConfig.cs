// Copyright (c) Microsoft. All rights reserved.

using System.ComponentModel.DataAnnotations;

namespace VectorStoreRAG.Options;

/// <summary>
/// Azure DocumentDB and Azure Cosmos DB service settings.
/// </summary>
internal sealed class CosmosConfig
{
    public const string DocumentDBConfigSectionName = "AzureDocumentDB";
    public const string NoSqlConfigSectionName = "CosmosNoSql";

    [Required]
    public string ConnectionString { get; set; } = string.Empty;

    [Required]
    public string DatabaseName { get; set; } = string.Empty;
}
