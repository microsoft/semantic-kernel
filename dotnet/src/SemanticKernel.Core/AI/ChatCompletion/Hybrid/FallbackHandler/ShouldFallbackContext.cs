// Copyright (c) Microsoft. All rights reserved.

using System;

namespace Microsoft.SemanticKernel.ChatCompletion;

public sealed class ShouldFallbackContext
{
    public Exception Exception { get; init; }
}
