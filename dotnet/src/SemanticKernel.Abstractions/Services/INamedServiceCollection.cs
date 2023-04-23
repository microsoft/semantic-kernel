// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections;

namespace Microsoft.SemanticKernel.Services;

[System.Diagnostics.CodeAnalysis.SuppressMessage("Naming", "CA1711:Identifiers should not have incorrect suffix",
    Justification = "This is a collection, and is modeled after ServiceCollection")]
public interface INamedServiceCollection : INamedServiceProvider
{
    void AddSingleton<T>(T service);
    void AddSingleton<T>(string name, T service, bool isDefault = false);

    void AddTransient<T>(Func<T> factory);
    void AddTransient<T>(string name, Func<T> factory, bool isDefault = false);

    void AddTransient<T>(Func<INamedServiceProvider, T> factory);
    void AddTransient<T>(string name, Func<INamedServiceProvider, T> factory, bool isDefault = false);

    bool TrySetDefault<T>(string name);

    bool TryRemove<T>(string name);

    void Clear<T>();

    void Clear();

    //INamedServiceProvider Build();
}
