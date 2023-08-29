// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.ComponentModel;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.Extensions.Logging;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.AI.TextCompletion;
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
        kernel.ImportSkill(nativeSkill, "mySk");

        // Act
        FunctionsView data = kernel.Skills.GetFunctionsView();

        // Assert - 3 functions, var name is not case sensitive
        Assert.True(data.IsNative("mySk", "sayhello"));
        Assert.True(data.IsNative("MYSK", "SayHello"));
        Assert.True(data.IsNative("mySk", "ReadSkillCollectionAsync"));
        Assert.True(data.IsNative("MYSK", "readskillcollectionasync"));
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
        var skill = kernel.ImportSkill(nativeSkill, "mySk");

        // Act
        SKContext result = await kernel.RunAsync(skill["ReadSkillCollectionAsync"]);

        // Assert - 3 functions, var name is not case sensitive
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
}
