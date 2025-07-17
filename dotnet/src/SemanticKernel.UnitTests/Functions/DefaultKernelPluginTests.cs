// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.SemanticKernel;
using Xunit;

namespace SemanticKernel.UnitTests.Functions;

/// <summary>
/// Unit tests for <see cref="DefaultKernelPlugin"/> class.
/// </summary>
/// <remarks>
/// These tests cover the TryGetFunction method which has been updated to:
/// 1. First try direct function name lookup in the plugin's function dictionary
/// 2. If not found and the name is long enough, search for AI functions by their Name property
/// 3. Return early if the plugin has no functions (optimization)
///
/// Key behaviors tested:
/// - Direct function name lookup (case-insensitive)
/// - Plugin prefix lookup (e.g., "PluginName_FunctionName")
/// - KernelFunctions inherit from FullyQualifiedAIFunction, so they ARE AIFunctions
/// - The AIFunction.Name property returns "PluginName_FunctionName" when the function has a plugin
/// - Edge cases like empty plugins, null inputs, very long names, etc.
/// </remarks>
public sealed class DefaultKernelPluginTests
{
    [Fact]
    public void TryGetFunctionWithDirectFunctionNameReturnsTrue()
    {
        // Arrange
        var function1 = KernelFunctionFactory.CreateFromMethod(() => "Result1", "TestFunction1");
        var function2 = KernelFunctionFactory.CreateFromMethod(() => "Result2", "TestFunction2");
        var plugin = new DefaultKernelPlugin("TestPlugin", "Test Description", [function1, function2]);

        // Act & Assert
        Assert.True(plugin.TryGetFunction("TestFunction1", out KernelFunction? foundFunction));
        Assert.NotNull(foundFunction);
        Assert.Equal("TestFunction1", foundFunction.Name);
        Assert.Equal("TestPlugin", foundFunction.PluginName);
    }

    [Fact]
    public void TryGetFunctionWithDirectFunctionNameIsCaseInsensitive()
    {
        // Arrange
        var function = KernelFunctionFactory.CreateFromMethod(() => "Result", "TestFunction");
        var plugin = new DefaultKernelPlugin("TestPlugin", "Test Description", [function]);

        // Act & Assert
        Assert.True(plugin.TryGetFunction("testfunction", out KernelFunction? foundFunction));
        Assert.NotNull(foundFunction);
        Assert.Equal("TestFunction", foundFunction.Name);

        Assert.True(plugin.TryGetFunction("TESTFUNCTION", out foundFunction));
        Assert.NotNull(foundFunction);
        Assert.Equal("TestFunction", foundFunction.Name);
    }

    [Fact]
    public void TryGetFunctionWithNonExistentFunctionNameReturnsFalse()
    {
        // Arrange
        var function = KernelFunctionFactory.CreateFromMethod(() => "Result", "TestFunction");
        var plugin = new DefaultKernelPlugin("TestPlugin", "Test Description", [function]);

        // Act & Assert
        Assert.False(plugin.TryGetFunction("NonExistentFunction", out KernelFunction? foundFunction));
        Assert.Null(foundFunction);
    }

    [Fact]
    public void TryGetFunctionWithDirectNameReturnsTrue()
    {
        // Arrange
        var function = KernelFunctionFactory.CreateFromMethod(() => "Result", "TestFunction");
        var plugin = new DefaultKernelPlugin("TestPlugin", "Test Description", [function]);

        // Act & Assert - Direct function name should work
        Assert.True(plugin.TryGetFunction("TestFunction", out KernelFunction? foundFunction));
        Assert.NotNull(foundFunction);
        Assert.Equal("TestFunction", foundFunction.Name);
        Assert.Equal("TestPlugin", foundFunction.PluginName);

        // KernelFunctions ARE AIFunctions (they inherit from FullyQualifiedAIFunction)
        Assert.True(function is Microsoft.Extensions.AI.AIFunction);

        // The new implementation DOES find KernelFunctions by plugin prefix
        // because KernelFunction.Name returns the fully qualified name when it has a plugin
        Assert.True(plugin.TryGetFunction("TestPlugin_TestFunction", out foundFunction));
        Assert.NotNull(foundFunction);
        Assert.Equal("TestFunction", foundFunction.Name);
        Assert.Equal("TestPlugin", foundFunction.PluginName);
    }

