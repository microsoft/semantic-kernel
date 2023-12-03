// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;

namespace Microsoft.SemanticKernel.Experimental.Agents.Extensions;

internal static class KernelArgumentsExtensions
{
    internal static Dictionary<string, object?> ToDictionary(this KernelArguments args)
    {
        var dictionary = new Dictionary<string, object?>();
        foreach (var arg in args)
        {
            dictionary.Add(arg.Key, arg.Value);
        }

        return dictionary;
    }
}
