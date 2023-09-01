// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.ComponentModel;
using System.Runtime.CompilerServices;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.Extensions.Logging;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.AI.TextCompletion;
using Microsoft.SemanticKernel.Events;
using Microsoft.SemanticKernel.Orchestration;
using Microsoft.SemanticKernel.SkillDefinition;
using Moq;
using Xunit;

// ReSharper disable StringLiteralTypo

namespace SemanticKernel.UnitTests;

public class KernelTests
{
    [Fact]
    public void ItProvidesAccessToFunctionsViaSkillCollection()
    {
        // Arrange
        var factory = new Mock<Func<ILoggerFactory, ITextCompletion>>();
        var kernel = Kernel.Builder
            .WithDefaultAIService<ITextCompletion>(factory.Object)
            .Build();

        var nativeSkill = new MySkill();
        kernel.CreateSemanticFunction(promptTemplate: "Tell me a joke", functionName: "joker", skillName: "jk", description: "Nice fun");
        kernel.ImportSkill(nativeSkill, "mySk");

        // Act
        FunctionsView data = kernel.Skills.GetFunctionsView();

        // Assert - 3 functions, var name is not case sensitive
        Assert.True(data.IsSemantic("jk", "joker"));
        Assert.True(data.IsSemantic("JK", "JOKER"));
        Assert.False(data.IsNative("jk", "joker"));
        Assert.False(data.IsNative("JK", "JOKER"));
        Assert.True(data.IsNative("mySk", "sayhello"));
        Assert.True(data.IsNative("MYSK", "SayHello"));
        Assert.True(data.IsNative("mySk", "ReadSkillCollectionAsync"));
        Assert.True(data.IsNative("MYSK", "readskillcollectionasync"));
        Assert.Single(data.SemanticFunctions["Jk"]);
        Assert.Equal(3, data.NativeFunctions["mySk"].Count);
    }

    [Fact]
    public async Task ItProvidesAccessToFunctionsViaSKContextAsync()
    {
        // Arrange
        var factory = new Mock<Func<ILoggerFactory, KernelConfig, ITextCompletion>>();
        var kernel = Kernel.Builder
            .WithAIService<ITextCompletion>("x", factory.Object)
            .Build();

        var nativeSkill = new MySkill();
        kernel.CreateSemanticFunction("Tell me a joke", functionName: "joker", skillName: "jk", description: "Nice fun");
        var skill = kernel.ImportSkill(nativeSkill, "mySk");

        // Act
        SKContext result = await kernel.RunAsync(skill["ReadSkillCollectionAsync"]);

        // Assert - 3 functions, var name is not case sensitive
        Assert.Equal("Nice fun", result.Variables["jk.joker"]);
        Assert.Equal("Nice fun", result.Variables["JK.JOKER"]);
        Assert.Equal("Just say hello", result.Variables["mySk.sayhello"]);
        Assert.Equal("Just say hello", result.Variables["mySk.SayHello"]);
        Assert.Equal("Export info.", result.Variables["mySk.ReadSkillCollectionAsync"]);
        Assert.Equal("Export info.", result.Variables["mysk.readskillcollectionasync"]);
    }

    [Fact]
    public async Task RunAsyncDoesNotRunWhenCancelledAsync()
    {
        // Arrange
        var kernel = Kernel.Builder.Build();
        var nativeSkill = new MySkill();
        var skill = kernel.ImportSkill(nativeSkill, "mySk");

        using CancellationTokenSource cts = new();
        cts.Cancel();

        // Act
        SKContext result = await kernel.RunAsync(cts.Token, skill["GetAnyValue"]);

        // Assert
        Assert.True(string.IsNullOrEmpty(result.Result));
        Assert.True(result.ErrorOccurred);
        Assert.True(result.LastException is OperationCanceledException);
    }

    [Fact]
    public async Task RunAsyncRunsWhenNotCancelledAsync()
    {
        // Arrange
        var kernel = Kernel.Builder.Build();
        var nativeSkill = new MySkill();
        kernel.ImportSkill(nativeSkill, "mySk");

        using CancellationTokenSource cts = new();

        // Act
        SKContext result = await kernel.RunAsync(cts.Token, kernel.Func("mySk", "GetAnyValue"));

        // Assert
        Assert.False(string.IsNullOrEmpty(result.Result));
        Assert.False(result.ErrorOccurred);
        Assert.False(result.LastException is OperationCanceledException);
    }