    [Fact]
    public void TryGetFunctionWithIncorrectPluginNamePrefixReturnsFalse()
    {
        // Arrange
        var function = KernelFunctionFactory.CreateFromMethod(() => "Result", "TestFunction");
        var plugin = new DefaultKernelPlugin("TestPlugin", "Test Description", [function]);

        // Act & Assert - Function name with wrong plugin name prefix
        Assert.False(plugin.TryGetFunction("WrongPlugin_TestFunction", out KernelFunction? foundFunction));
        Assert.Null(foundFunction);
    }

    [Fact]
    public void TryGetFunctionWithFunctionNameTooShortReturnsFalse()
    {
        // Arrange
        var function = KernelFunctionFactory.CreateFromMethod(() => "Result", "TestFunction");
        var plugin = new DefaultKernelPlugin("VeryLongPluginName", "Test Description", [function]);

        // Act & Assert - Function name shorter than plugin name
        Assert.False(plugin.TryGetFunction("Short", out KernelFunction? foundFunction));
        Assert.Null(foundFunction);
    }

    [Fact]
    public void TryGetFunctionWithFunctionNameEqualToPluginNameLengthReturnsFalse()
    {
        // Arrange
        var function = KernelFunctionFactory.CreateFromMethod(() => "Result", "TestFunction");
        var plugin = new DefaultKernelPlugin("TestPlugin", "Test Description", [function]);

        // Act & Assert - Function name equal to plugin name length (10 characters)
        Assert.False(plugin.TryGetFunction("1234567890", out KernelFunction? foundFunction));
        Assert.Null(foundFunction);
    }

    [Fact]
    public void TryGetFunctionWithPluginNamePrefixButNonExistentFunctionReturnsFalse()
    {
        // Arrange
        var function = KernelFunctionFactory.CreateFromMethod(() => "Result", "TestFunction");
        var plugin = new DefaultKernelPlugin("TestPlugin", "Test Description", [function]);

        // Act & Assert - Correct plugin prefix but function doesn't exist
        Assert.False(plugin.TryGetFunction("TestPlugin_NonExistentFunction", out KernelFunction? foundFunction));
        Assert.Null(foundFunction);
    }

    [Fact]
    public void TryGetFunctionWithCaseInsensitiveNameReturnsTrue()
    {
        // Arrange
        var function = KernelFunctionFactory.CreateFromMethod(() => "Result", "TestFunction");
        var plugin = new DefaultKernelPlugin("TestPlugin", "Test Description", [function]);

        // Act & Assert - Direct function name with different casing should work
        Assert.True(plugin.TryGetFunction("testfunction", out KernelFunction? foundFunction));
        Assert.NotNull(foundFunction);
        Assert.Equal("TestFunction", foundFunction.Name);

        // Plugin prefix with different casing won't work for regular KernelFunctions
        Assert.False(plugin.TryGetFunction("testplugin_testfunction", out foundFunction));
        Assert.Null(foundFunction);
    }

    [Fact]
    public void TryGetFunctionWithEmptyPluginNameThrowsArgumentException()
    {
        // Arrange & Act & Assert - Empty plugin name should throw exception
        Assert.Throws<ArgumentException>(() =>
        {
            var function = KernelFunctionFactory.CreateFromMethod(() => "Result", "TestFunction");
            var plugin = new DefaultKernelPlugin("", "Test Description", [function]);
        });
    }

    [Fact]
    public void TryGetFunctionWithSingleCharacterPluginNameHandlesCorrectly()
    {
        // Arrange
        var function = KernelFunctionFactory.CreateFromMethod(() => "Result", "TestFunction");
        var plugin = new DefaultKernelPlugin("A", "Test Description", [function]);

        // Act & Assert - Direct function name
        Assert.True(plugin.TryGetFunction("TestFunction", out KernelFunction? foundFunction));
        Assert.NotNull(foundFunction);

        // Act & Assert - With plugin prefix
        Assert.True(plugin.TryGetFunction("A_TestFunction", out foundFunction));
        Assert.NotNull(foundFunction);

        // Act & Assert - Function name too short (equal to plugin name length)
        Assert.False(plugin.TryGetFunction("A", out foundFunction));
        Assert.Null(foundFunction);
    }

