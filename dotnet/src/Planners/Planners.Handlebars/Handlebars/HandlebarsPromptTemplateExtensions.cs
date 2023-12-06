// Copyright (c) Microsoft. All rights reserved.

using HandlebarsDotNet;

namespace Microsoft.SemanticKernel.Planning.Handlebars;

/// <summary>
/// Provides extension methods for rendering Handlebars templates in the context of a Semantic Kernel.
/// </summary>
internal sealed class HandlebarsPromptTemplateExtensions
{
    public static void RegisterCustomCreatePlanHelpers(
        IHandlebars handlebarsInstance,
        KernelArguments executionContext
    )
    {
        handlebarsInstance.RegisterHelper("getSchemaTypeName", (in HelperOptions options, in Context context, in Arguments arguments) =>
        {
            KernelParameterMetadata parameter = (KernelParameterMetadata)arguments[0];
            return parameter.GetSchemaTypeName();
        });

        handlebarsInstance.RegisterHelper("getSchemaReturnTypeName", (in HelperOptions options, in Context context, in Arguments arguments) =>
        {
            KernelReturnParameterMetadata parameter = (KernelReturnParameterMetadata)arguments[0];
            var functionName = arguments[1].ToString();
            return parameter.ToSKParameterMetadata(functionName).GetSchemaTypeName();
        });
    }
}