    [Fact]
    public void ItImportsSkillsNotCaseSensitive()
    {
        // Act
        IDictionary<string, ISKFunction> skill = Kernel.Builder.Build().ImportSkill(new MySkill(), "test");

        // Assert
        Assert.Equal(3, skill.Count);
        Assert.True(skill.ContainsKey("GetAnyValue"));
        Assert.True(skill.ContainsKey("getanyvalue"));
        Assert.True(skill.ContainsKey("GETANYVALUE"));
    }

    [Fact]
    public void ItAllowsToImportSkillsInTheGlobalNamespace()
    {
        // Arrange
        var kernel = Kernel.Builder.Build();

        // Act
        IDictionary<string, ISKFunction> skill = kernel.ImportSkill(new MySkill());

        // Assert
        Assert.Equal(3, skill.Count);
        Assert.True(kernel.Skills.TryGetFunction("GetAnyValue", out ISKFunction? functionInstance));
        Assert.NotNull(functionInstance);
    }

    [Fact]
    public void ItAllowsToImportTheSameSkillMultipleTimes()
    {
        // Arrange
        var kernel = Kernel.Builder.Build();

        // Act - Assert no exception occurs
        kernel.ImportSkill(new MySkill());
        kernel.ImportSkill(new MySkill());
        kernel.ImportSkill(new MySkill());
    }

    [Theory]
    [InlineData(1)]
    [InlineData(2)]
    public async Task RunAsyncHandlesPreInvocation(int pipelineCount)
    {
        // Arrange
        var sut = Kernel.Builder.Build();
        var semanticFunction = sut.CreateSemanticFunction("Write a simple phrase about UnitTests");
        var (mockTextResult, mockTextCompletion) = this.SetupMocks();

        semanticFunction.SetAIService(() => mockTextCompletion.Object);
        var invoked = 0;
        sut.FunctionInvoking += (object? sender, FunctionInvokingEventArgs e) =>
        {
            invoked++;
        };
        List<ISKFunction> functions = new();
        for (int i = 0; i < pipelineCount; i++)
        {
            functions.Add(semanticFunction);
        }

        // Act
        var result = await sut.RunAsync(functions.ToArray());

        // Assert
        Assert.Equal(pipelineCount, invoked);
        mockTextCompletion.Verify(m => m.GetCompletionsAsync(It.IsAny<string>(), It.IsAny<CompleteRequestSettings>(), It.IsAny<CancellationToken>()), Times.Exactly(pipelineCount));
    }

    [Fact]
    public async Task RunAsyncHandlesPreInvocationWasCancelled()
    {
        // Arrange
        var sut = Kernel.Builder.Build();
        var semanticFunction = sut.CreateSemanticFunction("Write a simple phrase about UnitTests");
        var input = "This input should not change after cancel";
        var invoked = false;
        sut.FunctionInvoking += (object? sender, FunctionInvokingEventArgs e) =>
        {
            invoked = true;
            e.Cancel();
        };

        // Act
        var result = await sut.RunAsync(input, semanticFunction);

        // Assert
        Assert.True(invoked);
        Assert.Equal(input, result.Result);
    }

    [Fact]
    public async Task RunAsyncHandlesPreInvocationCancelationDontRunSubsequentFunctionsInThePipeline()
    {
        // Arrange
        var sut = Kernel.Builder.Build();
        var (mockTextResult, mockTextCompletion) = this.SetupMocks();
        var semanticFunction = sut.CreateSemanticFunction("Write a simple phrase about UnitTests");
        semanticFunction.SetAIService(() => mockTextCompletion.Object);

        var invoked = 0;
        sut.FunctionInvoking += (object? sender, FunctionInvokingEventArgs e) =>
        {
            invoked++;
            e.Cancel();
        };

        // Act
        var result = await sut.RunAsync(semanticFunction, semanticFunction);

        // Assert
        Assert.Equal(1, invoked);
        mockTextCompletion.Verify(m => m.GetCompletionsAsync(It.IsAny<string>(), It.IsAny<CompleteRequestSettings>(), It.IsAny<CancellationToken>()), Times.Never);
    }

