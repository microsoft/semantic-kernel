// Copyright (c) Microsoft. All rights reserved.

using Microsoft.SemanticKernel.Diagnostics;

namespace Microsoft.SemanticKernel.Services;

/// <summary>
/// Represents a base class for service configurations.
/// </summary>
public abstract class ServiceConfig : IServiceConfig
{
    /// <summary>
    /// Gets the identifier used to map semantic functions to AI services,
    /// decoupling prompts configurations from the actual provider and model used.
    /// </summary>
    public string ServiceId { get; }

    /// <summary>
    /// Initializes a new instance of the <see cref="ServiceConfig" /> class with the supplied values.
    /// </summary>
    /// <param name="serviceId">An identifier used to map semantic functions to AI services and models.</param>
    protected ServiceConfig(string serviceId)
    {
        Verify.NotNullOrWhiteSpace(serviceId);
        this.ServiceId = serviceId;
    }
}
