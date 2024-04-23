// Copyright (c) Microsoft. All rights reserved.

using YamlDotNet.Serialization;

namespace Microsoft.SemanticKernel.Experimental.Prompty.Core;
internal class PromptyModel
{
    [YamlMember(Alias = "api")]
    public ApiType Api { get; set; }
    [YamlMember(Alias = "configuration")]
    public PromptyModelConfig? ModelConfiguration;
    [YamlMember(Alias = "parameters")]
    public PromptyModelParameters? Parameters;
    [YamlMember(Alias = "response")]
    public string? Response { get; set; }
}