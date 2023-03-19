// Copyright (c) Microsoft Corporation. All rights reserved.

import { IPromptTemplate } from './IPromptTemplate';
import { IPromptTemplateConfig } from './PromptTemplateConfig';

/**
 * Semantic function configuration.
 */
export class SemanticFunctionConfig {
    // Prompt template configuration.
    public readonly promptTemplateConfig: IPromptTemplateConfig;
    // Prompt template.
    public readonly promptTemplate: IPromptTemplate;

    /**
     * Constructor for SemanticFunctionConfig.
     * @param config Prompt template configuration.
     * @param template Prompt template.
     */
    public constructor(config: IPromptTemplateConfig, template: IPromptTemplate) {
        this.promptTemplateConfig = config;
        this.promptTemplate = template;
    }
}
