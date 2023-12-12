// Copyright (c) Microsoft. All rights reserved.

using System.Diagnostics.CodeAnalysis;

namespace Microsoft.SemanticKernel.Connectors.OpenAI;

/// <summary>
/// Azure OpenAI text to image response status
/// <see herf="https://learn.microsoft.com/en-us/azure/cognitive-services/openai/reference#image-generation" />
/// </summary>
[Experimental("SKEXP0012")]
internal static class AzureOpenAIImageOperationStatus
{
    /// <summary>
    /// Text to image Succeeded
    /// </summary>
    public const string Succeeded = "succeeded";

    /// <summary>
    /// Text to image Failed
    /// </summary>
    public const string Failed = "failed";

    /// <summary>
    /// Task is running
    /// </summary>
    public const string Running = "running";

    /// <summary>
    /// Task is queued but hasn't started yet
    /// </summary>
    public const string NotRunning = "notRunning";

    /// <summary>
    /// The image has been removed from Azure's server.
    /// </summary>
    public const string Deleted = "deleted";

    /// <summary>
    /// Task has timed out
    /// </summary>
    public const string Cancelled = "cancelled";
}
