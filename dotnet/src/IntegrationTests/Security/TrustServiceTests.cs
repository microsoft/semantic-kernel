// Copyright (c) Microsoft. All rights reserved.

using Microsoft.Extensions.Configuration;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Orchestration;
using Microsoft.SemanticKernel.Security;
using Microsoft.SemanticKernel.SkillDefinition;
using SemanticKernel.IntegrationTests.TestSettings;
using Xunit;
using Xunit.Abstractions;

namespace SemanticKernel.IntegrationTests.Security;

public sealed class TrustServiceTests
{
    public TrustServiceTests(ITestOutputHelper output)
    {
        this._configuration = new ConfigurationBuilder()
            .AddJsonFile(path: "testsettings.json", optional: false, reloadOnChange: true)
            .AddJsonFile(path: "testsettings.development.json", optional: true, reloadOnChange: true)
            .AddEnvironmentVariables()
            .AddUserSecrets<TrustServiceTests>()
            .Build();
    }

    [Fact]
    public async void FlowWithUntrustedContentAndNotSensitiveSemanticFunctionShouldSucceed()
    {
        // Arrange
        var valueToEcho = "Hello AI :)";
        var kernel = this.InitializeKernel();

        var defaultUntrustedEchoFunction = this.CreateSemanticEchoFunction(
            kernel,
            functionName: "DefaultUntrustedEchoFunction",
            isSensitive: false,
            trustService: TrustService.DefaultUntrusted
        );
        var defaultTrustedEchoFunction = this.CreateSemanticEchoFunction(
            kernel,
            functionName: "DefaultTrustedEchoFunction",
            isSensitive: false,
            trustService: TrustService.DefaultTrusted
        );

        // Act
        var result = await kernel.RunAsync(valueToEcho, defaultUntrustedEchoFunction, defaultTrustedEchoFunction);

        // Assert
        Assert.Equal(valueToEcho, result.Result);
        Assert.False(result.IsTrusted);
    }

    [Fact]
    public async void FlowWithUntrustedContentAndSensitiveSemanticFunctionShouldThrow()
    {
        // Arrange
        var valueToEcho = "Hello AI :)";

        var kernel = this.InitializeKernel();

        var notSensitiveEchoFunction = this.CreateSemanticEchoFunction(
            kernel,
            functionName: "NotSensitiveEchoFunction",
            isSensitive: false,
            trustService: TrustService.DefaultUntrusted
        );
        var sensitiveEchoFunction = this.CreateSemanticEchoFunction(
            kernel,
            functionName: "SensitiveEchoFunction",
            isSensitive: true,
            trustService: TrustService.DefaultTrusted
        );

        // Act
        var result = await kernel.RunAsync(valueToEcho, notSensitiveEchoFunction, sensitiveEchoFunction);

        // Assert
        this.AssertResultHasThrown(result);
    }

    [Fact]
    public async void FlowWithUntrustedContentAndNotSensitiveNativeFunctionShouldSucceed()
    {
        // Arrange
        var valueToEcho = "Hello AI :)";
        var kernel = this.InitializeKernel();

        var defaultUntrustedEchoFunction = this.CreateNativeEchoFunction(
            kernel,
            isSensitive: false,
            trustService: TrustService.DefaultUntrusted
        );
        var defaultTrustedEchoFunction = this.CreateNativeEchoFunction(
            kernel,
            isSensitive: false,
            trustService: TrustService.DefaultTrusted
        );

        // Act
        var result = await kernel.RunAsync(valueToEcho, defaultUntrustedEchoFunction, defaultTrustedEchoFunction);

        // Assert
        Assert.Equal(valueToEcho, result.Result);
        Assert.False(result.IsTrusted);
    }

    [Fact]
    public async void FlowWithUntrustedContentAndSensitiveNativeFunctionShouldThrow()
    {
        // Arrange
        var valueToEcho = "Hello AI :)";
        var kernel = this.InitializeKernel();

        var notSensitiveEchoFunction = this.CreateNativeEchoFunction(
            kernel,
            isSensitive: false,
            trustService: TrustService.DefaultUntrusted
        );
        var sensitiveEchoFunction = this.CreateNativeEchoFunction(
            kernel,
            isSensitive: true,
            trustService: TrustService.DefaultTrusted
        );

        // Act
        var result = await kernel.RunAsync(valueToEcho, notSensitiveEchoFunction, sensitiveEchoFunction);

        // Assert
        this.AssertResultHasThrown(result);
    }

