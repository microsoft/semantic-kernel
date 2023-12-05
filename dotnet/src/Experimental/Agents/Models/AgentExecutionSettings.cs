// Copyright (c) Microsoft. All rights reserved.

using YamlDotNet.Serialization;

namespace Microsoft.SemanticKernel.Experimental.Agents.Models;

internal class AgentExecutionSettings
{
    [YamlMember(Alias = "planner")]
    public string? Planner { get; set; }

    [YamlMember(Alias = "model")]
    public string? Model { get; set; }

    [YamlMember(Alias = "deployment_name")]
    public string? DeploymentName { get; set; }
}
