// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Reflection;
using System.Threading.Tasks;
using Microsoft.Extensions.Logging;
using Microsoft.SemanticKernel.Orchestration;
using Microsoft.SemanticKernel.SkillDefinition;
using Moq;
using Xunit;

namespace SemanticKernel.UnitTests.SkillDefinition;

public sealed class SKFunctionTests2
{
    private readonly Mock<ILogger> _log;
    private readonly Mock<IReadOnlySkillCollection> _skills;

    private static string s_expected = string.Empty;
    private static string s_actual = string.Empty;

    public SKFunctionTests2()
    {
        this._log = new Mock<ILogger>();
        this._skills = new Mock<IReadOnlySkillCollection>();

        s_expected = Guid.NewGuid().ToString("D");
    }

    [Fact]
    public async Task ItSupportsStaticVoidVoidAsync()
    {
        // Arrange
        [SKFunction("Test")]
        [SKFunctionName("Test")]
        static void Test()
        {
            s_actual = s_expected;
        }

        var context = this.MockContext("");

        // Act
        var function = SKFunction.FromNativeMethod(Method(Test), log: this._log.Object);
        Assert.NotNull(function);
        SKContext result = await function.InvokeAsync(context);

        // Assert
        Assert.False(result.ErrorOccurred);
        Assert.Equal(s_expected, s_actual);
    }

    [Fact]
    public async Task ItSupportsStaticVoidStringAsync()
    {
        // Arrange
        [SKFunction("Test")]
        [SKFunctionName("Test")]
        static string Test()
        {
            s_actual = s_expected;
            return s_expected;
        }

        var context = this.MockContext("");

        // Act
        var function = SKFunction.FromNativeMethod(Method(Test), log: this._log.Object);
        Assert.NotNull(function);
        SKContext result = await function.InvokeAsync(context);

        // Assert
        Assert.False(result.ErrorOccurred);
        Assert.Equal(s_expected, s_actual);
        Assert.Equal(s_expected, result.Result);
        Assert.Equal(s_expected, context.Result);
    }

    [Fact]
    public async Task ItSupportsStaticVoidTaskStringAsync()
    {
        // Arrange
        [SKFunction("Test")]
        [SKFunctionName("Test")]
        static Task<string> Test()
        {
            s_actual = s_expected;
            return Task.FromResult(s_expected);
        }

        var context = this.MockContext("");

        // Act
        var function = SKFunction.FromNativeMethod(Method(Test), log: this._log.Object);
        Assert.NotNull(function);
        SKContext result = await function.InvokeAsync(context);

        // Assert
        Assert.False(result.ErrorOccurred);
        Assert.Equal(s_expected, s_actual);
        Assert.Equal(s_expected, context.Result);
        Assert.Equal(s_expected, result.Result);
    }

    [Fact]
    public async Task ItSupportsStaticContextVoidAsync()
    {
        // Arrange
        [SKFunction("Test")]
        [SKFunctionName("Test")]
        static void Test(SKContext cx)
        {
            s_actual = s_expected;
            cx["canary"] = s_expected;
        }

        var context = this.MockContext("xy");
        context["someVar"] = "qz";

        // Act
        var function = SKFunction.FromNativeMethod(Method(Test), log: this._log.Object);
        Assert.NotNull(function);
        SKContext result = await function.InvokeAsync(context);

        // Assert
        Assert.False(result.ErrorOccurred);
        Assert.Equal(s_expected, s_actual);
        Assert.Equal(s_expected, context["canary"]);
    }

    [Fact]
    public async Task ItSupportsStaticContextStringAsync()
    {
        // Arrange
        [SKFunction("Test")]
        [SKFunctionName("Test")]
        static string Test(SKContext cx)
        {
            s_actual = cx["someVar"];
            return "abc";
        }

        var context = this.MockContext("");
        context["someVar"] = s_expected;

        // Act
        var function = SKFunction.FromNativeMethod(Method(Test), log: this._log.Object);
        Assert.NotNull(function);
        SKContext result = await function.InvokeAsync(context);

        // Assert
        Assert.False(result.ErrorOccurred);
        Assert.Equal(s_expected, s_actual);
        Assert.Equal("abc", context.Result);
    }

