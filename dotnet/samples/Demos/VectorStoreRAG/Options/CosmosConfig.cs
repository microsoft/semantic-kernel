// Copyright (c) Microsoft. All rights reserved.

using System.ComponentModel.DataAnnotations;

namespace VectorStoreRAG.Options;

/// <summary>
/// Azure CosmosDB service settings for use with CosmosMongo and CosmosNoSql.
/// </summary>
internal sealed class CosmosConfig
{
    public const string MongoConfigSectionName = "CosmosMongoDB";
    public const string NoSqlConfigSectionName = "CosmosNoSql";

    [Required]
    public string ConnectionString { get; set; } = string.Empty;

    [Required]
    public string DatabaseName { get; set; } = string.Empty;
}
