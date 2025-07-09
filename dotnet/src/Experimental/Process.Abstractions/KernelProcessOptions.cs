// Copyright (c) Microsoft. All rights reserved.

using System.Text.Json.Serialization;

namespace Microsoft.SemanticKernel;

/// <summary>
/// Options for configuring the Kernel process
/// </summary>
public record KernelProcessOptions
{
    public JsonSerializerContext[] JsonSerializerAdditionalContexts { get; init; } = [];
}
