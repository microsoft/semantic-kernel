// Copyright (c) Microsoft. All rights reserved.

using YamlDotNet.Serialization;

namespace Microsoft.SemanticKernel.Experimental.Prompty.Core;

internal class PromptyModelConfig
{
    // azure open ai
    [YamlMember(Alias = "type")]
    public ModelType? ModelType;

    [YamlMember(Alias = "api_version")]
    public string ApiVersion = "2023-12-01-preview";

    [YamlMember(Alias = "azure_endpoint")]
    public string AzureEndpoint { get; set; }

    [YamlMember(Alias = "azure_deployment")]
    public string AzureDeployment { get; set; }

    [YamlMember(Alias = "api_key")]
    public string ApiKey { get; set; }

    //open ai props
    [YamlMember(Alias = "name")]
    public string Name { get; set; }
    [YamlMember(Alias = "organization")]
    public string Organization { get; set; }
}
