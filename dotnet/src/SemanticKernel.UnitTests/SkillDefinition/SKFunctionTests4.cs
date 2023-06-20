// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Reflection;
using System.Threading.Tasks;
using Microsoft.Extensions.Logging;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Orchestration;
using Microsoft.SemanticKernel.Security;
using Microsoft.SemanticKernel.SemanticFunctions;
using Microsoft.SemanticKernel.SkillDefinition;
using Moq;
using Xunit;

namespace SemanticKernel.UnitTests.SkillDefinition;

public class SKFunctionTests4
{
    private readonly Mock<ILogger> _log;
    private readonly Mock<IReadOnlySkillCollection> _skills;
    private readonly Mock<IPromptTemplate> _promptTemplate;
    private static string s_expected = string.Empty;
    private static string s_actual = string.Empty;

    public SKFunctionTests4()
    {
        this._promptTemplate = new Mock<IPromptTemplate>();
        this._promptTemplate.Setup(x => x.RenderAsync(It.IsAny<SKContext>())).ReturnsAsync("foo");
        this._promptTemplate.Setup(x => x.GetParameters()).Returns(new List<ParameterView>());

        this._log = new Mock<ILogger>();
        this._skills = new Mock<IReadOnlySkillCollection>();

        s_expected = Guid.NewGuid().ToString("D");
    }

    [Fact]
    public void ItHasDefaultTrustSettings()
    {
        // Arrange
        var templateConfig = new PromptTemplateConfig();
        var functionConfig = new SemanticFunctionConfig(templateConfig, this._promptTemplate.Object);

        // Act
        var skFunction = SKFunction.FromSemanticConfig("sk", "name", functionConfig);

        // Assert
        Assert.False(skFunction.IsSensitive);
        Assert.IsType<TrustService>(skFunction.TrustServiceInstance);
    }

    [Fact]
    public void ItHasDefaultTrustSettings2()
    {
        // Arrange
        static void Test()
        {
        }

        // Act
        var function = SKFunction.FromNativeMethod(Method(Test), log: this._log.Object);

        // Assert
        Assert.NotNull(function);
        Assert.False(function.IsSensitive);
        Assert.IsType<TrustService>(function.TrustServiceInstance);
    }

    [Fact]
    public void ItSetsTrustSettings()
    {
        // Arrange
        [SKFunction(isSensitive: true)]
        static void Test()
        {
        }

        var trustService = new CustomTrustService();

        // Act
        var function = SKFunction.FromNativeMethod(Method(Test), log: this._log.Object, trustService: trustService);

        // Assert
        Assert.NotNull(function);
        Assert.True(function.IsSensitive);
        Assert.IsType<CustomTrustService>(function.TrustServiceInstance);
        Assert.Equal(trustService, function.TrustServiceInstance);
    }

    [Fact]
    public void ItSetsTrustSettings2()
    {
        // Arrange
        var context = Kernel.Builder.Build().CreateNewContext();

        async Task<SKContext> ExecuteAsync(SKContext contextIn)
        {
            await Task.Delay(0);
            return contextIn;
        }

        var trustService = new CustomTrustService();

        // Act
        ISKFunction function = SKFunction.FromNativeFunction(
            nativeFunction: ExecuteAsync,
            parameters: null,
            description: "description",
            skillName: "skillName",
            functionName: "functionName",
            isSensitive: true,
            trustService: trustService);

        // Assert
        Assert.NotNull(function);
        Assert.True(function.IsSensitive);
        Assert.IsType<CustomTrustService>(function.TrustServiceInstance);
        Assert.Equal(trustService, function.TrustServiceInstance);
    }

    [Fact]
    public void ItAllowsFunctionToBeSensitive()
    {
        // Arrange
        var templateConfig = new PromptTemplateConfig { IsSensitive = true };
        var functionConfig = new SemanticFunctionConfig(templateConfig, this._promptTemplate.Object);
        var skFunction = SKFunction.FromSemanticConfig("sk", "name", functionConfig);

        // Assert
        Assert.True(functionConfig.PromptTemplateConfig.IsSensitive);
        Assert.True(skFunction.IsSensitive);
    }

    [Fact]
    public void ItCanSetCustomTrustService()
    {
        // Arrange
        var templateConfig = new PromptTemplateConfig();
        var functionConfig = new SemanticFunctionConfig(templateConfig, this._promptTemplate.Object);
        var trustService = new CustomTrustService();

        // Act
        var skFunction = SKFunction.FromSemanticConfig("sk", "name", functionConfig, trustService: trustService);

        // Assert
        Assert.IsType<CustomTrustService>(skFunction.TrustServiceInstance);
        Assert.Equal(trustService, skFunction.TrustServiceInstance);
    }

