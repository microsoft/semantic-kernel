/**
 * Copyright (c) Microsoft Corporation. All rights reserved.
 * Licensed under the MIT License.
 */

import { SKContext } from '../orchestration';
import { ParameterView } from '../registry';

export interface IPromptTemplate {
    /**
     * Get the list of parameters required by the template, using configuration and template info.
     * @returns List of parameters
     */
    getParameters(): ParameterView[];

    /**
     * Render the template using the information in the working memory and the functions in the kernel registry
     * @param executionContext Kernel execution context helpers
     * @returns Prompt rendered to string
     */
    render(executionContext: SKContext): Promise<string>;
}
