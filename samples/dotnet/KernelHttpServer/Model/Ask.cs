// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;
using System.Linq;

namespace KernelHttpServer.Model;

public class Ask
{
    public string Value { get; set; } = string.Empty;

    /// <summary>
    /// When a non-empty collection is given, only skills matching these names should be loaded
    /// </summary>
    public IEnumerable<string>? Skills { get; set; } = null;

    public IEnumerable<AskInput> Inputs { get; set; } = Enumerable.Empty<AskInput>();
}

public class AskInput
{
    public string Key { get; set; } = string.Empty;

    public string Value { get; set; } = string.Empty;
}
