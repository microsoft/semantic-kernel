﻿// Copyright (c) Microsoft. All rights reserved.
namespace Microsoft.SemanticKernel.Process.Internal;

internal static class ProcessConstants
{
    /// <summary>
    /// Event raised internally for errors not handled at the step level.
    /// </summary>
    public const string GlobalErrorEventId = "Microsoft.SemanticKernel.Process.Global.OnError";

    /// <summary>
    /// Qualified name of the end step.
    /// </summary>
    public const string EndStepName = "Microsoft.SemanticKernel.Process.EndStep";

    /// <summary>
    /// Version for state of internal steps
    /// </summary>
    public const string InternalStepsVersion = "v0";

    /// <summary>
    /// Enum containing the name of internal components.
    /// Used for serialization purposes.
    /// </summary>
    public enum SupportedComponents
    {
        Step = 0,
        Process = 1,
    }
}
