// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;

namespace Microsoft.SemanticKernel.Connectors.MistralAI.Client;

internal class MistralPropertyType
{
    public string Type { get; set; }

    public string? Description { get; set; }

    public IList<string>? Enum { get; set; }

    public MistralPropertyType(string type, string? description = null, IList<string>? @enum = null)
    {
        Verify.NotNull(type, nameof(type));

        this.Type = type;
        this.Description = description;
        this.Enum = @enum;
    }
}