    [Fact]
    public void ItCanImportNativeFunctionsWithTrustService()
    {
        // Arrange
        var context = Kernel.Builder.Build().CreateNewContext();

        Task<SKContext> Execute(SKContext contextIn)
        {
            return Task.FromResult(contextIn);
        }

        var trustService = new CustomTrustService();

        // Act
        ISKFunction function = SKFunction.FromNativeFunction(
            nativeFunction: Execute,
            parameters: null,
            description: "description",
            skillName: "skillName",
            functionName: "functionName",
            trustService: trustService);

        // Assert
        Assert.IsType<CustomTrustService>(function.TrustServiceInstance);
        Assert.Equal(trustService, function.TrustServiceInstance);
    }

    [Theory]
    [InlineData(true, true, true)]
    [InlineData(false, true, false)]
    [InlineData(true, false, false)]
    public async Task ItSupportsType1Async(bool isTrusted, bool defaultTrusted, bool expectedTrustResult)
    {
        // Arrange
        static void Test()
        {
            s_actual = s_expected;
        }

        var context = this.MockContext("", isTrusted);

        var trustService = defaultTrusted ? TrustService.DefaultTrusted : TrustService.DefaultUntrusted;

        // Act
        var function = SKFunction.FromNativeMethod(Method(Test), trustService: trustService, log: this._log.Object);
        Assert.NotNull(function);
        SKContext result = await function.InvokeAsync(context);

        // Assert
        Assert.False(result.ErrorOccurred);
        Assert.Equal(s_expected, s_actual);
        Assert.Equal(expectedTrustResult, result.IsTrusted);
    }

    [Theory]
    [InlineData(true, true, true)]
    [InlineData(false, true, false)]
    [InlineData(true, false, false)]
    public async Task ItSupportsType2Async(bool isTrusted, bool defaultTrusted, bool expectedTrustResult)
    {
        // Arrange
        static string Test()
        {
            s_actual = s_expected;
            return s_expected;
        }

        var context = this.MockContext("", isTrusted);

        var trustService = defaultTrusted ? TrustService.DefaultTrusted : TrustService.DefaultUntrusted;

        // Act
        var function = SKFunction.FromNativeMethod(Method(Test), trustService: trustService, log: this._log.Object);
        Assert.NotNull(function);
        SKContext result = await function.InvokeAsync(context);

        // Assert
        Assert.False(result.ErrorOccurred);
        Assert.Equal(s_expected, s_actual);
        Assert.Equal(s_expected, result.Result);
        Assert.Equal(s_expected, context.Result);
        Assert.Equal(expectedTrustResult, result.IsTrusted);
    }

    [Theory]
    [InlineData(true, true, true)]
    [InlineData(false, true, false)]
    [InlineData(true, false, false)]
    public async Task ItSupportsType3Async(bool isTrusted, bool defaultTrusted, bool expectedTrustResult)
    {
        // Arrange
        static Task<string> Test()
        {
            s_actual = s_expected;
            return Task.FromResult(s_expected);
        }

        var context = this.MockContext("", isTrusted);

        var trustService = defaultTrusted ? TrustService.DefaultTrusted : TrustService.DefaultUntrusted;

        // Act
        var function = SKFunction.FromNativeMethod(Method(Test), trustService: trustService, log: this._log.Object);
        Assert.NotNull(function);
        SKContext result = await function.InvokeAsync(context);

        // Assert
        Assert.False(result.ErrorOccurred);
        Assert.Equal(s_expected, s_actual);
        Assert.Equal(s_expected, context.Result);
        Assert.Equal(s_expected, result.Result);
        Assert.Equal(expectedTrustResult, result.IsTrusted);
    }

    [Theory]
    [InlineData(true, true, true)]
    [InlineData(false, true, false)]
    [InlineData(true, false, false)]
    public async Task ItSupportsType4Async(bool isTrusted, bool defaultTrusted, bool expectedTrustResult)
    {
        // Arrange
        static void Test(SKContext cx)
        {
            s_actual = s_expected;
            cx["canary"] = s_expected;
        }

        var context = this.MockContext("xy", isTrusted);
        context["someVar"] = "qz";

        var trustService = defaultTrusted ? TrustService.DefaultTrusted : TrustService.DefaultUntrusted;

        // Act
        var function = SKFunction.FromNativeMethod(Method(Test), trustService: trustService, log: this._log.Object);
        Assert.NotNull(function);
        SKContext result = await function.InvokeAsync(context);

        // Assert
        Assert.False(result.ErrorOccurred);
        Assert.Equal(s_expected, s_actual);
        Assert.Equal(s_expected, context["canary"]);
        Assert.Equal(expectedTrustResult, result.IsTrusted);
    }

