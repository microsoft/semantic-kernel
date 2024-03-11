// Copyright (c) Microsoft. All rights reserved.

using YamlDotNet.Serialization;

namespace Microsoft.SemanticKernel.Prompty.Core;

internal sealed class PromptyModelConfig
{
    // azure open ai
    [YamlMember(Alias = "type")]
    public ModelType ModelType { get; set; }

    [YamlMember(Alias = "api_version")]
    public string ApiVersion { get; set; } = "2023-12-01-preview";

    [YamlMember(Alias = "azure_endpoint")]
    public string? AzureEndpoint { get; set; }

    [YamlMember(Alias = "azure_deployment")]
    public string? AzureDeployment { get; set; }

    [YamlMember(Alias = "api_key")]
    public string? ApiKey { get; set; }

    //open ai props
    [YamlMember(Alias = "name")]
    public string? Name { get; set; }

    [YamlMember(Alias = "organization")]
    public string? Organization { get; set; }
}
