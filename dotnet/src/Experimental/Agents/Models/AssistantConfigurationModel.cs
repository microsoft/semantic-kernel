// Copyright (c) Microsoft. All rights reserved.
#pragma warning disable CA1812

using YamlDotNet.Serialization;

namespace Microsoft.SemanticKernel.Experimental.Agents.Models;

/// <summary>
/// Represents a yaml configuration file for an assistant.
/// </summary>
internal sealed class AssistantConfigurationModel
{
    /// <summary>
    /// The assistant name
    /// </summary>
    [YamlMember(Alias = "name")]
    public string Name { get; set; } = string.Empty;

    /// <summary>
    /// The assistant description
    /// </summary>
    [YamlMember(Alias = "description")]
    public string Description { get; set; } = string.Empty;

    /// <summary>
    /// The assistant instructions template
    /// </summary>
    [YamlMember(Alias = "instructions")]
    public string Instructions { get; set; } = string.Empty;
}
