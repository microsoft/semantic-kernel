// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;
using System.Text.Json;
using System.Text.Json.Serialization;
using System.Text.Json.Serialization.Metadata;

namespace Microsoft.SemanticKernel;

public static class KernelJsonSerializationOptions
{
    /// <summary>
    /// Method that allows adding additional serialization contexts to the default options using within Semantic Kernel.
    /// </summary>
    /// <param name="additionalContexts">List of additional serializations contexts to be added</param>
    /// <returns></returns>
    public static JsonSerializerOptions GetKernelCustomJsonSerializationOptions(JsonSerializerContext[] additionalContexts)
    {
        // Default options are compatible with internal SK components
        var jsonOptions = new JsonSerializerOptions(AbstractionsJsonContext.Default.Options);
        if (additionalContexts != null)
        {
            List<JsonSerializerContext> predefinedContexts = new() { AbstractionsJsonContext.Default };
            predefinedContexts.AddRange(additionalContexts);

            jsonOptions.TypeInfoResolver = JsonTypeInfoResolver.Combine(predefinedContexts.ToArray());
        }

        return jsonOptions;
    }
}
