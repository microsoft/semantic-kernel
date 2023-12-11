// Copyright (c) Microsoft. All rights reserved.

using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.PromptTemplate.Handlebars;

namespace Extensions.UnitTests.PromptTemplate.Handlebars;

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