    [Fact]
    public async Task ItSupportsInstanceContextStringNullableAsync()
    {
        // Arrange
        int invocationCount = 0;

        [SKFunction("Test")]
        [SKFunctionName("Test")]
        string? Test(SKContext cx)
        {
            invocationCount++;
            s_actual = cx["someVar"];
            return "abc";
        }

        var context = this.MockContext("");
        context["someVar"] = s_expected;

        // Act
        Func<SKContext, string?> method = Test;
        var function = SKFunction.FromNativeMethod(Method(method), method.Target, log: this._log.Object);
        Assert.NotNull(function);
        SKContext result = await function.InvokeAsync(context);

        // Assert
        Assert.False(result.ErrorOccurred);
        Assert.Equal(1, invocationCount);
        Assert.Equal(s_expected, s_actual);
        Assert.Equal("abc", context.Result);
    }

    [Fact]
    public async Task ItSupportsInstanceContextTaskStringAsync()
    {
        // Arrange
        int invocationCount = 0;

        [SKFunction("Test")]
        [SKFunctionName("Test")]
        Task<string> Test(SKContext cx)
        {
            invocationCount++;
            s_actual = s_expected;
            cx.Variables["canary"] = s_expected;
            return Task.FromResult(s_expected);
        }

        var context = this.MockContext("");

        // Act
        Func<SKContext, Task<string>> method = Test;
        var function = SKFunction.FromNativeMethod(Method(method), method.Target, log: this._log.Object);
        Assert.NotNull(function);
        SKContext result = await function.InvokeAsync(context);

        // Assert
        Assert.False(result.ErrorOccurred);
        Assert.Equal(1, invocationCount);
        Assert.Equal(s_expected, s_actual);
        Assert.Equal(s_actual, context.Result);
        Assert.Equal(s_expected, context["canary"]);
    }

    [Fact]
    public async Task ItSupportsInstanceContextTaskContextAsync()
    {
        // Arrange
        int invocationCount = 0;

        [SKFunction("Test")]
        [SKFunctionName("Test")]
        async Task<SKContext> TestAsync(SKContext cx)
        {
            await Task.Delay(0);
            invocationCount++;
            s_actual = s_expected;
            cx.Variables.Update("foo");
            cx["canary"] = s_expected;
            return cx;
        }

        var context = this.MockContext("");

        // Act
        Func<SKContext, Task<SKContext>> method = TestAsync;
        var function = SKFunction.FromNativeMethod(Method(method), method.Target, log: this._log.Object);
        Assert.NotNull(function);
        SKContext result = await function.InvokeAsync(context);

        // Assert
        Assert.False(result.ErrorOccurred);
        Assert.Equal(1, invocationCount);
        Assert.Equal(s_expected, s_actual);
        Assert.Equal(s_expected, context["canary"]);
        Assert.Equal("foo", context.Result);
    }

    [Fact]
    public async Task ItSupportsInstanceStringVoidAsync()
    {
        // Arrange
        int invocationCount = 0;

        [SKFunction("Test")]
        [SKFunctionName("Test")]
        void Test(string input)
        {
            invocationCount++;
            s_actual = s_expected + input;
        }

        var context = this.MockContext(".blah");

        // Act
        Action<string> method = Test;
        var function = SKFunction.FromNativeMethod(Method(method), method.Target, log: this._log.Object);
        Assert.NotNull(function);
        SKContext result = await function.InvokeAsync(context);

        // Assert
        Assert.False(result.ErrorOccurred);
        Assert.Equal(1, invocationCount);
        Assert.Equal(s_expected + ".blah", s_actual);
    }

    [Fact]
    public async Task ItSupportsInstanceStringStringAsync()
    {
        // Arrange
        int invocationCount = 0;

        [SKFunction("Test")]
        [SKFunctionName("Test")]
        string Test(string input)
        {
            invocationCount++;
            s_actual = s_expected;
            return "foo-bar";
        }

        var context = this.MockContext("");

        // Act
        Func<string, string> method = Test;
        var function = SKFunction.FromNativeMethod(Method(method), method.Target, log: this._log.Object);
        Assert.NotNull(function);
        SKContext result = await function.InvokeAsync(context);

        // Assert
        Assert.False(result.ErrorOccurred);
        Assert.Equal(1, invocationCount);
        Assert.Equal(s_expected, s_actual);
        Assert.Equal("foo-bar", context.Result);
    }

