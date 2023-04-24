// Copyright (c) Microsoft. All rights reserved.

namespace SemanticKernel.Service.Config;

/// <summary>
/// Configuration settings for the bot file schema that is supported by this application.
/// </summary>
public class BotSchemaConfig
{
    /// <summary>
    /// The name of the schema.
    /// </summary>
    public string Name { get; set; } = string.Empty;

    /// <summary>
    /// The version of the schema.
    /// </summary>
    public int Version { get; set; } = -1;
}
