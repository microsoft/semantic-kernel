// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.Extensions.Logging;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.AI.TextCompletion;
using Microsoft.SemanticKernel.Orchestration;
using Microsoft.SemanticKernel.Security;
using Microsoft.SemanticKernel.SemanticFunctions;
using Microsoft.SemanticKernel.SkillDefinition;
using Moq;
using Xunit;

namespace SemanticKernel.UnitTests.Security;

/// <summary>
/// Unit tests of <see cref="TrustService"/>.
/// </summary>
public sealed class TrustServiceTests
{
    [Fact]
    public async Task SemanticSensitiveFunctionShouldNotFailWithTrustedInputAsync()
    {
        // Arrange
        ITrustService trustService = TrustService.DefaultTrusted;
        var factory = new Mock<Func<(ILogger, KernelConfig), ITextCompletion>>();
        var kernel = Kernel.Builder
            .WithAIService<ITextCompletion>("x", factory.Object)
            .WithTrustService(trustService).Build();
        var aiService = MockAIService();
        var context = new ContextVariables("my input");

        factory.Setup(x => x.Invoke(It.IsAny<(ILogger, KernelConfig)>())).Returns(aiService.Object);

        var func = kernel.CreateSemanticFunction(
            "Tell me a joke",
            functionName: "joker",
            skillName: "jk",
            description: "Nice fun",
            isSensitive: true
        );

        // Act
        var result = await kernel.RunAsync(context, "x", func);

        // Assert
        Assert.Empty(result.LastErrorDescription);
        Assert.False(result.ErrorOccurred);
        Assert.Null(result.LastException);
    }

    [Fact]
    public async Task SemanticSensitiveFunctionShouldFailWithUntrustedInputAsync()
    {
        // Arrange
        ITrustService trustService = TrustService.DefaultTrusted;
        var factory = new Mock<Func<(ILogger, KernelConfig), ITextCompletion>>();
        var kernel = Kernel.Builder
            .WithAIService<ITextCompletion>("x", factory.Object)
            .WithTrustService(trustService).Build();
        var aiService = MockAIService();
        // The input here is set as untrusted
        var context = new ContextVariables(TrustAwareString.CreateUntrusted("my input"));

        factory.Setup(x => x.Invoke(It.IsAny<(ILogger, KernelConfig)>())).Returns(aiService.Object);

        var func = kernel.CreateSemanticFunction(
            "Tell me a joke",
            functionName: "joker",
            skillName: "jk",
            description: "Nice fun",
            isSensitive: true
        );

        // Act
        var result = await kernel.RunAsync(context, "x", func);

        // Assert
        // We expect the UntrustedContentException to be thrown using the TrustService.DefaultTrusted
        Assert.True(result.ErrorOccurred);
        Assert.IsType<UntrustedContentException>(result.LastException);
        Assert.Equal(
            UntrustedContentException.ErrorCodes.SensitiveFunctionWithUntrustedContent,
            ((UntrustedContentException)result.LastException).ErrorCode
        );
    }

    [Fact]
    public async Task SemanticSensitiveFunctionWithDefaultUntrustedFlagAsync()
    {
        // Arrange
        // Here we are forcing the output of the function to always be untrusted with
        // defaultTrusted = false
        ITrustService trustService = TrustService.DefaultUntrusted;
        var factory = new Mock<Func<(ILogger, KernelConfig), ITextCompletion>>();
        var kernel = Kernel.Builder
            .WithAIService<ITextCompletion>("x", factory.Object)
            .WithTrustService(trustService).Build();
        var aiService = MockAIService();
        var context = new ContextVariables("my input");

        factory.Setup(x => x.Invoke(It.IsAny<(ILogger, KernelConfig)>())).Returns(aiService.Object);

        var func = kernel.CreateSemanticFunction(
            "Tell me a joke",
            functionName: "joker",
            skillName: "jk",
            description: "Nice fun",
            isSensitive: true
        );

        // Act
        var result = await kernel.RunAsync(context, "x", func);

        // Assert
        Assert.Null(result.LastException);
        Assert.Empty(result.LastErrorDescription);
        Assert.False(result.ErrorOccurred);
        // The output of the function is expected to be untrusted
        // but in this case no exception was thrown (the output was not used
        // by a sensitive function yet)
        Assert.False(result.IsTrusted);
    }

