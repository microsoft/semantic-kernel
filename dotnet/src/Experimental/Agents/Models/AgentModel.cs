// Copyright (c) Microsoft. All rights reserved.

namespace Microsoft.SemanticKernel.Experimental.Agents.Models;

internal class AgentModel
{
    public string? Name { get; set; }

    public string? Description { get; set; }

    public string Model { get; set; } = string.Empty;

    public string Instructions { get; set; } = string.Empty;
}
