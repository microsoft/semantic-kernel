/**
 * Copyright (c) Microsoft Corporation. All rights reserved.
 * Licensed under the MIT License.
 */

import { ISKMethodInfo } from './iSKMethodInfo';

/**
 * Decorator required to register native functions into the kernel.
 * @remarks
 * The registration is required by the prompt templating engine and by the pipeline generator (aka planner).
 * The quality of the description affects the planner ability to reason about complex tasks.
 * The description is used both with LLM prompts and embedding comparisons.
 */
export function SKFunction(
    description: string
): (target: any, propertyKey: string, descriptor: PropertyDescriptor) => void {
    return (target: any, propertyKey: string, descriptor: PropertyDescriptor) => {
        if (typeof descriptor.value !== 'function') {
            throw new Error(`@SKFunction(${description}) decorator can only be applied to methods.`);
        }

        const info = descriptor.value as ISKMethodInfo;
        info.hasSkFunctionAttribute = true;
        info.description = description;
        if (!Array.isArray(info.parameters)) {
            info.parameters = [];
        }
    };
}
