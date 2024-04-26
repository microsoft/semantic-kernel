// Copyright (c) Microsoft. All rights reserved.

using Microsoft.SemanticKernel.Plugins.Core;

namespace Examples;

public class MethodFunctions(ITestOutputHelper output) : BaseTest(output)
{
    [Fact]
    public Task RunAsync()
    {
        this.WriteLine("======== Functions ========");

        // Load native plugin
        var text = new TextPlugin();

        // Use function without kernel
        var result = text.Uppercase("ciao!");

        this.WriteLine(result);

        return Task.CompletedTask;
    }
}
