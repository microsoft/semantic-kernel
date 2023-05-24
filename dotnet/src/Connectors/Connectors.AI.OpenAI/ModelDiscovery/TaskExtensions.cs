// Copyright (c) Microsoft. All rights reserved.

using System.Threading.Tasks;

namespace Microsoft.SemanticKernel.Connectors.AI.OpenAI.ModelDiscovery;

internal static class TaskExtensions
{
    public static void RunTaskSynchronously(this Task t)
    {
        var task = Task.Run(async () => await t.ConfigureAwait(false));
        task.Wait();
    }

    public static T RunTaskSynchronously<T>(this Task<T> t)
    {
        var task = Task.Run(async () => await t.ConfigureAwait(false));
        task.Wait();
        return task.Result!;
    }
}