    [Fact]
    public async Task ItKeepsContextTrustType4Async()
    {
        // Arrange
        static void Test(SKContext cx)
        {
            s_actual = s_expected;
            // Set this variable as untrusted
            cx.Variables.Update(TrustAwareString.CreateUntrusted(cx.Variables.Input));
            cx["canary"] = s_expected;
        }

        var context = this.MockContext("xy");
        context["someVar"] = "qz";

        var trustService = TrustService.DefaultTrusted;

        // Act
        var function = SKFunction.FromNativeMethod(Method(Test), trustService: trustService, log: this._log.Object);
        Assert.NotNull(function);
        SKContext result = await function.InvokeAsync(context);

        // Assert
        Assert.False(result.ErrorOccurred);
        Assert.Equal(s_expected, s_actual);
        Assert.Equal(s_expected, context["canary"]);
        // This should result in an untrusted output
        Assert.False(result.IsTrusted);
    }

    [Theory]
    [InlineData(true, true, true)]
    [InlineData(false, true, false)]
    [InlineData(true, false, false)]
    public async Task ItSupportsType5Async(bool isTrusted, bool defaultTrusted, bool expectedTrustResult)
    {
        // Arrange
        static string Test(SKContext cx)
        {
            s_actual = cx["someVar"];
            return "abc";
        }

        var context = this.MockContext("", isTrusted);
        context["someVar"] = s_expected;

        var trustService = defaultTrusted ? TrustService.DefaultTrusted : TrustService.DefaultUntrusted;

        // Act
        var function = SKFunction.FromNativeMethod(Method(Test), trustService: trustService, log: this._log.Object);
        Assert.NotNull(function);
        SKContext result = await function.InvokeAsync(context);

        // Assert
        Assert.False(result.ErrorOccurred);
        Assert.Equal(s_expected, s_actual);
        Assert.Equal("abc", context.Result);
        Assert.Equal(expectedTrustResult, result.IsTrusted);
    }

    [Fact]
    public async Task ItKeepsContextTrustType5Async()
    {
        // Arrange
        static string Test(SKContext cx)
        {
            // Set this variable as untrusted
            cx.Variables.Update(TrustAwareString.CreateUntrusted("some value"));
            s_actual = cx["someVar"];
            return "abc";
        }

        var context = this.MockContext("");
        context["someVar"] = s_expected;

        var trustService = TrustService.DefaultTrusted;

        // Act
        var function = SKFunction.FromNativeMethod(Method(Test), trustService: trustService, log: this._log.Object);
        Assert.NotNull(function);
        SKContext result = await function.InvokeAsync(context);

        // Assert
        Assert.False(result.ErrorOccurred);
        Assert.Equal(s_expected, s_actual);
        Assert.Equal("abc", context.Result);
        // This should result in an untrusted output
        Assert.False(result.IsTrusted);
    }

    [Theory]
    [InlineData(true, true, true)]
    [InlineData(false, true, false)]
    [InlineData(true, false, false)]
    public async Task ItSupportsType5NullableAsync(bool isTrusted, bool defaultTrusted, bool expectedTrustResult)
    {
        // Arrange
        string? Test(SKContext cx)
        {
            s_actual = cx["someVar"];
            return "abc";
        }

        var context = this.MockContext("", isTrusted);
        context["someVar"] = s_expected;

        var trustService = defaultTrusted ? TrustService.DefaultTrusted : TrustService.DefaultUntrusted;

        // Act
        var function = SKFunction.FromNativeMethod(Method(Test), trustService: trustService, log: this._log.Object);
        Assert.NotNull(function);
        SKContext result = await function.InvokeAsync(context);

        // Assert
        Assert.False(result.ErrorOccurred);
        Assert.Equal(s_expected, s_actual);
        Assert.Equal("abc", context.Result);
        Assert.Equal(expectedTrustResult, result.IsTrusted);
    }

