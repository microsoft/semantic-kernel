// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;
using System.Linq;

namespace KernelHttpServer.Model;

public class Skill
{
    public string Name { get; set; } = string.Empty;

    public string FunctionName { get; set; } = string.Empty;

    public string PromptTemplate { get; set; } = string.Empty;

    public int MaxTokens { get; set; }

    public float TopP { get; set; }

    public float Temperature { get; set; }

    public IEnumerable<string> StopSequences { get; set; } = Enumerable.Empty<string>();
}
