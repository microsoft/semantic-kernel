// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;

namespace Microsoft.SemanticKernel.Experimental.Assistants;

public interface IPlugin
{
    IEnumerable<ISKFunction> Functions { get; }

    string Name { get; }
}
