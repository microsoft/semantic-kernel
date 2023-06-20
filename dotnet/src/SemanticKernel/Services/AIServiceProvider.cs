// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;

namespace Microsoft.SemanticKernel.Services;

public class AIServiceProvider : NamedServiceProvider<IAIService>, IAIServiceProvider
{
    public AIServiceProvider(Dictionary<Type, Dictionary<string, Func<object>>> services, Dictionary<Type, string> defaultIds)
        : base(services, defaultIds)
    {
    }
}
