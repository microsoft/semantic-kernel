// Copyright (c) Microsoft. All rights reserved.

using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.PromptTemplates.Handlebars;

namespace Extensions.UnitTests.PromptTemplates.Handlebars;

public static class HandlebarsPromptTemplateTestUtils
{
    public static PromptTemplateConfig InitializeHbPromptConfig(string template)
    {
        return new PromptTemplateConfig()
        {
            TemplateFormat = HandlebarsPromptTemplateFactory.HandlebarsTemplateFormat,
            Template = template
        };
    }
}