    [Fact]
    public async Task RunAsyncPreInvocationCancelationDontTriggerInvokedHandler()
    {
        // Arrange
        var sut = Kernel.Builder.Build();
        var semanticFunction = sut.CreateSemanticFunction("Write a simple phrase about UnitTests");
        var invoked = 0;

        sut.FunctionInvoking += (object? sender, FunctionInvokingEventArgs e) =>
        {
            e.Cancel();
        };

        sut.FunctionInvoked += (object? sender, FunctionInvokedEventArgs e) =>
        {
            invoked++;
        };

        // Act
        var result = await sut.RunAsync(semanticFunction);

        // Assert
        Assert.Equal(0, invoked);
    }

    [Fact]
    public async Task RunAsyncPreInvocationSkipDontTriggerInvokedHandler()
    {
        // Arrange
        var sut = Kernel.Builder.Build();
        var (mockTextResult, mockTextCompletion) = this.SetupMocks();
        var semanticFunction1 = sut.CreateSemanticFunction("Write one phrase about UnitTests", functionName: "SkipMe");
        var semanticFunction2 = sut.CreateSemanticFunction("Write two phrases about UnitTests", functionName: "DontSkipMe");
        semanticFunction2.SetAIService(() => mockTextCompletion.Object);
        var invoked = 0;
        var invoking = 0;
        string invokedFunction = string.Empty;

        sut.FunctionInvoking += (object? sender, FunctionInvokingEventArgs e) =>
        {
            invoking++;
            if (e.FunctionView.Name == "SkipMe")
            {
                e.Skip();
            }
        };

        sut.FunctionInvoked += (object? sender, FunctionInvokedEventArgs e) =>
        {
            invokedFunction = e.FunctionView.Name;
            invoked++;
        };

        // Act
        var result = await sut.RunAsync(
            semanticFunction1,
            semanticFunction2);

        // Assert
        Assert.Equal(2, invoking);
        Assert.Equal(1, invoked);
        Assert.Equal("DontSkipMe", invokedFunction);
    }

    [Theory]
    [InlineData(1)]
    [InlineData(2)]
    public async Task RunAsyncHandlesPostInvocation(int pipelineCount)
    {
        // Arrange
        var sut = Kernel.Builder.Build();
        var semanticFunction = sut.CreateSemanticFunction("Write a simple phrase about UnitTests");
        var (mockTextResult, mockTextCompletion) = this.SetupMocks();

        semanticFunction.SetAIService(() => mockTextCompletion.Object);
        var invoked = 0;

        sut.FunctionInvoked += (object? sender, FunctionInvokedEventArgs e) =>
        {
            invoked++;
        };

        List<ISKFunction> functions = new();
        for (int i = 0; i < pipelineCount; i++)
        {
            functions.Add(semanticFunction);
        }

        // Act
        var result = await sut.RunAsync(functions.ToArray());

        // Assert
        Assert.Equal(pipelineCount, invoked);
        mockTextCompletion.Verify(m => m.GetCompletionsAsync(It.IsAny<string>(), It.IsAny<CompleteRequestSettings>(), It.IsAny<CancellationToken>()), Times.Exactly(pipelineCount));
    }

    [Fact(Skip = "Template Engine is not available. Null template engine will fail the test")]
    public async Task RunAsyncHandlerEventArgsPromptMatches()
    {
        // Arrange
        var sut = Kernel.Builder.Build();
        var prompt = "Write a simple phrase about UnitTests {{$input}}";
        var semanticFunction = sut.CreateSemanticFunction(prompt);
        var (mockTextResult, mockTextCompletion) = this.SetupMocks();

        semanticFunction.SetAIService(() => mockTextCompletion.Object);
        var input = "Importance";
        var generatedPromptPreExecution = string.Empty;
        var generatedPromptPostExecution = string.Empty;

        sut.FunctionInvoking += (object? sender, FunctionInvokingEventArgs e) =>
        {
            if (e is SemanticFunctionInvokingEventArgs se)
            {
                generatedPromptPreExecution = se.RenderedPrompt;
            }
        };

        sut.FunctionInvoked += (object? sender, FunctionInvokedEventArgs e) =>
        {
            if (e is SemanticFunctionInvokedEventArgs se)
            {
                generatedPromptPostExecution = se.RenderedPrompt;
            }
        };

        // Act
        var result = await sut.RunAsync(input, semanticFunction);

        // Assert
        Assert.Equal(prompt.Replace("{{$input}}", input, StringComparison.OrdinalIgnoreCase), generatedPromptPreExecution);
        Assert.Equal(prompt.Replace("{{$input}}", input, StringComparison.OrdinalIgnoreCase), generatedPromptPostExecution);
        mockTextCompletion.Verify(m => m.GetCompletionsAsync(It.IsAny<string>(), It.IsAny<CompleteRequestSettings>(), It.IsAny<CancellationToken>()), Times.Once);
    }

