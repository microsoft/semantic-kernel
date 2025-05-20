// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.Extensions.AI;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.ChatCompletion;
using Xunit;
using ChatMessageContent = Microsoft.SemanticKernel.ChatMessageContent;

namespace SemanticKernel.UnitTests.Filters.AutoFunctionInvocation;

public class AutoFunctionInvocationContextTests
{
    [Fact]
    public void ConstructorWithValidParametersCreatesInstance()
    {
        // Arrange
        var kernel = new Kernel();
        var function = KernelFunctionFactory.CreateFromMethod(() => "Test", "TestFunction");
        var result = new FunctionResult(function);
        var chatHistory = new ChatHistory();
        var chatMessageContent = new ChatMessageContent(AuthorRole.Assistant, "Test message");

        // Act
        var context = new AutoFunctionInvocationContext(
            kernel,
            function,
            result,
            chatHistory,
            chatMessageContent);

        // Assert
        Assert.NotNull(context);
        Assert.Same(kernel, context.Kernel);
        Assert.Same(function, context.Function);
        Assert.Same(result, context.Result);
        Assert.Same(chatHistory, context.ChatHistory);
        Assert.Same(chatMessageContent, context.ChatMessageContent);
    }

    [Fact]
    public void ConstructorWithNullKernelThrowsException()
    {
        // Arrange
        var function = KernelFunctionFactory.CreateFromMethod(() => "Test", "TestFunction");
        var result = new FunctionResult(function);
        var chatHistory = new ChatHistory();
        var chatMessageContent = new ChatMessageContent(AuthorRole.Assistant, "Test message");

        // Act & Assert
        Assert.Throws<ArgumentNullException>(() => new AutoFunctionInvocationContext(
            null!,
            function,
            result,
            chatHistory,
            chatMessageContent));
    }

    [Fact]
    public void ConstructorWithNullFunctionThrowsException()
    {
        // Arrange
        var kernel = new Kernel();
        var function = KernelFunctionFactory.CreateFromMethod(() => "Test", "TestFunction");
        var result = new FunctionResult(function);
        var chatHistory = new ChatHistory();
        var chatMessageContent = new ChatMessageContent(AuthorRole.Assistant, "Test message");

        // Act & Assert
        Assert.Throws<ArgumentNullException>(() => new AutoFunctionInvocationContext(
            kernel,
            null!,
            result,
            chatHistory,
            chatMessageContent));
    }

    [Fact]
    public void ConstructorWithNullResultThrowsException()
    {
        // Arrange
        var kernel = new Kernel();
        var function = KernelFunctionFactory.CreateFromMethod(() => "Test", "TestFunction");
        var chatHistory = new ChatHistory();
        var chatMessageContent = new ChatMessageContent(AuthorRole.Assistant, "Test message");

        // Act & Assert
        Assert.Throws<ArgumentNullException>(() => new AutoFunctionInvocationContext(
            kernel,
            function,
            null!,
            chatHistory,
            chatMessageContent));
    }

    [Fact]
    public void ConstructorWithNullChatHistoryThrowsException()
    {
        // Arrange
        var kernel = new Kernel();
        var function = KernelFunctionFactory.CreateFromMethod(() => "Test", "TestFunction");
        var result = new FunctionResult(function);
        var chatMessageContent = new ChatMessageContent(AuthorRole.Assistant, "Test message");

        // Act & Assert
        Assert.Throws<ArgumentNullException>(() => new AutoFunctionInvocationContext(
            kernel,
            function,
            result,
            null!,
            chatMessageContent));
    }

    [Fact]
    public void ConstructorWithNullChatMessageContentThrowsException()
    {
        // Arrange
        var kernel = new Kernel();
        var function = KernelFunctionFactory.CreateFromMethod(() => "Test", "TestFunction");
        var result = new FunctionResult(function);
        var chatHistory = new ChatHistory();

        // Act & Assert
        Assert.Throws<ArgumentNullException>(() => new AutoFunctionInvocationContext(
            kernel,
            function,
            result,
            chatHistory,
            null!));
    }

    [Fact]
    public void PropertiesReturnCorrectValues()
    {
        // Arrange
        var kernel = new Kernel();
        var function = KernelFunctionFactory.CreateFromMethod(() => "Test", "TestFunction");
        var result = new FunctionResult(function);
        var chatHistory = new ChatHistory();
        var chatMessageContent = new ChatMessageContent(AuthorRole.Assistant, "Test message");

        // Act
        var context = new AutoFunctionInvocationContext(
            kernel,
            function,
            result,
            chatHistory,
            chatMessageContent);

        // Assert
        Assert.Same(kernel, context.Kernel);
        Assert.Same(function, context.Function);
        Assert.Same(result, context.Result);
        Assert.Same(chatHistory, context.ChatHistory);
        Assert.Same(chatMessageContent, context.ChatMessageContent);
    }

