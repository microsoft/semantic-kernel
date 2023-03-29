// Copyright (c) Microsoft. All rights reserved.

namespace SemanticKernel.Service.Model;

public class Ask
{
    public string Value { get; set; } = string.Empty;

    public IEnumerable<KeyValuePair<string, string>> Inputs { get; set; } = Enumerable.Empty<KeyValuePair<string, string>>();
}
