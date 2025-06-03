// Copyright (c) Microsoft. All rights reserved.

namespace Microsoft.SemanticKernel;

/// <summary>
/// Defines the policy for how threads are managed in the process.
/// </summary>
public enum KernelProcessThreadLifetime
{
    /// <summary>
    /// The thread is created when the process is created. The thread id is saved in the process state and will be reused within the scope of a process instance. Scoped threads can be shared between steps.
    /// </summary>
    Scoped,

    /// <summary>
    /// A new thread is created every time a step in the process uses it. The thread id is not saved in the process state. Transient threads cannot be shared between steps.
    /// </summary>
    Transient
}
