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
using Microsoft.SemanticKernel.SemanticFunctions;
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
        var factory = new Mock<Func<ILoggerFactory, ITextCompletion>>();
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

    [Theory]
    [InlineData(null, "Assistant is a large language model.")]
    [InlineData("My Chat Prompt", "My Chat Prompt")]
    public void ItUsesChatSystemPromptWhenProvided(string providedSystemChatPrompt, string expectedSystemChatPrompt)
    {
        // Arrange
        var mockTextCompletion = new Mock<ITextCompletion>();
        var mockCompletionResult = new Mock<ITextResult>();

        mockTextCompletion.Setup(c => c.GetCompletionsAsync(It.IsAny<string>(), It.IsAny<CompleteRequestSettings>(), It.IsAny<CancellationToken>())).ReturnsAsync(new[] { mockCompletionResult.Object });
        mockCompletionResult.Setup(cr => cr.GetCompletionAsync(It.IsAny<CancellationToken>())).ReturnsAsync("llmResult");

        var kernel = Kernel.Builder
            .WithAIService<ITextCompletion>("x", mockTextCompletion.Object)
            .Build();

        var templateConfig = new PromptTemplateConfig();
        templateConfig.Completion.ChatSystemPrompt = providedSystemChatPrompt;

        var func = kernel.CreateSemanticFunction("template", templateConfig, "functionName", "skillName");

        // Act
        kernel.RunAsync(func);

        // Assert
        mockTextCompletion.Verify(a => a.GetCompletionsAsync("template", It.Is<CompleteRequestSettings>(c => c.ChatSystemPrompt == expectedSystemChatPrompt), It.IsAny<CancellationToken>()), Times.Once());
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

    [Fact]
    public void ItUsesDefaultServiceWhenSpecified()
    {
        // Arrange
        var mockTextCompletion1 = new Mock<ITextCompletion>();
        var mockTextCompletion2 = new Mock<ITextCompletion>();
        var mockCompletionResult = new Mock<ITextResult>();

        mockTextCompletion1.Setup(c => c.GetCompletionsAsync(It.IsAny<string>(), It.IsAny<CompleteRequestSettings>(), It.IsAny<CancellationToken>())).ReturnsAsync(new[] { mockCompletionResult.Object });
        mockTextCompletion2.Setup(c => c.GetCompletionsAsync(It.IsAny<string>(), It.IsAny<CompleteRequestSettings>(), It.IsAny<CancellationToken>())).ReturnsAsync(new[] { mockCompletionResult.Object });
        mockCompletionResult.Setup(cr => cr.GetCompletionAsync(It.IsAny<CancellationToken>())).ReturnsAsync("llmResult");

        var kernel = Kernel.Builder
            .WithAIService<ITextCompletion>("service1", mockTextCompletion1.Object, false)
            .WithAIService<ITextCompletion>("service2", mockTextCompletion2.Object, true)
            .Build();

        var templateConfig = new PromptTemplateConfig();
        var func = kernel.CreateSemanticFunction("template", templateConfig, "functionName", "skillName");

        // Act
        kernel.RunAsync(func);

        // Assert
        mockTextCompletion1.Verify(a => a.GetCompletionsAsync("template", It.IsAny<CompleteRequestSettings>(), It.IsAny<CancellationToken>()), Times.Never());
        mockTextCompletion2.Verify(a => a.GetCompletionsAsync("template", It.IsAny<CompleteRequestSettings>(), It.IsAny<CancellationToken>()), Times.Once());
    }

    [Fact]
    public void ItUsesServiceIdWhenProvided()
    {
        // Arrange
        var mockTextCompletion1 = new Mock<ITextCompletion>();
        var mockTextCompletion2 = new Mock<ITextCompletion>();
        var mockCompletionResult = new Mock<ITextResult>();

        mockTextCompletion1.Setup(c => c.GetCompletionsAsync(It.IsAny<string>(), It.IsAny<CompleteRequestSettings>(), It.IsAny<CancellationToken>())).ReturnsAsync(new[] { mockCompletionResult.Object });
        mockTextCompletion2.Setup(c => c.GetCompletionsAsync(It.IsAny<string>(), It.IsAny<CompleteRequestSettings>(), It.IsAny<CancellationToken>())).ReturnsAsync(new[] { mockCompletionResult.Object });
        mockCompletionResult.Setup(cr => cr.GetCompletionAsync(It.IsAny<CancellationToken>())).ReturnsAsync("llmResult");

        var kernel = Kernel.Builder
            .WithAIService<ITextCompletion>("service1", mockTextCompletion1.Object, false)
            .WithAIService<ITextCompletion>("service2", mockTextCompletion2.Object, true)
            .Build();

        var templateConfig = new PromptTemplateConfig();
        templateConfig.Completion.ServiceId = "service1";
        var func = kernel.CreateSemanticFunction("template", templateConfig, "functionName", "skillName");

        // Act
        kernel.RunAsync(func);

        // Assert
        mockTextCompletion1.Verify(a => a.GetCompletionsAsync("template", It.IsAny<CompleteRequestSettings>(), It.IsAny<CancellationToken>()), Times.Once());
        mockTextCompletion2.Verify(a => a.GetCompletionsAsync("template", It.IsAny<CompleteRequestSettings>(), It.IsAny<CancellationToken>()), Times.Never());
    }

    [Fact]
    public async Task ItFailsIfInvalidServiceIdIsProvidedAsync()
    {
        // Arrange
        var mockTextCompletion1 = new Mock<ITextCompletion>();
        var mockTextCompletion2 = new Mock<ITextCompletion>();

        var kernel = Kernel.Builder
            .WithAIService<ITextCompletion>("service1", mockTextCompletion1.Object, false)
            .WithAIService<ITextCompletion>("service2", mockTextCompletion2.Object, true)
            .Build();

        var templateConfig = new PromptTemplateConfig();
        templateConfig.Completion.ServiceId = "service3";
        var func = kernel.CreateSemanticFunction("template", templateConfig, "functionName", "skillName");

        // Act
        SKContext result = await kernel.RunAsync(func);

        // Assert
        Assert.NotNull(result.LastException);
        Assert.Equal("Service of type Microsoft.SemanticKernel.AI.TextCompletion.ITextCompletion and name service3 not registered.", result.LastException.Message);
        Assert.True(result.ErrorOccurred);
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
