﻿// Copyright (c) Microsoft. All rights reserved.

using System.Diagnostics.CodeAnalysis;

namespace Microsoft.SemanticKernel.Connectors.Weaviate;

#pragma warning disable CA1812 // 'GraphErrorLocationsItems' is an internal class that is apparently never instantiated. If so, remove the code from the assembly. If this class is intended to contain only static members, make it 'static' (Module in Visual Basic).
[Experimental("SKEXP0020")]
internal sealed class GraphErrorLocationsItems
#pragma warning restore CA1812 // 'GraphErrorLocationsItems' is an internal class that is apparently never instantiated. If so, remove the code from the assembly. If this class is intended to contain only static members, make it 'static' (Module in Visual Basic).
{
    public long? Column { get; set; }
    public long? Line { get; set; }
}
