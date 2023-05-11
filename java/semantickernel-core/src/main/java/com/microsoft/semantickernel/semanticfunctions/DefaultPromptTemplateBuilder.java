// Copyright (c) Microsoft. All rights reserved.
package com.microsoft.semantickernel.semanticfunctions;

public class DefaultPromptTemplateBuilder implements PromptTemplate.Builder {

    @Override
    public PromptTemplate build(String promptTemplate, PromptTemplateConfig config) {
        return new DefaultPromptTemplate(promptTemplate, config);
    }
}
