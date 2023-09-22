// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;

namespace Microsoft.SemanticKernel.Services;
/// <summary>
/// Provides AI services by managing a collection of named service instances.
/// </summary>
public class AIServiceProvider : NamedServiceProvider<IAIService>, IAIServiceProvider
{
    /// <summary>
    /// Initializes a new instance of the <see cref="AIServiceProvider"/> class.
    /// </summary>
    /// <param name="services">A dictionary of service types and their corresponding named instances.</param>
    /// <param name="defaultIds">A dictionary of service types and their default instance names.</param>
    public AIServiceProvider(Dictionary<Type, Dictionary<string, Func<object>>> services, Dictionary<Type, string> defaultIds)
        : base(services, defaultIds)
    {
    }
}
