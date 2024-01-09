// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;

namespace Microsoft.SemanticKernel;

/// <summary>
/// Represents video content.
/// </summary>
public sealed class VideoContent : KernelContent
{
    /// <summary>
    /// The URI of video.
    /// </summary>
    public Uri? Uri { get; set; }

    /// <summary>
    /// Video model context start time offset from the start of the video.
    /// </summary>
    public TimeSpan? StartTimeOffset { get; set; }

    /// <summary>
    /// Video model context end time offset from the start of the video.
    /// </summary>
    public TimeSpan? EndTimeOffset { get; set; }

    /// <summary>
    /// Initializes a new instance of the <see cref="VideoContent"/> class.
    /// </summary>
    /// <param name="uri">The URI of video.</param>
    /// <param name="startTimeOffset">The start time offset from the start of the video.</param>
    /// <param name="endTimeOffset">The end time offset from the start of the video.</param>
    /// <param name="modelId">The model ID used to generate the content.</param>
    /// <param name="innerContent">Inner content.</param>
    /// <param name="metadata">Additional metadata.</param>
    public VideoContent(
        Uri uri,
        TimeSpan? startTimeOffset = null,
        TimeSpan? endTimeOffset = null,
        string? modelId = null,
        object? innerContent = null,
        IReadOnlyDictionary<string, object?>? metadata = null)
        : base(innerContent, modelId, metadata)
    {
        this.Uri = uri;
        this.StartTimeOffset = startTimeOffset;
        this.EndTimeOffset = endTimeOffset;
    }

    /// <inheritdoc/>
    public override string ToString()
    {
        return this.Uri?.ToString() ?? string.Empty;
    }
}
