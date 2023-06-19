// Copyright (c) Microsoft. All rights reserved.

namespace Microsoft.SemanticKernel.Connectors.AI.OpenAI.ImageGeneration;

/// <summary>
/// Azure image generation response status
/// <see herf="https://learn.microsoft.com/en-us/azure/cognitive-services/openai/reference#image-generation" />
/// </summary>
public static class AzureImageOperationStatus
{
    /// <summary>
    /// Image generation Succeeded
    /// </summary>
    public const string Succeeded = "succeeded";

    /// <summary>
    /// Image generation Failed
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