    [Fact]
    public void TryGetFunctionWithAIFunctionNameReturnsCorrectResults()
    {
        // Arrange
        var function = KernelFunctionFactory.CreateFromMethod(() => "Result", "TestFunction");
        var plugin = new DefaultKernelPlugin("TestPlugin", "Test Description", [function]);

        // Act & Assert - Direct function name should work
        Assert.True(plugin.TryGetFunction("TestFunction", out KernelFunction? foundFunction));
        Assert.NotNull(foundFunction);
        Assert.Equal("TestFunction", foundFunction.Name);

        // The new implementation finds AI functions by their exact Name property
        // KernelFunctions ARE AIFunctions and their Name includes plugin prefix when they have one
        Assert.True(plugin.TryGetFunction("TestPlugin_TestFunction", out foundFunction));
        Assert.NotNull(foundFunction);
        Assert.Equal("TestFunction", foundFunction.Name);

        // Different separators should not work (only underscore is the standard)
        Assert.False(plugin.TryGetFunction("TestPlugin-TestFunction", out foundFunction));
        Assert.Null(foundFunction);

        Assert.False(plugin.TryGetFunction("TestPlugin.TestFunction", out foundFunction));
        Assert.Null(foundFunction);

        Assert.False(plugin.TryGetFunction("TestPlugin:TestFunction", out foundFunction));
        Assert.Null(foundFunction);
    }

    [Fact]
    public void TryGetFunctionWithMultipleUnderscoresInNameHandlesCorrectly()
    {
        // Arrange
        var function = KernelFunctionFactory.CreateFromMethod(() => "Result", "Test_Function_Name");
        var plugin = new DefaultKernelPlugin("TestPlugin", "Test Description", [function]);

        // Act & Assert - Direct function name with underscores
        Assert.True(plugin.TryGetFunction("Test_Function_Name", out KernelFunction? foundFunction));
        Assert.NotNull(foundFunction);
        Assert.Equal("Test_Function_Name", foundFunction.Name);

        // Act & Assert - With plugin prefix
        Assert.True(plugin.TryGetFunction("TestPlugin_Test_Function_Name", out foundFunction));
        Assert.NotNull(foundFunction);
        Assert.Equal("Test_Function_Name", foundFunction.Name);
    }

    [Fact]
    public void TryGetFunctionWithPluginNameContainingUnderscoreHandlesCorrectly()
    {
        // Arrange
        var function = KernelFunctionFactory.CreateFromMethod(() => "Result", "TestFunction");
        var plugin = new DefaultKernelPlugin("Test_Plugin", "Test Description", [function]);

        // Act & Assert - Direct function name
        Assert.True(plugin.TryGetFunction("TestFunction", out KernelFunction? foundFunction));
        Assert.NotNull(foundFunction);

        // Act & Assert - With plugin prefix (plugin name has underscore)
        Assert.True(plugin.TryGetFunction("Test_Plugin_TestFunction", out foundFunction));
        Assert.NotNull(foundFunction);
        Assert.Equal("TestFunction", foundFunction.Name);
    }

    [Fact]
    public void TryGetFunctionWithExactPluginNameAsInputReturnsFalse()
    {
        // Arrange
        var function = KernelFunctionFactory.CreateFromMethod(() => "Result", "TestFunction");
        var plugin = new DefaultKernelPlugin("TestPlugin", "Test Description", [function]);

        // Act & Assert - Exact plugin name should return false (too short)
        Assert.False(plugin.TryGetFunction("TestPlugin", out KernelFunction? foundFunction));
        Assert.Null(foundFunction);
    }

    [Fact]
    public void TryGetFunctionWithPluginNamePlusUnderscoreOnlyReturnsFalse()
    {
        // Arrange
        var function = KernelFunctionFactory.CreateFromMethod(() => "Result", "TestFunction");
        var plugin = new DefaultKernelPlugin("TestPlugin", "Test Description", [function]);

        // Act & Assert - Plugin name + underscore only (no function name part)
        Assert.False(plugin.TryGetFunction("TestPlugin_", out KernelFunction? foundFunction));
        Assert.Null(foundFunction);
    }

