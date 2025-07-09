// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;
using System.Text.Json;
using System.Text.Json.Serialization;

namespace Microsoft.SemanticKernel.Process.Serialization;

// Internal Process Framework objects used in Process Framework should be added to the serialization context 
[JsonSerializable(typeof(KernelProcessStepContext))]
[JsonSerializable(typeof(KernelProcessStepExternalContext))]
[JsonSerializable(typeof(KernelProcessProxyMessage))]
internal partial class KernelProcessAbstractionsJsonContext : JsonSerializerContext
{
}

/// <summary>
/// Extensions for Semantic Kernel process abstractions JSON serialization.
/// </summary>
public static class KernelProcessJsonSerializationExtensions
{
    /// <summary>
    /// Method that allows adding additional serialization contexts to the default options used within Semantic Kernel for process abstractions.
    /// </summary>
    /// <param name="additionalContexts">List of additional serializations contexts to be added</param>
    /// <returns></returns>
    public static JsonSerializerOptions GetKernelProcessCustomJsonSerializationOptions(JsonSerializerContext[] additionalContexts)
    {
        List<JsonSerializerContext> predefinedContexts = new() { KernelProcessAbstractionsJsonContext.Default };
        if (additionalContexts != null)
        {
            predefinedContexts.AddRange(additionalContexts);
        }

        var jsonOptions = KernelJsonSerializationOptions.GetKernelCustomJsonSerializationOptions(predefinedContexts.ToArray());

        return jsonOptions;
    }
}
