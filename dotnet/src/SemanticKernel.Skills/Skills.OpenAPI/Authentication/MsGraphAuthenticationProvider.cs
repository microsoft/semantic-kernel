// Copyright (c) Microsoft. All rights reserved.

using System;

namespace Microsoft.SemanticKernel.Skills.OpenAPI.Authentication;
public class MsGraphAuthenticationProvider : MsalAuthenticationProvider
{
    private const string MsGraphUri = "https://graph.microsoft.com/";
    public MsGraphAuthenticationProvider(string clientId, string tenantId, string[] scopes, Uri redirectUri)
        : base(clientId, tenantId, scopes, new Uri(MsGraphUri), redirectUri)
    {
    }
}
