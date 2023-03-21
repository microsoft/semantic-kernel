/**
 * Copyright (c) Microsoft Corporation. All rights reserved.
 * Licensed under the MIT License.
 */

import { ISKMethodInfo } from './iSKMethodInfo';
import { ParameterView } from './parameterView';

export interface ISKFunctionInputParameter {
    description?: string;
    defaultValue?: string;
}

/**
 * Decorator to describe the main parameter required by a native function,
 * @remarks
 * e.g.
 * @SKFunctionInput({ description: "...", defaultValue: "..." })
 */
export function SKFunctionInput(
    parameter: ISKFunctionInputParameter = {}
): (target: any, propertyKey: string, descriptor: PropertyDescriptor) => void {
    return (target: any, propertyKey: string, descriptor: PropertyDescriptor) => {
        if (typeof descriptor.value !== 'function') {
            throw new Error(
                `@SKFunctionInput(${parameter.description ?? ''}) decorator can only be applied to methods.`
            );
        }

        const info = descriptor.value as ISKMethodInfo;
        if (!Array.isArray(info.parameters)) {
            info.parameters = [];
        }
        info.parameters.push(new ParameterView('input', parameter.description, parameter.defaultValue));
    };
}
