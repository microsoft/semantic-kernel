package com.microsoft.semantickernel.semanticfunctions;

public interface PromptTemplateFactory {

    PromptTemplate tryCreate(PromptTemplateConfig templateConfig);

}
