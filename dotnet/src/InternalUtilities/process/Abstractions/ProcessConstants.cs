// Copyright (c) Microsoft. All rights reserved.
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
}
