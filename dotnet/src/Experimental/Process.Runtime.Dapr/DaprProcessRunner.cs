// Copyright (c) Microsoft. All rights reserved.

using System.Threading.Tasks;

namespace Microsoft.SemanticKernel;

/// <summary>
/// A class that can run a process locally or in-process.
/// </summary>
public class DaprProcessRunner
{
    /// <summary>
    /// Runs the specified process.
    /// </summary>
    /// <typeparam name="TProcess"></typeparam>
    /// <returns></returns>
    public Task RunProcess<TProcess>(string id)
    {
        return Task.CompletedTask;
    }
}
