// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Text;

namespace Connectors.AI.PaLM.TextCompletion;

public class ErrorCompletionResult
{
    public Filter[] filters { get; set; }
}

public class Filter
{
    public string reason { get; set; }
}
