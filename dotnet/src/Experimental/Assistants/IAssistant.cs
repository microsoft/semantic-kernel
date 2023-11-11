// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;

namespace Microsoft.SemanticKernel.Experimental.Assistants;

public interface IAssistant
{
    IEnumerable<ISKFunction> Functions { get; }

    string Name { get; }
}
