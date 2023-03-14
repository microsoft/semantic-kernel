// Copyright (c) Microsoft. All rights reserved.

using Microsoft.SemanticKernel.Configuration;
using Microsoft.SemanticKernel.Diagnostics;

namespace Microsoft.SemanticKernel.AI.OpenAI.Services;

public abstract class BackendConfig : IBackendConfig
{
    /// <summary>
    /// An identifier used to map semantic functions to backend,
    /// decoupling prompts configurations from the actual model used.
    /// </summary>
    public string Label { get; }

    /// <summary>
    /// Creates a new <see cref="BackendConfig" /> with supplied values.
    /// </summary>
    /// <param name="label">An identifier used to map semantic functions to backend.</param>
    protected BackendConfig(string label)
    {
        Verify.NotEmpty(label, "The configuration label is empty");
        this.Label = label;
    }
}
