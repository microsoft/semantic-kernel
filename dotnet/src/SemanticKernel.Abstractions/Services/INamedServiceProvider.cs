// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;
using System.Diagnostics.CodeAnalysis;

namespace Microsoft.SemanticKernel.Services;

public interface INamedServiceProvider
{
    T? GetService<T>(string? name = null);
    bool TryGetService<T>([NotNullWhen(true)] out T? service);
    bool TryGetService<T>(string name, [NotNullWhen(true)] out T? service);
    T GetRequiredService<T>(string? name = null);
    IEnumerable<string> GetServiceNames<T>();
}
