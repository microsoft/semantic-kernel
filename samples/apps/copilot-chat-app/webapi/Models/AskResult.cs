// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;
using System.Linq;

namespace SemanticKernel.Service.Models;

public class AskResult
{
    public string Value { get; set; } = string.Empty;

    public IEnumerable<KeyValuePair<string, string>>? Variables { get; set; } = Enumerable.Empty<KeyValuePair<string, string>>();
}
