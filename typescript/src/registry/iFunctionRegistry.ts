/**
 * Copyright (c) Microsoft Corporation. All rights reserved.
 * Licensed under the MIT License.
 */

import { IFunctionRegistryReader } from './iFunctionRegistryReader';
import { ISKFunction } from '../orchestration';

export interface IFunctionRegistry extends IFunctionRegistryReader {
    /**
     * Readonly only access into the registry
     */
    readonly functionRegistryReader: IFunctionRegistryReader;

    /**
     * Add a semantic function to the registry
     * @param fn Function delegate
     * @returns Self instance
     */
    registerSemanticFunction(fn: ISKFunction): this;

    /**
     * Add a native function to the registry
     * @param fn Wrapped function delegate
     * @returns Self instance
     */
    registerNativeFunction(fn: ISKFunction): this;
}
