// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.PromptTemplates.Handlebars;

namespace Extensions.UnitTests.PromptTemplates.Handlebars;

internal static class TestUtilities
{
    public static PromptTemplateConfig InitializeHbPromptConfig(
        string template,
        List<InputVariable>? inputVariables = null)
    {
        return new PromptTemplateConfig()
        {
            TemplateFormat = HandlebarsPromptTemplateFactory.HandlebarsTemplateFormat,
            Template = template,
            InputVariables = inputVariables ?? []
        };
    }
}
