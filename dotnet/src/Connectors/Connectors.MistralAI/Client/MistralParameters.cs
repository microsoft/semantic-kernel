// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;

namespace Microsoft.SemanticKernel.Connectors.MistralAI.Client;

/// <summary>
/// Represents the parameters of a MistralAI function.
/// </summary>
internal class MistralParameters
{
    /// <summary>
    /// Gets or sets the type of the parameters. This is always "object".
    /// </summary>
    public string Type => "object";

    /// <summary>
    /// Gets or sets the JSOn schema of the properties.
    /// </summary>
    public IDictionary<string, KernelJsonSchema> Properties { get; set; } = new Dictionary<string, KernelJsonSchema>();

    /// <summary>
    /// Gets or sets the list of required properties.
    /// </summary>
    public IList<string> Required { get; set; } = new List<string>();
}
