// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;

namespace Microsoft.SemanticKernel.Services;

/// <summary>
/// Extend this class to define the attributes for your AI service.
/// </summary>
public class AIServiceAttributes
{
    /// <summary>
    /// Model identifier key.
    /// </summary>
    public const string ModelIdKey = "ModelId";

    /// <summary>
    /// Endpoint key.
    /// </summary>
    public const string EndpointKey = "Endpoint";

    /// <summary>
    /// Api Version key.
    /// </summary>
    public const string ApiVersionKey = "ApiVersion";

    /// <summary>
    /// Initializes a new instance of the <see cref="AIServiceAttributes"/> class.
    /// </summary>
    protected Dictionary<string, object> InternalAttributes { get; } = new Dictionary<string, object>();

    /// <summary>
    /// Model identifier.
    /// This identifies the AI model these settings are configured for e.g., gpt-4, gpt-3.5-turbo
    /// </summary>
    public string? ModelId
    {
        get => this.InternalAttributes.TryGetValue(ModelIdKey, out var value) ? value as string : null;
        init => this.InternalAttributes[ModelIdKey] = value ?? string.Empty;
    }

    /// <summary>
    /// Endpoint.
    /// </summary>
    public string? Endpoint
    {
        get => this.InternalAttributes.TryGetValue(EndpointKey, out var value) ? value as string : null;
        init => this.InternalAttributes[EndpointKey] = value ?? string.Empty;
    }

    /// <summary>
    /// API Version.
    /// </summary>
    public string? ApiVersion
    {
        get => this.InternalAttributes.TryGetValue(ApiVersionKey, out var value) ? value as string : null;
        init => this.InternalAttributes[ApiVersionKey] = value ?? string.Empty;
    }

    /// <summary>
    /// Gets the AI service attributes.
    /// </summary>
    public IReadOnlyDictionary<string, object> Attributes => this.InternalAttributes;
}
