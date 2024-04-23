// Copyright (c) Microsoft. All rights reserved.

using YamlDotNet.Serialization;

namespace Microsoft.SemanticKernel.Experimental.Prompty.Core;

internal class Tool
{
    [YamlMember(Alias = "id")]
    public string? id { get; set; }
    [YamlMember(Alias = "type")]
    public string? Type { get; set; }
    [YamlMember(Alias = "function")]
    public Function? Function { get; set; }
}

internal class Function
{
    [YamlMember(Alias = "arguments")]
    public string? Arguments { get; set; }
    [YamlMember(Alias = "name")]
    public string? Name { get; set; }
    [YamlMember(Alias = "parameters")]
    public Parameters? Parameters { get; set; }
    [YamlMember(Alias = "description")]
    public string? Description { get; set; }
}
internal class Parameters
{
    [YamlMember(Alias = "description")]
    public string? Description { get; set; }
    [YamlMember(Alias = "type")]
    public string? Type { get; set; }
    [YamlMember(Alias = "properties")]
    public object? Properties { get; set; }
    [YamlMember(Alias = "prompt")]
    public string? Prompt { get; set; }
}