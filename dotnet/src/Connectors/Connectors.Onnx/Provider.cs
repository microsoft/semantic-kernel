// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;

namespace Microsoft.SemanticKernel.Connectors.Onnx;

/// <summary>ONNX provider</summary>
public class Provider
{
    /// <summary>
    /// Id
    /// </summary>
    public string Id { get; set; } = "";

    /// <summary>
    /// Options
    /// </summary>
    public Dictionary<string, string> Options { get; set; } = new();
}