    [Theory]
    [InlineData(true, true, true)]
    [InlineData(false, true, false)]
    [InlineData(true, false, false)]
    public async Task ItSupportsType6Async(bool isTrusted, bool defaultTrusted, bool expectedTrustResult)
    {
        // Arrange
        Task<string> Test(SKContext cx)
        {
            s_actual = s_expected;
            cx.Variables["canary"] = s_expected;
            return Task.FromResult(s_expected);
        }

        var context = this.MockContext("", isTrusted);

        var trustService = defaultTrusted ? TrustService.DefaultTrusted : TrustService.DefaultUntrusted;

        // Act
        var function = SKFunction.FromNativeMethod(Method(Test), trustService: trustService, log: this._log.Object);
        Assert.NotNull(function);
        SKContext result = await function.InvokeAsync(context);

        // Assert
        Assert.False(result.ErrorOccurred);
        Assert.Equal(s_expected, s_actual);
        Assert.Equal(s_actual, context.Result);
        Assert.Equal(s_expected, context["canary"]);
        Assert.Equal(expectedTrustResult, result.IsTrusted);
    }

    [Fact]
    public async Task ItKeepsContextTrustType6Async()
    {
        // Arrange
        Task<string> Test(SKContext cx)
        {
            // Set this variable as untrusted
            cx.Variables.Update(TrustAwareString.CreateUntrusted(cx.Variables.Input));
            s_actual = s_expected;
            cx.Variables["canary"] = s_expected;
            return Task.FromResult(s_expected);
        }

        var context = this.MockContext("");

        var trustService = TrustService.DefaultTrusted;

        // Act
        var function = SKFunction.FromNativeMethod(Method(Test), trustService: trustService, log: this._log.Object);
        Assert.NotNull(function);
        SKContext result = await function.InvokeAsync(context);

        // Assert
        Assert.False(result.ErrorOccurred);
        Assert.Equal(s_expected, s_actual);
        Assert.Equal(s_actual, context.Result);
        Assert.Equal(s_expected, context["canary"]);
        // This should result in an untrusted output
        Assert.False(result.IsTrusted);
    }

    [Theory]
    [InlineData(true, true, true)]
    [InlineData(false, true, false)]
    [InlineData(true, false, false)]
    public async Task ItSupportsType7Async(bool isTrusted, bool defaultTrusted, bool expectedTrustResult)
    {
        // Arrange
        Task<SKContext> Test(SKContext cx)
        {
            s_actual = s_expected;
            cx.Variables.Update("foo");
            cx["canary"] = s_expected;
            return Task.FromResult(cx);
        }

        var context = this.MockContext("", isTrusted);

        var trustService = defaultTrusted ? TrustService.DefaultTrusted : TrustService.DefaultUntrusted;

        // Act
        var function = SKFunction.FromNativeMethod(Method(Test), trustService: trustService, log: this._log.Object);
        Assert.NotNull(function);
        SKContext result = await function.InvokeAsync(context);

        // Assert
        Assert.False(result.ErrorOccurred);
        Assert.Equal(s_expected, s_actual);
        Assert.Equal(s_expected, context["canary"]);
        Assert.Equal("foo", context.Result);
        Assert.Equal(expectedTrustResult, result.IsTrusted);
    }

