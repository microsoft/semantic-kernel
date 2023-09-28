// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.ComponentModel;
using System.Threading.Tasks;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Orchestration;
using Moq;
using Xunit;

namespace SemanticKernel.UnitTests.Functions;

public class SKContextTests
{
    private readonly Mock<IReadOnlyFunctionCollection> _functions;
    private readonly Mock<IKernel> _kernel;

    public SKContextTests()
    {
        this._functions = new Mock<IReadOnlyFunctionCollection>();
        this._kernel = new Mock<IKernel>();
    }

    [Fact]
    public void ItHasHelpersForContextVariables()
    {
        // Arrange
        var variables = new ContextVariables();
        var target = new SKContext(this._kernel.Object, variables, functions: this._functions.Object);
        variables.Set("foo1", "bar1");

        // Act
        target.Variables["foo2"] = "bar2";
        target.Variables["INPUT"] = Guid.NewGuid().ToString("N");

        // Assert
        Assert.Equal("bar1", target.Variables["foo1"]);
        Assert.Equal("bar1", target.Variables["foo1"]);
        Assert.Equal("bar2", target.Variables["foo2"]);
        Assert.Equal("bar2", target.Variables["foo2"]);
        Assert.Equal(target.Variables["INPUT"], target.Result);
        Assert.Equal(target.Variables["INPUT"], target.ToString());
        Assert.Equal(target.Variables["INPUT"], target.Variables.Input);
        Assert.Equal(target.Variables["INPUT"], target.Variables.ToString());
    }

    [Fact]
    public async Task ItHasHelpersForFunctionCollectionAsync()
    {
        // Arrange
        IDictionary<string, ISKFunction> functions = KernelBuilder.Create().ImportFunctions(new Parrot(), "test");
        this._functions.Setup(x => x.GetFunction("func")).Returns(functions["say"]);
        var target = new SKContext(this._kernel.Object, new ContextVariables(), this._functions.Object);
        Assert.NotNull(target.Functions);

        // Act
        var say = target.Functions.GetFunction("func");

        FunctionResult result = await say.InvokeAsync("ciao", this._kernel.Object);

        // Assert
        Assert.Equal("ciao", result.Context.Result);
        Assert.Equal("ciao", result.GetValue<string>());
    }

    private sealed class Parrot
    {
        [SKFunction, Description("say something")]
        // ReSharper disable once UnusedMember.Local
        public string Say(string input)
        {
            return input;
        }
    }
}
