// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Experimental.Assistants.Extensions;
using Xunit;

namespace SemanticKernel.Experimental.Assistants.UnitTests.Extensions;

[Trait("Category", "Unit Tests")]
[Trait("Feature", "Assistant")]
public sealed class KernelFunctionExtensionTests
{
    private const string ToolName = "Bogus";
    private const string PluginName = "Fake";

    [Fact]
    public static void GetTwoPartName()
    {
        var function = KernelFunctionFactory.CreateFromMethod(() => true, ToolName);

        string qualifiedName = function.GetQualifiedName(PluginName);

        Assert.Equal($"{PluginName}-{ToolName}", qualifiedName);
    }

    [Fact]
    public static void GetToolModelFromFunction()
    {
        const string FunctionDescription = "Bogus description";
        const string RequiredParamName = "required";
        const string OptionalParamName = "optional";

        var requiredParam = new KernelParameterMetadata("required") { IsRequired = true };
        var optionalParam = new KernelParameterMetadata("optional");
        var parameters = new List<KernelParameterMetadata> { requiredParam, optionalParam };
        var function = KernelFunctionFactory.CreateFromMethod(() => true, ToolName, FunctionDescription, parameters);

        var toolModel = function.ToToolModel(PluginName);
        var properties = toolModel.Function?.Parameters.Properties;
        var required = toolModel.Function?.Parameters.Required;

        Assert.Equal("function", toolModel.Type);
        Assert.Equal($"{PluginName}-{ToolName}", toolModel.Function?.Name);
        Assert.Equal(FunctionDescription, toolModel.Function?.Description);
        Assert.Equal(2, properties?.Count);
        Assert.True(properties?.ContainsKey(RequiredParamName));
        Assert.True(properties?.ContainsKey(OptionalParamName));
        Assert.Equal(1, required?.Count ?? 0);
        Assert.True(required?.Contains(RequiredParamName) ?? false);
    }
}
