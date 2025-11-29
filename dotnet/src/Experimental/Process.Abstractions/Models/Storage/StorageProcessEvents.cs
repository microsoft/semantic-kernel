// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;
using System.Text.Json.Serialization;

namespace Microsoft.SemanticKernel.Process.Models.Storage;

/// <summary>
/// Storage representation of a process state.
/// </summary>
public record StorageProcessEvents
{
    /// <summary>
    /// Gets or sets the list of external pending messages associated with the process.
    /// </summary>
    [JsonPropertyName("externalPendingMessages")]
    public List<KernelProcessEvent> ExternalPendingMessages { get; set; } = [];

    /* TODO: 
     * Hypothetically step edgeGroup pending messages logic could be moved to the process and save it here 
     * All "pending messages" that cannot be processed by a step yet (waiting on some condition)
     * could be moved to the process layer instead.
     */
    //[JsonPropertyName("internalPendingMessages")]
    //public List<KernelProcessEvent> InternalProcessEvents { get; set; } = [];
}
