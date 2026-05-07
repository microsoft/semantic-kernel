// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;

namespace Microsoft.SemanticKernel.Connectors.Onnx;

/// <summary>ONNX provider</summary>
public class Provider
{
    /// <summary>
    /// Initializes a new instance of the Provider class with the specified identifier.
    /// </summary>
    /// <param name="id">The unique identifier for the provider. Cannot be null or empty.</param>
    public Provider(string id)
    {
        Verify.NotNullOrWhiteSpace(id);
        this.Id = id;
    }

    /// <summary>
    /// The unique identifier for the provider.
    /// </summary>
    /// <remarks>
    /// Refers to <see href="https://onnxruntime.ai/docs/genai/reference/config#provideroptions"/> for available options.
    /// </remarks>
    public string Id { get; }

    /// <summary>
    /// Options
    /// </summary>
    public Dictionary<string, string> Options { get; set; } = [];
}
