// Copyright (c) Microsoft. All rights reserved.

using Microsoft.SemanticKernel.Diagnostics;

namespace Microsoft.SemanticKernel.Services;

public abstract class ServiceConfig : IServiceConfig
{
    /// <summary>
    /// An identifier used to map semantic functions to AI services,
    /// decoupling prompts configurations from the actual provider and model used.
    /// </summary>
    public string ServiceId { get; }

    /// <summary>
    /// Creates a new <see cref="ServiceConfig" /> with supplied values.
    /// </summary>
    /// <param name="serviceId">An identifier used to map semantic functions to AI services and models.</param>
    protected ServiceConfig(string serviceId)
    {
        Verify.NotNullOrWhiteSpace(serviceId);
        this.ServiceId = serviceId;
    }
}