    [Fact]
    public async Task ItKeepsContextTrustType7Async()
    {
        // Arrange
        Task<SKContext> Test(SKContext cx)
        {
            s_actual = s_expected;
            // Set this variable as untrusted
            cx.Variables.Update(TrustAwareString.CreateUntrusted("foo"));
            cx["canary"] = s_expected;
            return Task.FromResult(cx);
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
        Assert.Equal("foo", context.Result);
        // This should result in an untrusted output
        Assert.False(result.IsTrusted);
    }

    [Theory]
    [InlineData(true, true, true)]
    [InlineData(false, true, false)]
    [InlineData(true, false, false)]
    public async Task ItSupportsAsyncType7Async(bool isTrusted, bool defaultTrusted, bool expectedTrustResult)
    {
        // Arrange
        async Task<SKContext> TestAsync(SKContext cx)
        {
            await Task.Delay(0);
            s_actual = s_expected;
            cx.Variables.Update("foo");
            cx["canary"] = s_expected;
            return cx;
        }

        var context = this.MockContext("", isTrusted);

        var trustService = defaultTrusted ? TrustService.DefaultTrusted : TrustService.DefaultUntrusted;

        // Act
        var function = SKFunction.FromNativeMethod(Method(TestAsync), trustService: trustService, log: this._log.Object);
        Assert.NotNull(function);
        SKContext result = await function.InvokeAsync(context);

        // Assert
        Assert.False(result.ErrorOccurred);
        Assert.Equal(s_expected, s_actual);
        Assert.Equal(s_expected, context["canary"]);
        Assert.Equal("foo", context.Result);
        Assert.Equal(expectedTrustResult, result.IsTrusted);
    }

    [Theory]
    [InlineData(true, true, true)]
    [InlineData(false, true, false)]
    [InlineData(true, false, false)]
    public async Task ItSupportsType8Async(bool isTrusted, bool defaultTrusted, bool expectedTrustResult)
    {
        // Arrange
        void Test(string input)
        {
            s_actual = s_expected + input;
        }

        var context = this.MockContext(".blah", isTrusted);

        var trustService = defaultTrusted ? TrustService.DefaultTrusted : TrustService.DefaultUntrusted;

        // Act
        var function = SKFunction.FromNativeMethod(Method(Test), trustService: trustService, log: this._log.Object);
        Assert.NotNull(function);
        SKContext result = await function.InvokeAsync(context);

        // Assert
        Assert.False(result.ErrorOccurred);
        Assert.Equal(s_expected + ".blah", s_actual);
        Assert.Equal(expectedTrustResult, result.IsTrusted);
    }

    [Theory]
    [InlineData(true, true, true)]
    [InlineData(false, true, false)]
    [InlineData(true, false, false)]
    public async Task ItSupportsType9Async(bool isTrusted, bool defaultTrusted, bool expectedTrustResult)
    {
        // Arrange
        string Test(string input)
        {
            s_actual = s_expected;
            return "foo-bar";
        }

        var context = this.MockContext("", isTrusted);

        var trustService = defaultTrusted ? TrustService.DefaultTrusted : TrustService.DefaultUntrusted;

        // Act
        var function = SKFunction.FromNativeMethod(Method(Test), trustService: trustService, log: this._log.Object);
        Assert.NotNull(function);
        SKContext result = await function.InvokeAsync(context);

        // Assert
        Assert.False(result.ErrorOccurred);
        Assert.Equal(s_expected, s_actual);
        Assert.Equal("foo-bar", context.Result);
        Assert.Equal(expectedTrustResult, result.IsTrusted);
    }

    [Theory]
    [InlineData(true, true, true)]
    [InlineData(false, true, false)]
    [InlineData(true, false, false)]
    public async Task ItSupportsType10Async(bool isTrusted, bool defaultTrusted, bool expectedTrustResult)
    {
        // Arrange
        Task<string> Test(string input)
        {
            s_actual = s_expected;
            return Task.FromResult("hello there");
        }

        var context = this.MockContext("", isTrusted);

        var trustService = defaultTrusted ? TrustService.DefaultTrusted : TrustService.DefaultUntrusted;

        // Act
        var function = SKFunction.FromNativeMethod(Method(Test), trustService: trustService, log: this._log.Object);
        Assert.NotNull(function);
        SKContext result = await function.InvokeAsync(context);

        // Assert
        Assert.False(result.ErrorOccurred);
        Assert.Equal(s_expected, s_actual);
        Assert.Equal("hello there", context.Result);
        Assert.Equal(expectedTrustResult, result.IsTrusted);
    }

    [Theory]
    [InlineData(true, true, true)]
    [InlineData(false, true, false)]
    [InlineData(true, false, false)]
    public async Task ItSupportsType11Async(bool isTrusted, bool defaultTrusted, bool expectedTrustResult)
    {
        // Arrange
        void Test(string input, SKContext cx)
        {
            s_actual = s_expected;
            cx.Variables.Update("x y z");
            cx["canary"] = s_expected;
        }

        var context = this.MockContext("", isTrusted);

        var trustService = defaultTrusted ? TrustService.DefaultTrusted : TrustService.DefaultUntrusted;

        // Act
        var function = SKFunction.FromNativeMethod(Method(Test), trustService: trustService, log: this._log.Object);
        Assert.NotNull(function);
        SKContext result = await function.InvokeAsync(context);

        // Assert
        Assert.False(result.ErrorOccurred);
        Assert.Equal(s_expected, s_actual);
        Assert.Equal(s_expected, context["canary"]);
        Assert.Equal("x y z", context.Result);
        Assert.Equal(expectedTrustResult, result.IsTrusted);
    }

    [Fact]
    public async Task ItKeepsContextTrustType11Async()
    {
        // Arrange
        void Test(string input, SKContext cx)
        {
            s_actual = s_expected;
            cx.Variables.Update("x y z");
            cx["canary"] = s_expected;
            // Make all variables untrusted
            cx.UntrustAll();
        }

        var context = this.MockContext("");

        var trustService = TrustService.DefaultTrusted;

        // Act
        var function = SKFunction.FromNativeMethod(Method(Test), trustService: trustService, log: this._log.Object);
        Assert.NotNull(function);
        SKContext result = await function.InvokeAsync(context);

        // Assert
        Assert.False(result.ErrorOccurred);
        Assert.Equal(s_expected, s_actual);
        Assert.Equal(s_expected, context["canary"]);
        Assert.Equal("x y z", context.Result);
        // This should result in an untrusted output
        Assert.False(result.IsTrusted);
    }

    [Theory]
    [InlineData(true, true, true)]
    [InlineData(false, true, false)]
    [InlineData(true, false, false)]
    public async Task ItSupportsType12Async(bool isTrusted, bool defaultTrusted, bool expectedTrustResult)
    {
        // Arrange
        static string Test(string input, SKContext cx)
        {
            s_actual = s_expected;
            cx["canary"] = s_expected;
            cx.Variables.Update("x y z");
            // This value should overwrite "x y z"
            return "new data";
        }

        var context = this.MockContext("", isTrusted);

        var trustService = defaultTrusted ? TrustService.DefaultTrusted : TrustService.DefaultUntrusted;

        // Act
        var function = SKFunction.FromNativeMethod(Method(Test), trustService: trustService, log: this._log.Object);
        Assert.NotNull(function);
        SKContext result = await function.InvokeAsync(context);

        // Assert
        Assert.False(result.ErrorOccurred);
        Assert.Equal(s_expected, s_actual);
        Assert.Equal(s_expected, context["canary"]);
        Assert.Equal("new data", context.Result);
        Assert.Equal(expectedTrustResult, result.IsTrusted);
    }

    [Fact]
    public async Task ItKeepsContextTrustType12Async()
    {
        // Arrange
        static string Test(string input, SKContext cx)
        {
            s_actual = s_expected;
            cx["canary"] = s_expected;
            // Set this variable as untrusted
            cx.Variables.Update(TrustAwareString.CreateUntrusted("x y z"));

            // This value should overwrite "x y z"
            return "new data";
        }

        var context = this.MockContext("");

        var trustService = TrustService.DefaultTrusted;

        // Act
        var function = SKFunction.FromNativeMethod(Method(Test), trustService: trustService, log: this._log.Object);
        Assert.NotNull(function);
        SKContext result = await function.InvokeAsync(context);

        // Assert
        Assert.False(result.ErrorOccurred);
        Assert.Equal(s_expected, s_actual);
        Assert.Equal(s_expected, context["canary"]);
        Assert.Equal("new data", context.Result);
        // This should result in an untrusted output
        Assert.False(result.IsTrusted);
    }

    [Theory]
    [InlineData(true, true, true)]
    [InlineData(false, true, false)]
    [InlineData(true, false, false)]
    public async Task ItSupportsType13Async(bool isTrusted, bool defaultTrusted, bool expectedTrustResult)
    {
        // Arrange
        static Task<string> Test(string input, SKContext cx)
        {
            s_actual = s_expected;
            cx["canary"] = s_expected;
            cx.Variables.Update("x y z");
            // This value should overwrite "x y z"
            return Task.FromResult("new data");
        }

        var context = this.MockContext("", isTrusted);

        var trustService = defaultTrusted ? TrustService.DefaultTrusted : TrustService.DefaultUntrusted;

        // Act
        var function = SKFunction.FromNativeMethod(Method(Test), trustService: trustService, log: this._log.Object);
        Assert.NotNull(function);
        SKContext result = await function.InvokeAsync(context);

        // Assert
        Assert.False(result.ErrorOccurred);
        Assert.Equal(s_expected, s_actual);
        Assert.Equal(s_expected, context["canary"]);
        Assert.Equal("new data", context.Result);
        Assert.Equal(expectedTrustResult, result.IsTrusted);
    }

    [Fact]
    public async Task ItKeepsContextTrustType13Async()
    {
        // Arrange
        static Task<string> Test(string input, SKContext cx)
        {
            s_actual = s_expected;
            cx["canary"] = s_expected;
            // Set this variable as untrusted
            cx.Variables.Update(TrustAwareString.CreateUntrusted("x y z"));
            // This value should overwrite "x y z"
            return Task.FromResult("new data");
        }

        var context = this.MockContext("");

        var trustService = TrustService.DefaultTrusted;

        // Act
        var function = SKFunction.FromNativeMethod(Method(Test), trustService: trustService, log: this._log.Object);
        Assert.NotNull(function);
        SKContext result = await function.InvokeAsync(context);

        // Assert
        Assert.False(result.ErrorOccurred);
        Assert.Equal(s_expected, s_actual);
        Assert.Equal(s_expected, context["canary"]);
        Assert.Equal("new data", context.Result);
        // This should result in an untrusted output
        Assert.False(result.IsTrusted);
    }

    [Theory]
    [InlineData(true, true, true)]
    [InlineData(false, true, false)]
    [InlineData(true, false, false)]
    public async Task ItSupportsType14Async(bool isTrusted, bool defaultTrusted, bool expectedTrustResult)
    {
        // Arrange
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

        var oldContext = this.MockContext("", isTrusted);
        oldContext["legacy"] = "something";

        var trustService = defaultTrusted ? TrustService.DefaultTrusted : TrustService.DefaultUntrusted;

        // Act
        var function = SKFunction.FromNativeMethod(Method(Test), trustService: trustService, log: this._log.Object);
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
        Assert.Equal(expectedTrustResult, newContext.IsTrusted);
    }

    [Fact]
    public async Task ItKeepsContextTrustType14Async()
    {
        // Arrange
        static Task<SKContext> Test(string input, SKContext cx)
        {
            s_actual = s_expected;
            cx["canary"] = s_expected;
            cx.Variables.Update("x y z");

            // This value should overwrite "x y z". Contexts are merged.
            var newCx = new SKContext(
                new ContextVariables(input),
                skills: new Mock<IReadOnlySkillCollection>().Object);

            // Setting the trust of the input to be false
            newCx.Variables.Update(TrustAwareString.CreateUntrusted("new data"));
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
        // Check if the trust of the input is still false
        Assert.False(newContext.IsTrusted);
    }

    [Theory]
    [InlineData(true, true, true)]
    [InlineData(false, true, false)]
    [InlineData(true, false, false)]
    public async Task ItSupportsType15Async(bool isTrusted, bool defaultTrusted, bool expectedTrustResult)
    {
        // Arrange
        static Task TestAsync(string input)
        {
            s_actual = s_expected;
            return Task.CompletedTask;
        }

        var context = this.MockContext("", isTrusted);

        var trustService = defaultTrusted ? TrustService.DefaultTrusted : TrustService.DefaultUntrusted;

        // Act
        var function = SKFunction.FromNativeMethod(Method(TestAsync), trustService: trustService, log: this._log.Object);
        Assert.NotNull(function);
        SKContext result = await function.InvokeAsync(context);

        // Assert
        Assert.False(result.ErrorOccurred);
        Assert.Equal(s_expected, s_actual);
        Assert.Equal(expectedTrustResult, result.IsTrusted);
    }

    [Theory]
    [InlineData(true, true, true)]
    [InlineData(false, true, false)]
    [InlineData(true, false, false)]
    public async Task ItSupportsType16Async(bool isTrusted, bool defaultTrusted, bool expectedTrustResult)
    {
        // Arrange
        static Task TestAsync(SKContext cx)
        {
            s_actual = s_expected;
            cx["canary"] = s_expected;
            cx.Variables.Update("x y z");
            return Task.CompletedTask;
        }

        var context = this.MockContext("", isTrusted);

        var trustService = defaultTrusted ? TrustService.DefaultTrusted : TrustService.DefaultUntrusted;

        // Act
        var function = SKFunction.FromNativeMethod(Method(TestAsync), trustService: trustService, log: this._log.Object);
        Assert.NotNull(function);
        SKContext result = await function.InvokeAsync(context);

        // Assert
        Assert.False(result.ErrorOccurred);
        Assert.Equal(s_expected, s_actual);
        Assert.Equal(s_expected, context["canary"]);
        Assert.Equal("x y z", context.Result);
        Assert.Equal(expectedTrustResult, result.IsTrusted);
    }

    [Fact]
    public async Task ItKeepsContextTrustType16Async()
    {
        // Arrange
        static Task Test(SKContext cx)
        {
            s_actual = s_expected;
            cx["canary"] = s_expected;
            // Set this variable as untrusted
            cx.Variables.Update(TrustAwareString.CreateUntrusted("x y z"));
            return Task.CompletedTask;
        }

        var context = this.MockContext("");

        var trustService = TrustService.DefaultTrusted;

        // Act
        var function = SKFunction.FromNativeMethod(Method(Test), trustService: trustService, log: this._log.Object);
        Assert.NotNull(function);
        SKContext result = await function.InvokeAsync(context);

        // Assert
        Assert.False(result.ErrorOccurred);
        Assert.Equal(s_expected, s_actual);
        Assert.Equal(s_expected, context["canary"]);
        Assert.Equal("x y z", context.Result);
        // This should result in an untrusted output
        Assert.False(result.IsTrusted);
    }

    [Theory]
    [InlineData(true, true, true)]
    [InlineData(false, true, false)]
    [InlineData(true, false, false)]
    public async Task ItSupportsType17Async(bool isTrusted, bool defaultTrusted, bool expectedTrustResult)
    {
        // Arrange
        static Task TestAsync(string input, SKContext cx)
        {
            s_actual = s_expected;
            cx["canary"] = s_expected;
            cx.Variables.Update(input + "x y z");
            return Task.CompletedTask;
        }

        var context = this.MockContext("input:", isTrusted);

        var trustService = defaultTrusted ? TrustService.DefaultTrusted : TrustService.DefaultUntrusted;

        // Act
        var function = SKFunction.FromNativeMethod(Method(TestAsync), trustService: trustService, log: this._log.Object);
        Assert.NotNull(function);
        SKContext result = await function.InvokeAsync(context);

        // Assert
        Assert.False(result.ErrorOccurred);
        Assert.Equal(s_expected, s_actual);
        Assert.Equal(s_expected, context["canary"]);
        Assert.Equal("input:x y z", context.Result);
        Assert.Equal(expectedTrustResult, result.IsTrusted);
    }

    [Fact]
    public async Task ItKeepsContextTrustType17Async()
    {
        // Arrange
        static Task Test(string input, SKContext cx)
        {
            s_actual = s_expected;
            cx["canary"] = s_expected;
            // Set this variable as untrusted
            cx.Variables.Update(TrustAwareString.CreateUntrusted(input + "x y z"));
            return Task.CompletedTask;
        }

        var context = this.MockContext("input:");

        var trustService = TrustService.DefaultTrusted;

        // Act
        var function = SKFunction.FromNativeMethod(Method(Test), trustService: trustService, log: this._log.Object);
        Assert.NotNull(function);
        SKContext result = await function.InvokeAsync(context);

        // Assert
        Assert.False(result.ErrorOccurred);
        Assert.Equal(s_expected, s_actual);
        Assert.Equal(s_expected, context["canary"]);
        Assert.Equal("input:x y z", context.Result);
        // This should result in an untrusted output
        Assert.False(result.IsTrusted);
    }

    [Theory]
    [InlineData(true, true, true)]
    [InlineData(false, true, false)]
    [InlineData(true, false, false)]
    public async Task ItSupportsType18Async(bool isTrusted, bool defaultTrusted, bool expectedTrustResult)
    {
        // Arrange
        static Task TestAsync()
        {
            s_actual = s_expected;
            return Task.CompletedTask;
        }

        var context = this.MockContext("", isTrusted);

        var trustService = defaultTrusted ? TrustService.DefaultTrusted : TrustService.DefaultUntrusted;

        // Act
        var function = SKFunction.FromNativeMethod(Method(TestAsync), trustService: trustService, log: this._log.Object);
        Assert.NotNull(function);
        SKContext result = await function.InvokeAsync(context);

        // Assert
        Assert.False(result.ErrorOccurred);
        Assert.Equal(s_expected, s_actual);
        Assert.Equal(expectedTrustResult, result.IsTrusted);
    }

    private static MethodInfo Method(Delegate method)
    {
        return method.Method;
    }

    private SKContext MockContext(string input, bool isTrusted = true)
    {
        return new SKContext(
            new ContextVariables(new TrustAwareString(input, isTrusted)),
            skills: this._skills.Object,
            logger: this._log.Object);
    }

    private sealed class CustomTrustService : ITrustService
    {
        public Task<bool> ValidateContextAsync(ISKFunction func, SKContext context)
        {
            return Task.FromResult(context.IsTrusted);
        }

        public Task<TrustAwareString> ValidatePromptAsync(ISKFunction func, SKContext context, string prompt)
        {
            return Task.FromResult(new TrustAwareString(prompt, context.IsTrusted));
        }
    }
}