    [Fact]
    public async Task AutoFunctionInvocationContextCanBeUsedInFilter()
    {
        // Arrange
        var kernel = new Kernel();
        var function = KernelFunctionFactory.CreateFromMethod(() => "Test", "TestFunction");
        var result = new FunctionResult(function);
        var chatHistory = new ChatHistory();
        var chatMessageContent = new ChatMessageContent(AuthorRole.Assistant, "Test message");

        var context = new AutoFunctionInvocationContext(
            kernel,
            function,
            result,
            chatHistory,
            chatMessageContent);

        bool filterWasCalled = false;

        // Create a simple filter that just sets a flag
        async Task FilterMethod(AutoFunctionInvocationContext ctx, Func<AutoFunctionInvocationContext, Task> next)
        {
            filterWasCalled = true;
            Assert.Same(context, ctx);
            await next(ctx);
        }

        // Act
        await FilterMethod(context, _ => Task.CompletedTask);

        // Assert
        Assert.True(filterWasCalled);
    }

    [Fact]
    public void ExecutionSettingsCanBeSetAndRetrieved()
    {
        // Arrange
        var kernel = new Kernel();
        var function = KernelFunctionFactory.CreateFromMethod(() => "Test", "TestFunction");
        var result = new FunctionResult(function);
        var chatHistory = new ChatHistory();
        var chatMessageContent = new ChatMessageContent(AuthorRole.Assistant, "Test message");
        var executionSettings = new PromptExecutionSettings();

        var options = new KernelChatOptions(kernel, settings: executionSettings)
        {
            ChatMessageContent = chatMessageContent,
        };

        // Act
        var context = new AutoFunctionInvocationContext(options, function);

        // Assert
        Assert.Same(executionSettings, context.ExecutionSettings);
    }

    [Fact]
    public async Task KernelFunctionCloneWithKernelUsesProvidedKernel()
    {
        // Arrange
        var originalKernel = new Kernel();
        var newKernel = new Kernel();

        // Create a function that returns the kernel's hash code
        var function = KernelFunctionFactory.CreateFromMethod(
            (Kernel k) => k.GetHashCode().ToString(),
            "GetKernelHashCode");

        // Act
        // Create AIFunctions with different kernels
        var aiFunction1 = function.WithKernel(originalKernel);
        var aiFunction2 = function.WithKernel(newKernel);

        // Invoke both functions
        var args = new AIFunctionArguments();
        var result1 = await aiFunction1.InvokeAsync(args, default);
        var result2 = await aiFunction2.InvokeAsync(args, default);

        // Assert
        // The results should be different because they use different kernels
        Assert.NotNull(result1);
        Assert.NotNull(result2);
        Assert.NotEqual(result1, result2);
        Assert.Equal(originalKernel.GetHashCode().ToString(), result1.ToString());
        Assert.Equal(newKernel.GetHashCode().ToString(), result2.ToString());
    }

    // Let's simplify our approach and use a different testing strategy
    [Fact]
    public void ArgumentsPropertyHandlesKernelArguments()
    {
        // Arrange
        var kernel = new Kernel();
        var function = KernelFunctionFactory.CreateFromMethod(() => "Test", "TestFunction");
        var result = new FunctionResult(function);
        var chatHistory = new ChatHistory();
        var chatMessageContent = new ChatMessageContent(AuthorRole.Assistant, "Test message");

        // Create KernelArguments and set them via the init property
        var kernelArgs = new KernelArguments { ["test"] = "value" };

        // Set the arguments via the init property
        var contextWithArgs = new AutoFunctionInvocationContext(
            kernel,
            function,
            result,
            chatHistory,
            chatMessageContent)
        {
            Arguments = kernelArgs
        };

        // Act & Assert
        Assert.Same(kernelArgs, contextWithArgs.Arguments);
    }

    [Fact]
    public void ArgumentsPropertyInitializesEmptyKernelArgumentsWhenSetToNull()
    {
        // Arrange
        var kernel = new Kernel();
        var function = KernelFunctionFactory.CreateFromMethod(() => "Test", "TestFunction");
        var result = new FunctionResult(function);
        var chatHistory = new ChatHistory();
        var chatMessageContent = new ChatMessageContent(AuthorRole.Assistant, "Test message");

        // Set the arguments to null via the init property
        var contextWithNullArgs = new AutoFunctionInvocationContext(
            kernel,
            function,
            result,
            chatHistory,
            chatMessageContent)
        {
            Arguments = null
        };

        // Act & Assert
        Assert.NotNull(contextWithNullArgs.Arguments);
        Assert.IsType<KernelArguments>(contextWithNullArgs.Arguments);
        Assert.Empty(contextWithNullArgs.Arguments);
    }