    [Fact]
    public async Task SemanticSensitiveFunctionShouldFailWithUntrustedTemplateRenderAsync()
    {
        // Arrange
        var trustService = TrustService.DefaultTrusted;
        var promptTemplateConfig = new PromptTemplateConfig { IsSensitive = true };
        var promptTemplate = new Mock<IPromptTemplate>();

        // Mock this to make the context untrusted when the template is rendered
        promptTemplate.Setup(x => x.RenderAsync(It.IsAny<SKContext>()))
            .Callback<SKContext>(ctx => ctx.Variables.Update(TrustAwareString.CreateUntrusted("some untrusted content")))
            .ReturnsAsync("unsafe prompt");

        promptTemplate
            .Setup(x => x.GetParameters())
            .Returns(new List<ParameterView>());

        var functionConfig = new SemanticFunctionConfig(promptTemplateConfig, promptTemplate.Object);
        var func = SKFunction.FromSemanticConfig(
            "exampleSkill",
            "exampleFunction",
            functionConfig,
            trustService
        );
        var aiService = new Mock<ITextCompletion>();

        // Act
        var result = await func.InvokeAsync(textCompletionService: aiService.Object);

        // Assert
        // Since the context was tagged an untrusted, the DefaultTrustHandler should throw
        Assert.True(result.ErrorOccurred);
        Assert.IsType<UntrustedContentException>(result.LastException);
        Assert.Equal(
            UntrustedContentException.ErrorCodes.SensitiveFunctionWithUntrustedContent,
            ((UntrustedContentException)result.LastException).ErrorCode
        );
    }

    [Fact]
    public async Task NativeSensitiveFunctionShouldNotFailWithTrustedInputAsync()
    {
        // Arrange
        ITrustService trustService = TrustService.DefaultTrusted;
        var factory = new Mock<Func<(ILogger, KernelConfig), ITextCompletion>>();
        var kernel = Kernel.Builder
            .WithAIService<ITextCompletion>("x", factory.Object)
            .WithTrustService(trustService).Build();
        var aiService = MockAIService();
        var context = new ContextVariables("my input");

        factory.Setup(x => x.Invoke(It.IsAny<(ILogger, KernelConfig)>())).Returns(aiService.Object);

        var func = kernel.ImportSkill(new MySkill(), nameof(MySkill))["Function1"];

        // Act
        var result = await kernel.RunAsync(context, "x", func);

        // Assert
        Assert.False(result.ErrorOccurred);
    }

    [Fact]
    public async Task NativeSensitiveFunctionShouldFailWithUntrustedInputAsync()
    {
        // Arrange
        ITrustService trustService = TrustService.DefaultTrusted;
        var factory = new Mock<Func<(ILogger, KernelConfig), ITextCompletion>>();
        var kernel = Kernel.Builder
            .WithAIService<ITextCompletion>("x", factory.Object)
            .WithTrustService(trustService).Build();
        var aiService = MockAIService();
        // Here the input is untrusted
        var context = new ContextVariables(TrustAwareString.CreateUntrusted("my input"));

        factory.Setup(x => x.Invoke(It.IsAny<(ILogger, KernelConfig)>())).Returns(aiService.Object);

        var func = kernel.ImportSkill(new MySkill(), nameof(MySkill))["Function1"];

        // Act
        var result = await kernel.RunAsync(context, "x", func);

        // Assert
        // We expect the TrustService.DefaultTrusted to throw because the context became untrusted
        Assert.True(result.ErrorOccurred);
        Assert.IsType<UntrustedContentException>(result.LastException);
        Assert.Equal(
            UntrustedContentException.ErrorCodes.SensitiveFunctionWithUntrustedContent,
            ((UntrustedContentException)result.LastException).ErrorCode
        );
    }

    private sealed class MySkill
    {
        [SKFunction("Function1", isSensitive: true)]
        public void Function1()
        {
        }
    }

    private static Mock<ITextCompletion> MockAIService()
    {
        var aiService = new Mock<ITextCompletion>();
        var textCompletionResult = new Mock<ITextCompletionResult>();

        textCompletionResult
            .Setup(x => x.GetCompletionAsync(It.IsAny<CancellationToken>()))
            .ReturnsAsync("some string");

        aiService
            .Setup(x => x.GetCompletionsAsync(It.IsAny<string>(), It.IsAny<CompleteRequestSettings>(), It.IsAny<CancellationToken>()))
            .ReturnsAsync(new List<ITextCompletionResult> { textCompletionResult.Object });

        return aiService;
    }
}