    [Fact]
    public void TryGetFunctionWithFunctionNameMatchingPluginNameHandlesCorrectly()
    {
        // Arrange - Function name same as plugin name
        var function = KernelFunctionFactory.CreateFromMethod(() => "Result", "TestPlugin");
        var plugin = new DefaultKernelPlugin("TestPlugin", "Test Description", [function]);

        // Act & Assert - Direct function name (same as plugin name)
        Assert.True(plugin.TryGetFunction("TestPlugin", out KernelFunction? foundFunction));
        Assert.NotNull(foundFunction);
        Assert.Equal("TestPlugin", foundFunction.Name);

        // Act & Assert - With plugin prefix
        Assert.True(plugin.TryGetFunction("TestPlugin_TestPlugin", out foundFunction));
        Assert.NotNull(foundFunction);
        Assert.Equal("TestPlugin", foundFunction.Name);
    }

    [Fact]
    public void TryGetFunctionWithNullFunctionNameThrowsArgumentNullException()
    {
        // Arrange
        var function = KernelFunctionFactory.CreateFromMethod(() => "Result", "TestFunction");
        var plugin = new DefaultKernelPlugin("TestPlugin", "Test Description", [function]);

        // Act & Assert
        Assert.Throws<ArgumentNullException>(() => plugin.TryGetFunction(null!, out _));
    }

    [Fact]
    public void TryGetFunctionWithEmptyFunctionNameReturnsFalse()
    {
        // Arrange
        var function = KernelFunctionFactory.CreateFromMethod(() => "Result", "TestFunction");
        var plugin = new DefaultKernelPlugin("TestPlugin", "Test Description", [function]);

        // Act & Assert
        Assert.False(plugin.TryGetFunction("", out KernelFunction? foundFunction));
        Assert.Null(foundFunction);
    }

    [Fact]
    public void TryGetFunctionWithWhitespaceFunctionNameReturnsFalse()
    {
        // Arrange
        var function = KernelFunctionFactory.CreateFromMethod(() => "Result", "TestFunction");
        var plugin = new DefaultKernelPlugin("TestPlugin", "Test Description", [function]);

        // Act & Assert
        Assert.False(plugin.TryGetFunction("   ", out KernelFunction? foundFunction));
        Assert.Null(foundFunction);
    }

    [Fact]
    public void TryGetFunctionWithWrongPluginPrefixReturnsFalse()
    {
        // Arrange
        var function = KernelFunctionFactory.CreateFromMethod(() => "Result", "TestFunction");
        var plugin = new DefaultKernelPlugin("TestPlugin", "Test Description", [function]);

        // Act & Assert - Try to find function with wrong plugin prefix
        Assert.False(plugin.TryGetFunction("WrongPlugin_TestFunction", out KernelFunction? foundFunction));
        Assert.Null(foundFunction);

        // Act & Assert - Correct plugin prefix should work
        Assert.True(plugin.TryGetFunction("TestPlugin_TestFunction", out foundFunction));
        Assert.NotNull(foundFunction);
        Assert.Equal("TestPlugin", foundFunction.PluginName);

        // Act & Assert - Direct function name should work
        Assert.True(plugin.TryGetFunction("TestFunction", out foundFunction));
        Assert.NotNull(foundFunction);
        Assert.Equal("TestPlugin", foundFunction.PluginName);
    }

    [Fact]
    public void TryGetFunctionWithVeryLongFunctionNameHandlesCorrectly()
    {
        // Arrange
        var longFunctionName = new string('A', 1000); // Very long function name
        var function = KernelFunctionFactory.CreateFromMethod(() => "Result", longFunctionName);
        var plugin = new DefaultKernelPlugin("TestPlugin", "Test Description", [function]);

        // Act & Assert - Direct function name
        Assert.True(plugin.TryGetFunction(longFunctionName, out KernelFunction? foundFunction));
        Assert.NotNull(foundFunction);
        Assert.Equal(longFunctionName, foundFunction.Name);

        // Act & Assert - With plugin prefix
        Assert.True(plugin.TryGetFunction($"TestPlugin_{longFunctionName}", out foundFunction));
        Assert.NotNull(foundFunction);
        Assert.Equal(longFunctionName, foundFunction.Name);
    }

    [Fact]
    public void TryGetFunctionWithSpecialCharactersInFunctionNameThrowsArgumentException()
    {
        // Arrange & Act & Assert - Function names with special characters should throw exception
        Assert.Throws<ArgumentException>(() =>
        {
            var specialFunctionName = "Test-Function.Name@123";
            var function = KernelFunctionFactory.CreateFromMethod(() => "Result", specialFunctionName);
        });
    }