    [Fact]
    public async void UntrustedVariableAndNotSensitiveSemanticFunctionShouldSucceed()
    {
        // Arrange
        var valueToEcho = "Hello AI, ";
        var extraVar = "welcome!";
        var variables = new ContextVariables(valueToEcho);
        var kernel = this.InitializeKernel();

        var notSensitiveEchoFunction = this.CreateSemanticEchoFunction(
            kernel,
            functionName: "NotSensitiveEchoFunction",
            isSensitive: false,
            trustService: null // Use defaults
        );

        // Make this untrusted
        variables.Set(TrustServiceTests.ExtraVarName, TrustAwareString.CreateUntrusted(extraVar));

        // Act
        var result = await kernel.RunAsync(variables, "fake-model", notSensitiveEchoFunction);

        // Assert
        Assert.Equal(valueToEcho + extraVar, result.Result);
        Assert.False(result.IsTrusted);
    }

    [Fact]
    public async void UntrustedVariableAndSensitiveSemanticFunctionShouldThrow()
    {
        // Arrange
        var valueToEcho = "Hello AI, ";
        var extraVar = "welcome!";
        var variables = new ContextVariables(valueToEcho);
        var kernel = this.InitializeKernel();

        var sensitiveEchoFunction = this.CreateSemanticEchoFunction(
            kernel,
            functionName: "SensitiveEchoFunction",
            isSensitive: true,
            trustService: null // Use defaults
        );

        // Make this untrusted
        variables.Set(TrustServiceTests.ExtraVarName, TrustAwareString.CreateUntrusted(extraVar));

        // Act
        var result = await kernel.RunAsync(variables, "fake-model", sensitiveEchoFunction);

        // Assert
        this.AssertResultHasThrown(result);
    }

    [Fact]
    public async void UntrustedVariableAndNotSensitiveNativeFunctionShouldSucceed()
    {
        // Arrange
        var valueToEcho = "Hello AI, ";
        var extraVar = "welcome!";
        var variables = new ContextVariables(valueToEcho);
        var kernel = this.InitializeKernel();

        var notSensitiveEchoFunction = this.CreateNativeEchoFunction(
            kernel,
            isSensitive: false,
            trustService: null // Use defaults
        );

        // Make this untrusted
        variables.Set(TrustServiceTests.ExtraVarName, TrustAwareString.CreateUntrusted(extraVar));

        // Act
        var result = await kernel.RunAsync(variables, "fake-model", notSensitiveEchoFunction);

        // Assert
        Assert.Equal(valueToEcho + extraVar, result.Result);
        Assert.False(result.IsTrusted);
    }

    [Fact]
    public async void UntrustedVariableAndSensitiveNativeFunctionShouldThrow()
    {
        // Arrange
        var valueToEcho = "Hello AI, ";
        var extraVar = "welcome!";
        var variables = new ContextVariables(valueToEcho);
        var kernel = this.InitializeKernel();

        var sensitiveEchoFunction = this.CreateNativeEchoFunction(
            kernel,
            isSensitive: true,
            trustService: null // Use defaults
        );

        // Make this untrusted
        variables.Set(TrustServiceTests.ExtraVarName, TrustAwareString.CreateUntrusted(extraVar));

        // Act
        var result = await kernel.RunAsync(variables, "fake-model", sensitiveEchoFunction);

        // Assert
        this.AssertResultHasThrown(result);
    }

    [Fact]
    public async void NotSensitiveFunctionWithTrustedFunctionCallShouldSucceed()
    {
        // Arrange
        var valueToEcho = "Hello AI :)";
        var kernel = this.InitializeKernel();

        this.CreateNativeEchoFunction(
            kernel,
            isSensitive: true,
            trustService: TrustService.DefaultTrusted
        );

        var sensitiveEchoWithFunctionCallFunction = this.CreateSemanticEchoWithFunctionCallFunction(
            kernel,
            functionName: "SensitiveEchoWithFunctionCallFunction",
            isSensitive: true,
            trustService: null // Use defaults
        );

        // Act
        var result = await kernel.RunAsync("fake-model", valueToEcho, sensitiveEchoWithFunctionCallFunction);

        // Assert
        Assert.Equal(valueToEcho, result.Result);
        Assert.True(result.IsTrusted);
    }

