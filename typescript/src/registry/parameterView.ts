/**
 * Copyright (c) Microsoft Corporation. All rights reserved.
 * Licensed under the MIT License.
 */

import { Verify } from '../diagnostics';

/**
 * Class used to copy and export data from
 * {@link SKFunctionContextParameterAttribute}
 * and {@link SKFunctionInputAttribute}
 * for planner and related scenarios.
 */
export class ParameterView {
    private _name: string = '';

    /**
     * Parameter name. Alphanumeric chars + "_" only.
     */
    public get name(): string {
        return this._name;
    }
    public set name(value: string) {
        Verify.validFunctionParamName(value);
        this._name = value;
    }

    /**
     * Parameter description.
     */
    public description: string;

    /**
     * Default value when the value is not provided.
     */
    public defaultValue: string;

    /**
     * Create a function parameter view, using information provided by the skill developer.
     * @param name Parameter name. The name must be alphanumeric (underscore is the only special char allowed).
     * @param description Parameter description
     * @param defaultValue Default parameter value, if not provided
     */
    public constructor(name: string, description: string = '', defaultValue: string = '') {
        Verify.validFunctionParamName(name);

        this.name = name;
        this.description = description;
        this.defaultValue = defaultValue;
    }
}
