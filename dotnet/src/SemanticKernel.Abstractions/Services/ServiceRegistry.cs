// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Concurrent;

namespace Microsoft.SemanticKernel.Services;

public partial class ServiceRegistry
{
    // A constant key for the default service
    private const string DefaultKey = "__DEFAULT__";

    // A dictionary that maps a service type to a nested dictionary of names and service instances or factories
    //private readonly Dictionary<Type, Dictionary<string, object>> _services = new();
    private readonly ConcurrentDictionary<Type, ConcurrentDictionary<string, Func<INamedServiceProvider, object>>> _services = new();

    // A dictionary that maps a service type to the name of the default service
    private readonly ConcurrentDictionary<Type, string> _defaultIds = new();
}
