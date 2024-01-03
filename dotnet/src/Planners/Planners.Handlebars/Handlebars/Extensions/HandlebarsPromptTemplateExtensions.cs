// Copyright (c) Microsoft. All rights reserved.

using HandlebarsDotNet;
using Microsoft.SemanticKernel.PromptTemplates.Handlebars;
using static Microsoft.SemanticKernel.PromptTemplates.Handlebars.HandlebarsPromptTemplateOptions;

namespace Microsoft.SemanticKernel.Planning.Handlebars;

/// <summary>
/// Provides extension methods for rendering Handlebars templates in the context of a Semantic Kernel.
/// </summary>
internal sealed class HandlebarsPromptTemplateExtensions
{
    public static void RegisterCustomCreatePlanHelpers(
        RegisterHelperCallback registerHelper,
        HandlebarsPromptTemplateOptions options,
        KernelArguments executionContext
    )
    {
        registerHelper("getSchemaTypeName", static (Context context, Arguments arguments) =>
        {
            KernelParameterMetadata parameter = (KernelParameterMetadata)arguments[0];
            return parameter.GetSchemaTypeName();
        });

        registerHelper("getSchemaReturnTypeName", static (Context context, Arguments arguments) =>
        {
            KernelReturnParameterMetadata parameter = (KernelReturnParameterMetadata)arguments[0];
            var functionName = arguments[1].ToString();
            return parameter.ToKernelParameterMetadata(functionName).GetSchemaTypeName();
        });
    }
}
