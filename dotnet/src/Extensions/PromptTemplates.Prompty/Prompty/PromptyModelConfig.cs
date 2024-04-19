using System;
using Prompty.Core.Types;
using YamlDotNet.Serialization;

namespace Prompty.Core
{
    public class PromptyModelConfig
    {

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

    }
}