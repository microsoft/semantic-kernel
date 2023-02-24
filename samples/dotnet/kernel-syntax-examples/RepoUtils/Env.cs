// Copyright (c) Microsoft. All rights reserved.

using System;

namespace RepoUtils;

internal static class Env
{
    /// <summary>
    /// Simple helper used to load env vars like credentials, to avoid hard coding them in the sample code
    /// </summary>
    /// <param name="name">Env var name</param>
    /// <returns>Env var value</returns>
    internal static string Var(string name)
    {
        var value = Environment.GetEnvironmentVariable(name);
        if (string.IsNullOrEmpty(value))
        {
            throw new YourAppException($"Env var not set: {name}");
        }

        return value;
    }
}
