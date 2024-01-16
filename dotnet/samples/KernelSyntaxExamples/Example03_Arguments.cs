// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Globalization;
using System.Threading.Tasks;
using Microsoft.SemanticKernel;
using Plugins;
using Xunit;
using Xunit.Abstractions;

namespace Examples;
// This example shows how to use kernel arguments when invoking functions.
public class Example03_Arguments : BaseTest
{
    [Fact]
    public async Task RunAsync()
    {
        this.WriteLine("======== Arguments ========");

        Kernel kernel = new();
        var textPlugin = kernel.ImportPluginFromType<StaticTextPlugin>();

        var arguments = new KernelArguments()
        {
            ["input"] = "Today is: ",
            ["day"] = DateTimeOffset.Now.ToString("dddd", CultureInfo.CurrentCulture)
        };

        // ** Different ways of executing functions with arguments **

        // Specify and get the value type as generic parameter
        string? resultValue = await kernel.InvokeAsync<string>(textPlugin["AppendDay"], arguments);
        this.WriteLine($"string -> {resultValue}");

        // If you need to access the result metadata, you can use the non-generic version to get the FunctionResult
        FunctionResult functionResult = await kernel.InvokeAsync(textPlugin["AppendDay"], arguments);
        var metadata = functionResult.Metadata;

        // Specify the type from the FunctionResult
        this.WriteLine($"FunctionResult.GetValue<string>() -> {functionResult.GetValue<string>()}");

        // FunctionResult.ToString() automatically converts the result to string
        this.WriteLine($"FunctionResult.ToString() -> {functionResult}");
    }

    public Example03_Arguments(ITestOutputHelper output) : base(output)
    {
    }
}
