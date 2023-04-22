// Copyright (c) Microsoft. All rights reserved.

namespace SemanticKernel.Service.Config;

/// <summary>
/// Configuration settings for connecting to Azure CosmosDB.
/// </summary>
public class CosmosConfig
{
    /// <summary>
    /// Gets or sets the Cosmos database name.
    /// </summary>
    public string Database { get; set; } = string.Empty;

    /// <summary>
    /// Gets or sets the Cosmos connection string.
    /// </summary>
    public string ConnectionString { get; set; } = string.Empty;

    /// <summary>
    /// Gets or sets the Cosmos container for chat sessions.
    /// </summary>
    public string ChatSessionsContainer { get; set; } = string.Empty;

    /// <summary>
    /// Gets or sets the Cosmos container for chat messages.
    /// </summary>
    public string ChatMessagesContainer { get; set; } = string.Empty;
}
