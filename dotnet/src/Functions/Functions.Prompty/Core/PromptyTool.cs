// Copyright (c) Microsoft. All rights reserved.

using YamlDotNet.Serialization;

namespace Microsoft.SemanticKernel.Prompty.Core;

internal sealed class PromptyTool
{
    [YamlMember(Alias = "id")]
    public string? id { get; set; }

    [YamlMember(Alias = "type")]
    public string? Type { get; set; }

    [YamlMember(Alias = "function")]
    public PromptyFunction? Function { get; set; }
}

internal sealed class PromptyFunction
{
    [YamlMember(Alias = "arguments")]
    public string? Arguments { get; set; }

    [YamlMember(Alias = "name")]
    public string? Name { get; set; }

    [YamlMember(Alias = "parameters")]
    public PromptyParameters? Parameters { get; set; }

    [YamlMember(Alias = "description")]
    public string? Description { get; set; }
}

internal sealed class PromptyParameters
{
    [YamlMember(Alias = "description")]
    public string? Description { get; set; }

    [YamlMember(Alias = "type")]
    public string? Type { get; set; }

    [YamlMember(Alias = "properties")]
    public object? Properties { get; set; }
}
