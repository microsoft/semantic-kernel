// Copyright (c) Microsoft. All rights reserved.

namespace Microsoft.SemanticKernel;

/// <summary>
/// An enumeration representing the visibility of a <see cref="KernelProcessEvent"/>. This is used to determine
/// if the event is kept within the process it's emitted in, or exposed to external processes and systems.
/// </summary>
public enum KernelProcessEventVisibility
{
    /// <summary>
    /// The event is only visible to steps within the same process.
    /// </summary>
    Internal,

    /// <summary>
    /// The event is visible inside the process as well as outside the process. This is useful
    /// when the event is intended to be consumed by other processes or external systems.
    /// </summary>
    Public
}
