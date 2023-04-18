// Copyright (c) Microsoft. All rights reserved.

using System;

namespace Microsoft.SemanticKernel.Skills.OpenAPI.Authentication;
public class AzureAuthenticationProvider : MSALAuthenticationProvider
{
    private const string AzureCliClientId = "04b07795-8ddb-461a-bbee-02f9e1bf7b46";

    public AzureAuthenticationProvider(string tenantId, string[] scopes, Uri redirectUri)
        : base(AzureCliClientId, tenantId, scopes, redirectUri)
    {
        // service name? so we can prefix the scopes?
    }
}
