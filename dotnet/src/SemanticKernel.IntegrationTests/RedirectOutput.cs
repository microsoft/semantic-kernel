// Copyright (c) Microsoft. All rights reserved.

using System.IO;
using System.Text;
using Xunit.Abstractions;

namespace SemanticKernel.IntegrationTests;

public class RedirectOutput : TextWriter
{
    private readonly ITestOutputHelper _output;

    public RedirectOutput(ITestOutputHelper output)
    {
        this._output = output;
    }

    public override Encoding Encoding { get; } = Encoding.UTF8;

    public override void WriteLine(string? value)
    {
        this._output.WriteLine(value);
    }
}