    [Fact]
    public async void SensitiveFunctionWithUntrustedFunctionCallShouldThrow()
    {
        // Arrange
        var valueToEcho = "Hello AI :)";
        var kernel = this.InitializeKernel();

        this.CreateNativeEchoFunction(
            kernel,
            isSensitive: true,
            trustService: TrustService.DefaultUntrusted // Forces output to be untrusted
        );

        var sensitiveEchoWithFunctionCallFunction = this.CreateSemanticEchoWithFunctionCallFunction(
            kernel,
            functionName: "SensitiveEchoWithFunctionCallFunction",
            isSensitive: true,
            trustService: null // Use defaults
        );

        // Act
        var result = await kernel.RunAsync("fake-model", valueToEcho, sensitiveEchoWithFunctionCallFunction);

        // Assert
        this.AssertResultHasThrown(result);
    }

    private IKernel InitializeKernel()
    {
        AzureOpenAIConfiguration? azureOpenAIConfiguration = this._configuration.GetSection("AzureOpenAI").Get<AzureOpenAIConfiguration>();
        Assert.NotNull(azureOpenAIConfiguration);

        var builder = Kernel.Builder
            .WithAzureTextCompletionService(
                deploymentName: azureOpenAIConfiguration.DeploymentName,
                endpoint: azureOpenAIConfiguration.Endpoint,
                apiKey: azureOpenAIConfiguration.ApiKey,
                serviceId: azureOpenAIConfiguration.ServiceId,
                setAsDefault: true
            );

        return builder.Build();
    }

    private ISKFunction CreateSemanticEchoFunction(
        IKernel kernel,
        string functionName,
        bool isSensitive,
        ITrustService? trustService)
    {
        string promptTemplate = TrustServiceTests.SemanticEchoPrompt.Replace(
            TrustServiceTests.WhatToEcho,
            $"{{{{$input}}}}{{{{${TrustServiceTests.ExtraVarName}}}}}",
            System.StringComparison.Ordinal
        );

        return kernel.CreateSemanticFunction(
            promptTemplate: promptTemplate,
            functionName: functionName,
            skillName: "CustomSkill",
            isSensitive: isSensitive,
            trustService: trustService
        );
    }

    private ISKFunction CreateSemanticEchoWithFunctionCallFunction(
        IKernel kernel,
        string functionName,
        bool isSensitive,
        ITrustService? trustService)
    {
        string promptTemplate = TrustServiceTests.SemanticEchoPrompt.Replace(
            TrustServiceTests.WhatToEcho,
            $"{{{{{nameof(EchoSkill)}.{nameof(EchoSkill.NotSensitiveEcho)} $input}}}}",
            System.StringComparison.Ordinal
        );

        return kernel.CreateSemanticFunction(
            promptTemplate: promptTemplate,
            functionName: functionName,
            skillName: "CustomSkill",
            isSensitive: isSensitive,
            trustService: trustService
        );
    }

    private ISKFunction CreateNativeEchoFunction(
        IKernel kernel,
        bool isSensitive,
        ITrustService? trustService)
    {
        var skill = kernel.ImportSkill(
            new EchoSkill(),
            nameof(EchoSkill),
            trustService: trustService
        );

        return isSensitive ?
            skill[nameof(EchoSkill.SensitiveEcho)] :
            skill[nameof(EchoSkill.NotSensitiveEcho)];
    }

    private void AssertResultHasThrown(SKContext result)
    {
        Assert.True(result.ErrorOccurred);
        Assert.IsType<UntrustedContentException>(result.LastException);
        Assert.Equal(
            UntrustedContentException.ErrorCodes.SensitiveFunctionWithUntrustedContent,
            ((UntrustedContentException)result.LastException).ErrorCode
        );
    }

    private readonly IConfigurationRoot _configuration;

    private sealed class EchoSkill
    {
        [SKFunction("Echoes a given text", isSensitive: false)]
        public string NotSensitiveEcho(SKContext context)
        {
            context.Variables.TryGetValue("extraVar", out string? extraVar);

            return context.Variables.Input + extraVar;
        }

        [SKFunction("Echoes a given text", isSensitive: true)]
        public string SensitiveEcho(SKContext context)
        {
            context.Variables.TryGetValue("extraVar", out string? extraVar);

            return context.Variables.Input + extraVar;
        }
    }

    private const string WhatToEcho = "[WHAT_TO_ECHO]";

    private const string ExtraVarName = "extraVar";

    private const string SemanticEchoPrompt = @$"Your goal is just to echo whatever input is given to you.

[EXAMPLES]
INPUT
-------------------
Hello, how are you?

RESULT
-------------------
Hello, how are you?

INPUT
-------------------
Hi!
            
RESULT
-------------------
Hi!
[END EXAMPLES]

INPUT
-------------------
{TrustServiceTests.WhatToEcho}

RESULT
-------------------
";
}