    [Fact]
    public async Task RunAsyncChangeVariableInvokingHandler()
    {
        var sut = Kernel.Builder.Build();
        var prompt = "Write a simple phrase about UnitTests {{$input}}";
        var semanticFunction = sut.CreateSemanticFunction(prompt);
        var (mockTextResult, mockTextCompletion) = this.SetupMocks();
        semanticFunction.SetAIService(() => mockTextCompletion.Object);
        var originalInput = "Importance";
        var newInput = "Problems";

        sut.FunctionInvoking += (object? sender, FunctionInvokingEventArgs e) =>
        {
            e.SKContext.Variables.Update(newInput);
            e.SKContext.Variables.TryAdd("new", newInput);
        };

        // Act
        var context = await sut.RunAsync(originalInput, semanticFunction);

        // Assert
        Assert.Equal(context.Variables["new"], newInput);
    }

    [Fact]
    public async Task RunAsyncChangeVariableInvokedHandler()
    {
        var sut = Kernel.Builder.Build();
        var prompt = "Write a simple phrase about UnitTests {{$input}}";
        var semanticFunction = sut.CreateSemanticFunction(prompt);
        var (mockTextResult, mockTextCompletion) = this.SetupMocks();
        semanticFunction.SetAIService(() => mockTextCompletion.Object);
        var originalInput = "Importance";
        var newInput = "Problems";

        sut.FunctionInvoked += (object? sender, FunctionInvokedEventArgs e) =>
        {
            e.SKContext.Variables.Update(newInput);
        };

        // Act
        var context = await sut.RunAsync(originalInput, semanticFunction);

        // Assert
        Assert.Equal(context.Variables.Input, newInput);
    }

    public class MySkill
    {
        [SKFunction, Description("Return any value.")]
        public string GetAnyValue()
        {
            return Guid.NewGuid().ToString();
        }

        [SKFunction, Description("Just say hello")]
        public void SayHello()
        {
            Console.WriteLine("Hello folks!");
        }

        [SKFunction, Description("Export info."), SKName("ReadSkillCollectionAsync")]
        public async Task<SKContext> ReadSkillCollectionAsync(SKContext context)
        {
            await Task.Delay(0);

            if (context.Skills == null)
            {
                Assert.Fail("Skills collection is missing");
            }

            FunctionsView procMem = context.Skills.GetFunctionsView();

            foreach (KeyValuePair<string, List<FunctionView>> list in procMem.SemanticFunctions)
            {
                foreach (FunctionView f in list.Value)
                {
                    context.Variables[$"{list.Key}.{f.Name}"] = f.Description;
                }
            }

            foreach (KeyValuePair<string, List<FunctionView>> list in procMem.NativeFunctions)
            {
                foreach (FunctionView f in list.Value)
                {
                    context.Variables[$"{list.Key}.{f.Name}"] = f.Description;
                }
            }

            return context;
        }
    }

    private (Mock<ITextResult> textResultMock, Mock<ITextCompletion> textCompletionMock) SetupMocks()
    {
        var mockTextResult = new Mock<ITextResult>();
        mockTextResult.Setup(m => m.GetCompletionAsync(It.IsAny<CancellationToken>())).ReturnsAsync("LLM Result about UnitTests");

        var mockTextCompletion = new Mock<ITextCompletion>();
        mockTextCompletion.Setup(m => m.GetCompletionsAsync(It.IsAny<string>(), It.IsAny<CompleteRequestSettings>(), It.IsAny<CancellationToken>())).ReturnsAsync(new List<ITextResult> { mockTextResult.Object });

        return (mockTextResult, mockTextCompletion);
    }
}
