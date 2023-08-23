// Copyright (c) Microsoft. All rights reserved.
namespace Microsoft.SemanticKernel.Connectors.AI.SourceGraph.Client;

public class SourceGraphClientOptions
{
    public string AccessToken { get; }

    public string ServerEndpoint { get; }

    public Dictionary<string, string>? CustomHeaders { get; set; }


    public SourceGraphClientOptions(string accessToken, string endpoint, Dictionary<string, string>? customHeaders = null)
    {
        AccessToken = accessToken;
        ServerEndpoint = endpoint;
        CustomHeaders = customHeaders;
    }
}
