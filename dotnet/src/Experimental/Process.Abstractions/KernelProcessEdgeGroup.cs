// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;

namespace Microsoft.SemanticKernel;

/// <summary>
/// Represents a group of edges in a kernel process.
/// </summary>
public sealed class KernelProcessEdgeGroup
{
    /// <summary>
    /// Initializes a new instance of the <see cref="KernelProcessEdgeGroup"/> class.
    /// </summary>
    /// <param name="groupId">The unique Id of the edge group.</param>
    /// <param name="messageSources">The message sources.</param>
    /// <param name="inputMapping">The input mapping.</param>
    public KernelProcessEdgeGroup(string groupId, List<KernelProcessMessageSource> messageSources, Func<Dictionary<string, object?>, IReadOnlyDictionary<string, object?>> inputMapping)
    {
        Verify.NotNullOrWhiteSpace(groupId, nameof(groupId));
        Verify.NotNullOrEmpty(messageSources, nameof(messageSources));
        Verify.NotNull(inputMapping, nameof(inputMapping));

        this.GroupId = groupId;
        this.MessageSources = messageSources;
        this.InputMapping = inputMapping;
    }

    /// <summary>
    /// Gets the unique identifier for this edge group.
    /// </summary>
    public string GroupId { get; }

    /// <summary>
    /// Gets the list of message sources that this edge group is listening to.
    /// </summary>
    public List<KernelProcessMessageSource> MessageSources { get; }

    /// <summary>
    /// Gets the input mapping function for this edge group.
    /// </summary>
    public Func<Dictionary<string, object?>, IReadOnlyDictionary<string, object?>> InputMapping { get; }
}
