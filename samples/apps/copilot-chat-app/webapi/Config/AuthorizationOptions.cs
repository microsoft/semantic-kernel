// Copyright (c) Microsoft. All rights reserved.

using Microsoft.Identity.Web;

namespace SemanticKernel.Service.Config;

public class AuthorizationOptions
{
    public const string PropertyName = "Authorization";

    public enum AuthorizationType
    {
        None,
        ApiKey,
        AzureAd
    }

    public AuthorizationType Type { get; set; }

    public string? ApiKey { get; set; }

    public AzureAdOptions? AzureAd { get; set; }

    public class AzureAdOptions
    {
        public string Instance { get; set; }
        public string TenantId { get; set; }
        public string ClientId { get; set; }
        public string Scopes { get; set; }
    }
}
