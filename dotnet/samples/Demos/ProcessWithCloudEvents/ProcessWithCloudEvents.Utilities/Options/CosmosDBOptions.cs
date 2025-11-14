// Copyright (c) Microsoft. All rights reserved.

using System.ComponentModel.DataAnnotations;

namespace ProcessWithCloudEvents.SharedComponents.Options;

/// <summary>
/// Configuration for Cosmos DB.
/// </summary>
public class CosmosDBOptions
{
    public const string SectionName = "CosmosDB";

    [Required]
    public string ConnectionString { get; set; } = string.Empty;

    [Required]
    public string DatabaseName { get; set; } = string.Empty;

    [Required]
    public string ContainerName { get; set; } = string.Empty;
}
