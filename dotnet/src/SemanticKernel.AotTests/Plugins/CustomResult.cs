// Copyright (c) Microsoft. All rights reserved.

namespace SemanticKernel.AotTests.Plugins;

internal sealed class CustomResult
{
    public string Value { get; set; }

    public CustomResult(string value)
    {
        this.Value = value;
    }
}
