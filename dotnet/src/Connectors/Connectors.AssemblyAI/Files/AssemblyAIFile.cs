// Copyright (c) Microsoft. All rights reserved.

using System;

namespace Microsoft.SemanticKernel.Connectors.AssemblyAI.Files;

/// <summary>
/// References an uploaded file by id.
/// </summary>
public sealed class AssemblyAIFile
{
    /// <summary>
    /// The file identifier.
    /// </summary>
    public Uri Url { get; set; } = null!;
}
