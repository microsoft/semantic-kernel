﻿// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;
using System.Diagnostics.CodeAnalysis;

namespace Microsoft.SemanticKernel.Connectors.Weaviate;

#pragma warning disable CA1812 // 'GetSchemaResponse' is an internal class that is apparently never instantiated. If so, remove the code from the assembly. If this class is intended to contain only static members, make it 'static' (Module in Visual Basic).
[Experimental("SKEXP0020")]
internal sealed class GetSchemaResponse
#pragma warning restore CA1812 // 'GetSchemaResponse' is an internal class that is apparently never instantiated. If so, remove the code from the assembly. If this class is intended to contain only static members, make it 'static' (Module in Visual Basic).
{
    // ReSharper disable once CollectionNeverUpdated.Global
    public List<GetClassResponse>? Classes { get; set; }
}
