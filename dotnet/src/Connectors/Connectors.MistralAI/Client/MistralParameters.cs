// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;

namespace Microsoft.SemanticKernel.Connectors.MistralAI.Client;
internal class MistralParameters
{
    public string Type { get; set; } = "object";

    public IDictionary<string, KernelJsonSchema> Properties { get; set; } = new Dictionary<string, KernelJsonSchema>();

    public IList<string> Required { get; set; } = new List<string>();
}
