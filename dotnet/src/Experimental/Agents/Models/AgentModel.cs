// Copyright (c) Microsoft. All rights reserved.

using YamlDotNet.Serialization;

namespace Microsoft.SemanticKernel.Experimental.Agents.Models;

internal class AgentModel
{
    [YamlMember(Alias = "name")]
    public string? Name { get; set; }

    [YamlMember(Alias = "description")]
    public string? Description { get; set; }

    [YamlMember(Alias = "instructions")]
    public string Instructions { get; set; } = string.Empty;

    [YamlMember(Alias = "planner")]
    public string? Planner { get; set; }

    [YamlMember(Alias = "model")]
    public string? Model { get; set; }
}