    [Fact]
    public void ArgumentsPropertyCanBeSetWithMultipleValues()
    {
        // Arrange
        var kernel = new Kernel();
        var function = KernelFunctionFactory.CreateFromMethod(() => "Test", "TestFunction");
        var result = new FunctionResult(function);
        var chatHistory = new ChatHistory();
        var chatMessageContent = new ChatMessageContent(AuthorRole.Assistant, "Test message");

        // Create KernelArguments with multiple values
        var kernelArgs = new KernelArguments
        {
            ["string"] = "value",
            ["int"] = 42,
            ["bool"] = true,
            ["object"] = new object()
        };

        // Set the arguments via the init property
        var context = new AutoFunctionInvocationContext(
            kernel,
            function,
            result,
            chatHistory,
            chatMessageContent)
        {
            Arguments = kernelArgs
        };

        // Act & Assert
        Assert.Same(kernelArgs, context.Arguments);
        Assert.Equal(4, context.Arguments.Count);
        Assert.Equal("value", context.Arguments["string"]);
        Assert.Equal(42, context.Arguments["int"]);
        Assert.Equal(true, context.Arguments["bool"]);
        Assert.NotNull(context.Arguments["object"]);
    }

    [Fact]
    public void ArgumentsPropertyCanBeSetWithExecutionSettings()
    {
        // Arrange
        var kernel = new Kernel();
        var function = KernelFunctionFactory.CreateFromMethod(() => "Test", "TestFunction");
        var result = new FunctionResult(function);
        var chatHistory = new ChatHistory();
        var chatMessageContent = new ChatMessageContent(AuthorRole.Assistant, "Test message");
        var executionSettings = new PromptExecutionSettings();

        // Create KernelArguments with execution settings
        var kernelArgs = new KernelArguments(executionSettings)
        {
            ["test"] = "value"
        };

        // Set the arguments via the init property
        var context = new AutoFunctionInvocationContext(
            kernel,
            function,
            result,
            chatHistory,
            chatMessageContent)
        {
            Arguments = kernelArgs
        };

        // Act & Assert
        Assert.Same(kernelArgs, context.Arguments);
        Assert.Equal("value", context.Arguments["test"]);
        Assert.Same(executionSettings, context.Arguments.ExecutionSettings?[PromptExecutionSettings.DefaultServiceId]);
    }

    [Fact]
    public void ArgumentsPropertyThrowsWhenBaseArgumentsIsNotKernelArguments()
    {
        // Arrange
        var kernel = new Kernel();
        var function = KernelFunctionFactory.CreateFromMethod(() => "Test", "TestFunction");
        var result = new FunctionResult(function);
        var chatHistory = new ChatHistory();
        var chatMessageContent = new ChatMessageContent(AuthorRole.Assistant, "Test message");

        var context = new AutoFunctionInvocationContext(
            kernel,
            function,
            result,
            chatHistory,
            chatMessageContent);

        ((Microsoft.Extensions.AI.FunctionInvocationContext)context).Arguments = new AIFunctionArguments();

        // Act & Assert
        Assert.Throws<InvalidOperationException>(() => context.Arguments);
    }

    [Fact]
    public void InternalConstructorWithOptionsAndAIFunctionSetsPropertiesCorrectly()
    {
        // Arrange
        var kernel = new Kernel();
        var function = KernelFunctionFactory.CreateFromMethod(() => "Test", "TestFunction");
        var chatMessageContent = new ChatMessageContent(AuthorRole.Assistant, "Test message");
        var executionSettings = new PromptExecutionSettings();

        var options = new KernelChatOptions(kernel, settings: executionSettings)
        {
            ChatMessageContent = chatMessageContent,
        };

        // Act
        var context = new AutoFunctionInvocationContext(options, function);

        // Assert
        Assert.Same(kernel, context.Kernel);
        Assert.Same(function, context.Function);
        Assert.Same(executionSettings, context.ExecutionSettings);
        Assert.Same(chatMessageContent, context.ChatMessageContent);
        Assert.NotNull(context.Result);
        Assert.Equal(kernel.Culture, context.Result.Culture);
    }

