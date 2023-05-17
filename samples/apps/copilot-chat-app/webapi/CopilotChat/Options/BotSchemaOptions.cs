// Copyright (c) Microsoft. All rights reserved.

using System.ComponentModel.DataAnnotations;
using SemanticKernel.Service.Options;

namespace SemanticKernel.Service.CopilotChat.Options;

/// <summary>
/// Configuration options for the bot file schema that is supported by this application.
/// </summary>
public class BotSchemaOptions
{
    public const string PropertyName = "BotSchema";

    /// <summary>
    /// The name of the schema.
    /// </summary>
    [Required, NotEmptyOrWhitespace]
    public string Name { get; set; } = string.Empty;

    /// <summary>
    /// The version of the schema.
    /// </summary>
    [Range(0, int.MaxValue)]
    public int Version { get; set; }
}
