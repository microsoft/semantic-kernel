/**
 * Copyright (c) Microsoft Corporation. All rights reserved.
 * Licensed under the MIT License.
 */

import { IPromptTemplate } from './iPromptTemplate';
import { IPromptTemplateConfig } from './promptTemplateConfig';

export interface ISemanticFunctionConfig {
    promptTemplateConfig: IPromptTemplateConfig;
    promptTemplate: IPromptTemplate;
}