    [Fact]
    public void InternalConstructorWithOptionsAndAIFunctionThrowsWithNullOptions()
    {
        // Arrange
        var function = KernelFunctionFactory.CreateFromMethod(() => "Test", "TestFunction");

        // Act & Assert
        Assert.Throws<ArgumentNullException>(() => new AutoFunctionInvocationContext(null!, function));
    }

    [Fact]
    public void InternalConstructorWithOptionsAndAIFunctionThrowsWithNullFunction()
    {
        // Arrange
        var kernel = new Kernel();
        var chatMessageContent = new ChatMessageContent(AuthorRole.Assistant, "Test message");

        var options = new KernelChatOptions(kernel)
        {
            ChatMessageContent = chatMessageContent,
        };

        // Act & Assert
        Assert.Throws<ArgumentNullException>(() => new AutoFunctionInvocationContext(options, null!));
    }

    [Fact]
    public void InternalConstructorWithOptionsAndAIFunctionThrowsWithNonKernelFunction()
    {
        // Arrange
        var kernel = new Kernel();
        var chatMessageContent = new ChatMessageContent(AuthorRole.Assistant, "Test message");
        var testAIFunction = new TestAIFunction("TestFunction");

        var options = new KernelChatOptions(kernel)
        {
            ChatMessageContent = chatMessageContent,
        };

        // Act & Assert
        Assert.Throws<InvalidOperationException>(() => new AutoFunctionInvocationContext(options, testAIFunction));
    }

    [Fact]
    public void InternalConstructorWithOptionsAndAIFunctionThrowsWithMissingKernel()
    {
        // Arrange
        var function = KernelFunctionFactory.CreateFromMethod(() => "Test", "TestFunction");
        var chatMessageContent = new ChatMessageContent(AuthorRole.Assistant, "Test message");

        // Act & Assert
        Assert.Throws<ArgumentNullException>(() =>
            // Create options without kernel
            new AutoFunctionInvocationContext(new(null!) { ChatMessageContent = chatMessageContent }, function)
        );
    }

    [Fact]
    public void InternalConstructorWithOptionsAndAIFunctionThrowsWithMissingChatMessageContent()
    {
        // Arrange
        var kernel = new Kernel();
        var function = KernelFunctionFactory.CreateFromMethod(() => "Test", "TestFunction");

        // Create options without chat message content
        var options = new KernelChatOptions(kernel);

        // Act & Assert
        Assert.Throws<ArgumentNullException>(() => new AutoFunctionInvocationContext(options, function));
    }

    [Fact]
    public void InternalConstructorWithOptionsAndAIFunctionCanSetAndRetrieveArguments()
    {
        // Arrange
        var kernel = new Kernel();
        var function = KernelFunctionFactory.CreateFromMethod(() => "Test", "TestFunction");
        var chatMessageContent = new ChatMessageContent(AuthorRole.Assistant, "Test message");
        var kernelArgs = new KernelArguments { ["test"] = "value" };

        // Create options with required properties
        var options = new KernelChatOptions(kernel)
        {
            ChatMessageContent = chatMessageContent,
        };

        // Act
        var context = new AutoFunctionInvocationContext(options, function)
        {
            Arguments = kernelArgs
        };

        // Assert
        Assert.Same(kernelArgs, context.Arguments);
        Assert.Equal("value", context.Arguments["test"]);
    }

    [Fact]
    public void InternalConstructorWithOptionsAndAIFunctionInitializesEmptyArgumentsWhenSetToNull()
    {
        // Arrange
        var kernel = new Kernel();
        var function = KernelFunctionFactory.CreateFromMethod(() => "Test", "TestFunction");
        var chatMessageContent = new ChatMessageContent(AuthorRole.Assistant, "Test message");

        // Create options with required properties
        var options = new KernelChatOptions(kernel)
        {
            ChatMessageContent = chatMessageContent,
        };
        // Act
        var context = new AutoFunctionInvocationContext(options, function)
        {
            Arguments = null
        };

        // Assert
        Assert.NotNull(context.Arguments);
        Assert.IsType<KernelArguments>(context.Arguments);
        Assert.Empty(context.Arguments);
    }

    // Helper class for testing non-KernelFunction AIFunction
    private sealed class TestAIFunction : AIFunction
    {
        public TestAIFunction(string name, string description = "")
        {
            this.Name = name;
            this.Description = description;
        }

        public override string Name { get; }

        public override string Description { get; }

        protected override ValueTask<object?> InvokeCoreAsync(AIFunctionArguments arguments, CancellationToken cancellationToken)
        {
            return ValueTask.FromResult<object?>("Test result");
        }
    }
}
