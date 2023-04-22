// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Diagnostics.CodeAnalysis;
using System.Linq;

namespace Microsoft.SemanticKernel.Skills.MsGraph.Connectors.Client;

/// <summary>
/// Graph API connector configuration model.
/// </summary>
public class MsGraphConfiguration
{
    /// <summary>
    /// Gets or sets the client ID.
    /// </summary>
    public string ClientId { get; }

    /// <summary>
    /// Gets or sets the tenant/directory ID.
    /// </summary>
    public string TenantId { get; }

    /// <summary>
    /// Gets or sets the API permission scopes.
    /// </summary>
    /// <remarks>
    /// Keeping this parameters nullable and out of the constructor is a workaround for
    /// nested types not working with IConfigurationSection.Get.
    /// See https://github.com/dotnet/runtime/issues/77677
    /// </remarks>
    public IEnumerable<string> Scopes { get; set; } = Enumerable.Empty<string>();

    /// <summary>
    /// Gets or sets the redirect URI to use.
    /// </summary>
    public Uri RedirectUri { get; }

    /// <summary>
    /// Initializes a new instance of the <see cref="MsGraphConfiguration"/> class.
    /// </summary>
    /// <param name="clientId">The client id.</param>
    /// <param name="tenantId">The tenant id.</param>
    /// <param name="redirectUri">The redirect URI.</param>
    public MsGraphConfiguration(
        [NotNull] string clientId,
        [NotNull] string tenantId,
        [NotNull] Uri redirectUri)
    {
        this.ClientId = clientId;
        this.TenantId = tenantId;
        this.RedirectUri = redirectUri;
    }
}