    [Fact]
    public void TryGetFunctionWithEmptyPluginReturnsCorrectResults()
    {
        // Arrange - Plugin with no functions
        var plugin = new DefaultKernelPlugin("TestPlugin", "Test Description", null);

        // Act & Assert - Early exit for empty plugin (new optimization)
        Assert.False(plugin.TryGetFunction("AnyFunction", out KernelFunction? foundFunction));
        Assert.Null(foundFunction);

        Assert.False(plugin.TryGetFunction("TestPlugin_AnyFunction", out foundFunction));
        Assert.Null(foundFunction);
    }

    [Fact]
    public void TryGetFunctionWithMultipleFunctionsFindsCorrectOne()
    {
        // Arrange
        var function1 = KernelFunctionFactory.CreateFromMethod(() => "Result1", "Function1");
        var function2 = KernelFunctionFactory.CreateFromMethod(() => "Result2", "Function2");
        var function3 = KernelFunctionFactory.CreateFromMethod(() => "Result3", "Function3");
        var plugin = new DefaultKernelPlugin("TestPlugin", "Test Description", [function1, function2, function3]);

        // Act & Assert - Find each function by direct name
        Assert.True(plugin.TryGetFunction("Function1", out KernelFunction? foundFunction));
        Assert.Equal("Function1", foundFunction!.Name);

        Assert.True(plugin.TryGetFunction("Function2", out foundFunction));
        Assert.Equal("Function2", foundFunction!.Name);

        Assert.True(plugin.TryGetFunction("Function3", out foundFunction));
        Assert.Equal("Function3", foundFunction!.Name);

        // Act & Assert - Find each function by plugin prefix
        Assert.True(plugin.TryGetFunction("TestPlugin_Function1", out foundFunction));
        Assert.Equal("Function1", foundFunction!.Name);

        Assert.True(plugin.TryGetFunction("TestPlugin_Function2", out foundFunction));
        Assert.Equal("Function2", foundFunction!.Name);

        Assert.True(plugin.TryGetFunction("TestPlugin_Function3", out foundFunction));
        Assert.Equal("Function3", foundFunction!.Name);
    }

    [Fact]
    public void TryGetFunctionWithAIFunctionWithPluginNameFindsCorrectFunction()
    {
        // Arrange - Create an AI function that has a fully qualified name
        var testAIFunction = new TestAIFunction("TestPlugin_TestFunction");
        var aiFunctionKernelFunction = new Microsoft.SemanticKernel.ChatCompletion.AIFunctionKernelFunction(testAIFunction);
        var plugin = new DefaultKernelPlugin("TestPlugin", "Test Description", [aiFunctionKernelFunction]);

        // Act & Assert - The AI function should be found by its fully qualified name
        Assert.True(plugin.TryGetFunction("TestPlugin_TestFunction", out KernelFunction? foundFunction));
        Assert.NotNull(foundFunction);
        Assert.Equal("TestPlugin_TestFunction", foundFunction.Name);
    }

    [Fact]
    public void TryGetFunctionWithEmptyFunctionDictionaryReturnsEarly()
    {
        // Arrange - Plugin with no functions to test early exit optimization
        var plugin = new DefaultKernelPlugin("TestPlugin", "Test Description", []);

        // Act & Assert - Should return false immediately due to empty function count check
        Assert.False(plugin.TryGetFunction("AnyFunction", out KernelFunction? foundFunction));
        Assert.Null(foundFunction);

        Assert.False(plugin.TryGetFunction("TestPlugin_AnyFunction", out foundFunction));
        Assert.Null(foundFunction);
    }

    // Helper class for testing AI functions
    private sealed class TestAIFunction : Microsoft.Extensions.AI.AIFunction
    {
        public TestAIFunction(string name, string description = "")
        {
            this.Name = name;
            this.Description = description;
        }

        public override string Name { get; }

        public override string Description { get; }

        protected override ValueTask<object?> InvokeCoreAsync(Microsoft.Extensions.AI.AIFunctionArguments? arguments = null, CancellationToken cancellationToken = default)
        {
            return ValueTask.FromResult<object?>("Test result");
        }
    }
}
