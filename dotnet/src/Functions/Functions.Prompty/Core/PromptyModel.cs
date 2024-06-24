// Copyright (c) Microsoft. All rights reserved.

using YamlDotNet.Serialization;

namespace Microsoft.SemanticKernel.Prompty.Core;

internal sealed class PromptyModel
{
    [YamlMember(Alias = "api")]
    public ApiType Api { get; set; } = ApiType.Chat;

    [YamlMember(Alias = "configuration")]
    public PromptyModelConfig? ModelConfiguration { get; set; }

    [YamlMember(Alias = "parameters")]
    public PromptyModelParameters? Parameters { get; set; }

    [YamlMember(Alias = "response")]
    public string? Response { get; set; }
}
