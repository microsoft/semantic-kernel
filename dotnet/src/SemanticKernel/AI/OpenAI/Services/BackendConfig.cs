// Copyright (c) Microsoft. All rights reserved.

using Microsoft.SemanticKernel.Configuration;
using Microsoft.SemanticKernel.Diagnostics;

namespace Microsoft.SemanticKernel.AI.OpenAI.Services;
public abstract class BackendConfig : IBackendConfig
{
    public string Label { get; }

    protected BackendConfig(string label)
    {
        Verify.NotEmpty(label, "The configuration label is empty");
        this.Label = label;
    }
}