    [Fact]
    public async Task ItSupportsInstanceStringTaskStringAsync()
    {
        // Arrange
        int invocationCount = 0;

        [SKFunction("Test")]
        [SKFunctionName("Test")]
        Task<string> Test(string input)
        {
            invocationCount++;
            s_actual = s_expected;
            return Task.FromResult("hello there");
        }

        var context = this.MockContext("");

        // Act
        Func<string, Task<string>> method = Test;
        var function = SKFunction.FromNativeMethod(Method(method), method.Target, log: this._log.Object);
        Assert.NotNull(function);
        SKContext result = await function.InvokeAsync(context);

        // Assert
        Assert.False(result.ErrorOccurred);
        Assert.Equal(1, invocationCount);
        Assert.Equal(s_expected, s_actual);
        Assert.Equal("hello there", context.Result);
    }

    [Fact]
    public async Task ItSupportsInstanceStringContextVoidAsync()
    {
        // Arrange
        int invocationCount = 0;

        [SKFunction("Test")]
        [SKFunctionName("Test")]
        void Test(string input, SKContext cx)
        {
            invocationCount++;
            s_actual = s_expected;
            cx.Variables.Update("x y z");
            cx["canary"] = s_expected;
        }

        var context = this.MockContext("");

        // Act
        Action<string, SKContext> method = Test;
        var function = SKFunction.FromNativeMethod(Method(method), method.Target, log: this._log.Object);
        Assert.NotNull(function);
        SKContext result = await function.InvokeAsync(context);

        // Assert
        Assert.False(result.ErrorOccurred);
        Assert.Equal(1, invocationCount);
        Assert.Equal(s_expected, s_actual);
        Assert.Equal(s_expected, context["canary"]);
        Assert.Equal("x y z", context.Result);
    }

    [Fact]
    public async Task ItSupportsInstanceContextStringVoidAsync()
    {
        // Arrange
        int invocationCount = 0;

        [SKFunction("Test")]
        [SKFunctionName("Test")]
        void Test(SKContext cx, string input)
        {
            invocationCount++;
            s_actual = s_expected;
            cx.Variables.Update("x y z");
            cx["canary"] = s_expected;
        }

        var context = this.MockContext("");

        // Act
        Action<SKContext, string> method = Test;
        var function = SKFunction.FromNativeMethod(Method(method), method.Target, log: this._log.Object);
        Assert.NotNull(function);
        SKContext result = await function.InvokeAsync(context);

        // Assert
        Assert.False(result.ErrorOccurred);
        Assert.Equal(1, invocationCount);
        Assert.Equal(s_expected, s_actual);
        Assert.Equal(s_expected, context["canary"]);
        Assert.Equal("x y z", context.Result);
    }

    [Fact]
    public async Task ItSupportsStaticStringContextStringAsync()
    {
        // Arrange
        [SKFunction("Test")]
        [SKFunctionName("Test")]
        static string Test(string input, SKContext cx)
        {
            s_actual = s_expected;
            cx["canary"] = s_expected;
            cx.Variables.Update("x y z");
            // This value should overwrite "x y z"
            return "new data";
        }

        var context = this.MockContext("");

        // Act
        var function = SKFunction.FromNativeMethod(Method(Test), log: this._log.Object);
        Assert.NotNull(function);
        SKContext result = await function.InvokeAsync(context);

        // Assert
        Assert.False(result.ErrorOccurred);
        Assert.Equal(s_expected, s_actual);
        Assert.Equal(s_expected, context["canary"]);
        Assert.Equal("new data", context.Result);
    }

    [Fact]
    public async Task ItSupportsStaticStringContextTaskStringAsync()
    {
        // Arrange
        [SKFunction("Test")]
        [SKFunctionName("Test")]
        static Task<string> Test(string input, SKContext cx)
        {
            s_actual = s_expected;
            cx["canary"] = s_expected;
            cx.Variables.Update("x y z");
            // This value should overwrite "x y z"
            return Task.FromResult("new data");
        }

        var context = this.MockContext("");

        // Act
        var function = SKFunction.FromNativeMethod(Method(Test), log: this._log.Object);
        Assert.NotNull(function);
        SKContext result = await function.InvokeAsync(context);

        // Assert
        Assert.False(result.ErrorOccurred);
        Assert.Equal(s_expected, s_actual);
        Assert.Equal(s_expected, context["canary"]);
        Assert.Equal("new data", context.Result);
    }

