// Copyright (c) Microsoft. All rights reserved.

namespace Microsoft.SemanticKernel;

/// <summary>
/// Represents the type of a thread in a kernel process.
/// </summary>
public enum KernelProcessThreadType
{
    /// <summary>
    /// A thread is a general chat completion type.
    /// </summary>
    ChatCompletion,

    /// <summary>
    /// A thread is an AzureAI or Foundry type.
    /// </summary>
    AzureAI
}
