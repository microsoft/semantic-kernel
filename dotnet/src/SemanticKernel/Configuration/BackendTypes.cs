// Copyright (c) Microsoft. All rights reserved.

namespace Microsoft.SemanticKernel.Configuration;

/// <summary>
/// Backend types.
/// </summary>
public enum BackendTypes
{
    /// <summary>
    /// Unknown.
    /// </summary>
    Unknown = -1,

    /// <summary>
    /// Azure OpenAI.
    /// </summary>
    AzureOpenAI = 0,

    /// <summary>
    /// OpenAI.
    /// </summary>
    OpenAI = 1,
}
