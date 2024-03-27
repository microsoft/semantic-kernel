// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;

namespace Microsoft.SemanticKernel.Connectors.MistralAI.Client;

/// <summary>
/// Represents the type of a MistralAI property.
/// </summary>
internal class MistralPropertyType
{
    /// <summary>
    /// Gets or sets the type of the property.
    /// </summary>
    public string Type { get; set; }

    /// <summary>
    /// Gets or sets the description of the property.
    /// </summary>
    public string? Description { get; set; }

    /// <summary>
    /// Gets or sets the list of possible values for the property.
    /// </summary>
    public IList<string>? Enum { get; set; }

    public MistralPropertyType(string type, string? description = null, IList<string>? @enum = null)
    {
        Verify.NotNull(type, nameof(type));

        this.Type = type;
        this.Description = description;
        this.Enum = @enum;
    }
}
