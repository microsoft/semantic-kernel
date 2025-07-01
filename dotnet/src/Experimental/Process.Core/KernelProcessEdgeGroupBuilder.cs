// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;

namespace Microsoft.SemanticKernel;
/// <summary>
/// Represents a group of edges in a kernel process.
/// </summary>
public sealed class KernelProcessEdgeGroupBuilder
{
    /// <summary>
    /// Initializes a new instance of the <see cref="KernelProcessEdgeGroup"/> class.
    /// </summary>
    /// <param name="groupId"></param>
    /// <param name="messageSources"></param>
    public KernelProcessEdgeGroupBuilder(string groupId, List<MessageSourceBuilder> messageSources)
    {
        Verify.NotNullOrEmpty(messageSources, nameof(messageSources));

        this.GroupId = groupId;
        this.MessageSources = messageSources;
    }

    /// <summary>
    /// Gets the unique identifier for this edge group.
    /// </summary>
    public string GroupId { get; }

    /// <summary>
    /// Gets the list of message sources that this edge group is listening to.
    /// </summary>
    public List<MessageSourceBuilder> MessageSources { get; }

    /// <summary>
    /// Gets the input mapping function for this edge group.
    /// </summary>
    public Func<Dictionary<string, object?>, Dictionary<string, object?>>? InputMapping { get; internal set; }
}
