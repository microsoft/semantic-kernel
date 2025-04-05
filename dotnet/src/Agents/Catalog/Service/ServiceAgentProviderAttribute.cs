// Copyright (c) Microsoft. All rights reserved.

using System;

namespace Microsoft.SemanticKernel.Agents.Service;

/// <summary>
/// Describes the <see cref="ServiceAgentProvider"/> associated with an <see cref="ServiceAgent"/>.
/// </summary>
[AttributeUsage(AttributeTargets.Class, Inherited = false, AllowMultiple = false)]
public sealed class ServiceAgentProviderAttribute<TProvider> : Attribute
    where TProvider : ServiceAgentProvider
{
    /// <summary>
    /// Initializes a new instance of the <see cref="ServiceAgentProviderAttribute{TProvider}"/> class.
    /// </summary>
    public ServiceAgentProviderAttribute()
    {
        this.ServiceProviderType = typeof(TProvider);
    }
    /// <summary>
    /// Gets the type of the service provider.
    /// </summary>
    public Type ServiceProviderType { get; }
}
