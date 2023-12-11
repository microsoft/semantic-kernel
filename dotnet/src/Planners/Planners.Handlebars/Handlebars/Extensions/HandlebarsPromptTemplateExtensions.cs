// Copyright (c) Microsoft. All rights reserved.

using HandlebarsDotNet;
using Microsoft.SemanticKernel.PromptTemplate.Handlebars;
using static Microsoft.SemanticKernel.PromptTemplate.Handlebars.HandlebarsPromptTemplateOptions;

namespace Microsoft.SemanticKernel.Planning.Handlebars;

/// <summary>
/// Provides extension methods for rendering Handlebars templates in the context of a Semantic Kernel.
/// </summary>
internal sealed class HandlebarsPromptTemplateExtensions
{
    public static void RegisterCustomCreatePlanHelpers(
        RegisterHelperSafeCallback registerHelperSafe,
        HandlebarsPromptTemplateOptions options,
        KernelArguments executionContext
    )
    {
        registerHelperSafe("getSchemaTypeName", (Context context, Arguments arguments) =>
        {
            KernelParameterMetadata parameter = (KernelParameterMetadata)arguments[0];
            return parameter.GetSchemaTypeName();
        });

        registerHelperSafe("getSchemaReturnTypeName", (Context context, Arguments arguments) =>
        {
            KernelReturnParameterMetadata parameter = (KernelReturnParameterMetadata)arguments[0];
            var functionName = arguments[1].ToString();
            return parameter.ToSKParameterMetadata(functionName).GetSchemaTypeName();
        });
    }
}
