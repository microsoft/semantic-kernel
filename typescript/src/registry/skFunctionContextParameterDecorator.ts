/**
 * Copyright (c) Microsoft Corporation. All rights reserved.
 * Licensed under the MIT License.
 */

import { ISKMethodInfo } from './iSKMethodInfo';
import { ParameterView } from './parameterView';

export interface ISKFunctionContextParameter {
    name: string;
    description?: string;
    defaultValue?: string;
}

/**
 * Decorator to describe the parameters required by a native function.
 * @remarks
 * e.g.
 * @SKFunctionContextParameter({ name: "...", description: "...", defaultValue: "..." })
 */
export function SKFunctionContextParameter(
    parameter: ISKFunctionContextParameter
): (target: any, propertyKey: string, descriptor: PropertyDescriptor) => void {
    return (target: any, propertyKey: string, descriptor: PropertyDescriptor) => {
        if (typeof descriptor.value !== 'function') {
            throw new Error(`@SKFunctionContextParameter(${parameter.name}) decorator can only be applied to methods.`);
        }

        const info = descriptor.value as ISKMethodInfo;
        if (!Array.isArray(info.parameters)) {
            info.parameters = [];
        }
        info.parameters.push(new ParameterView(parameter.name, parameter.description, parameter.defaultValue));
    };
}