    [Fact]
    public async Task ItSupportsStaticStringContextTaskContextAsync()
    {
        // Arrange
        [SKFunction("Test")]
        [SKFunctionName("Test")]
        static Task<SKContext> Test(string input, SKContext cx)
        {
            s_actual = s_expected;
            cx["canary"] = s_expected;
            cx.Variables.Update("x y z");

            // This value should overwrite "x y z". Contexts are merged.
            var newCx = new SKContext(
                new ContextVariables(input),
                skills: new Mock<IReadOnlySkillCollection>().Object);

            newCx.Variables.Update("new data");
            newCx["canary2"] = "222";

            return Task.FromResult(newCx);
        }

        var oldContext = this.MockContext("");
        oldContext["legacy"] = "something";

        // Act
        var function = SKFunction.FromNativeMethod(Method(Test), log: this._log.Object);
        Assert.NotNull(function);
        SKContext newContext = await function.InvokeAsync(oldContext);

        // Assert
        Assert.False(oldContext.ErrorOccurred);
        Assert.False(newContext.ErrorOccurred);

        Assert.Equal(s_expected, s_actual);

        Assert.True(oldContext.Variables.ContainsKey("canary"));
        Assert.False(oldContext.Variables.ContainsKey("canary2"));

        Assert.False(newContext.Variables.ContainsKey("canary"));
        Assert.True(newContext.Variables.ContainsKey("canary2"));

        Assert.Equal(s_expected, oldContext["canary"]);
        Assert.Equal("222", newContext["canary2"]);

        Assert.True(oldContext.Variables.ContainsKey("legacy"));
        Assert.False(newContext.Variables.ContainsKey("legacy"));

        Assert.Equal("x y z", oldContext.Result);
        Assert.Equal("new data", newContext.Result);
    }

    [Fact]
    public async Task ItSupportsStaticStringTaskAsync()
    {
        // Arrange
        [SKFunction("Test")]
        [SKFunctionName("Test")]
        static Task TestAsync(string input)
        {
            s_actual = s_expected;
            return Task.CompletedTask;
        }

        var context = this.MockContext("");

        // Act
        var function = SKFunction.FromNativeMethod(Method(TestAsync), log: this._log.Object);
        Assert.NotNull(function);
        SKContext result = await function.InvokeAsync(context);

        // Assert
        Assert.False(result.ErrorOccurred);
        Assert.Equal(s_expected, s_actual);
    }

    [Fact]
    public async Task ItSupportsStaticContextTaskAsync()
    {
        // Arrange
        [SKFunction("Test")]
        [SKFunctionName("Test")]
        static Task TestAsync(SKContext cx)
        {
            s_actual = s_expected;
            cx["canary"] = s_expected;
            cx.Variables.Update("x y z");
            return Task.CompletedTask;
        }

        var context = this.MockContext("");

        // Act
        var function = SKFunction.FromNativeMethod(Method(TestAsync), log: this._log.Object);
        Assert.NotNull(function);
        SKContext result = await function.InvokeAsync(context);

        // Assert
        Assert.False(result.ErrorOccurred);
        Assert.Equal(s_expected, s_actual);
        Assert.Equal(s_expected, context["canary"]);
        Assert.Equal("x y z", context.Result);
    }

    [Fact]
    public async Task ItSupportsStaticStringContextTaskAsync()
    {
        // Arrange
        [SKFunction("Test")]
        [SKFunctionName("Test")]
        static Task TestAsync(string input, SKContext cx)
        {
            s_actual = s_expected;
            cx["canary"] = s_expected;
            cx.Variables.Update(input + "x y z");
            return Task.CompletedTask;
        }

        var context = this.MockContext("input:");

        // Act
        var function = SKFunction.FromNativeMethod(Method(TestAsync), log: this._log.Object);
        Assert.NotNull(function);
        SKContext result = await function.InvokeAsync(context);

        // Assert
        Assert.False(result.ErrorOccurred);
        Assert.Equal(s_expected, s_actual);
        Assert.Equal(s_expected, context["canary"]);
        Assert.Equal("input:x y z", context.Result);
    }

    [Fact]
    public async Task ItSupportsStaticVoidTaskAsync()
    {
        // Arrange
        [SKFunction("Test")]
        [SKFunctionName("Test")]
        static Task TestAsync()
        {
            s_actual = s_expected;
            return Task.CompletedTask;
        }

        var context = this.MockContext("");

        // Act
        var function = SKFunction.FromNativeMethod(Method(TestAsync), log: this._log.Object);
        Assert.NotNull(function);
        SKContext result = await function.InvokeAsync(context);

        // Assert
        Assert.False(result.ErrorOccurred);
        Assert.Equal(s_expected, s_actual);
    }

    private static MethodInfo Method(Delegate method)
    {
        return method.Method;
    }

    private SKContext MockContext(string input)
    {
        return new SKContext(
            new ContextVariables(input),
            skills: this._skills.Object,
            logger: this._log.Object);
    }
}
