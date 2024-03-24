// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;

namespace Microsoft.SemanticKernel.Connectors.MistralAI.Client;
internal class MistralParameters
{
    public string Type { get; set; }

    public IDictionary<string, MistralPropertyType> Properties { get; set; }

    public IList<string> Required { get; set; }
}
