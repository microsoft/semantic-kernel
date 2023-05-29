// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Text;

namespace Microsoft.SemanticKernel.Orchestration;
public abstract class PromptResultBase
{
    public int InputUsage { get; set; }
    public int OutputUsage { get; set; }
    public int TotalUsage => this.InputUsage + this.OutputUsage;
}
