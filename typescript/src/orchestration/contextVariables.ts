// Copyright (c) Microsoft. All rights reserved.

import { CaseInsensitiveMap } from '../utils/caseInsensitiveMap';
import { Verify } from '../utils/verify';

export class ContextVariables {
    private readonly mainKey = 'INPUT';

    // In the simplest scenario, the data is an input string, stored here.
    public input: string;

    // Important: names are case insensitive
    private readonly _variables: CaseInsensitiveMap<string, string> = new CaseInsensitiveMap();

    /**
     * Constructor for context variables.
     *
     * @constructor
     * @param content Optional value for the main variable of the context.
     */
    public constructor(content: string = '') {
        this._variables.set(this.mainKey, content);
        this.input = content;
    }

    /**
     * Updates the main input text with the new value after a function is complete.
     *
     * @param content The new input value, for the next function in the pipeline, or as a result for the user if the pipeline reached the end.
     * @returns The current instance.
     */
    public update(content: string): ContextVariables {
        this._variables.set(this.mainKey, content);
        return this;
    }

    /**
     * Updates all the local data with new data, merging the two datasets. Do not discard old data.
     *
     * @param newData New data to be merged.
     * @param merge Whether to merge and keep old data, or replace. false == discard old data.
     * @returns The current instance.
     */
    public updateAll(newData: ContextVariables, merge: boolean = true): ContextVariables {
        // If requested, discard old data and keep only the new one.
        if (!merge) {
            this._variables.clear();
        }

        const newDataCollection: CaseInsensitiveMap<string, string> = newData.getAll();
        for (const key of newDataCollection.keys()) {
            const newDataValue = newDataCollection.get(key);
            if (newDataValue) {
                this._variables.set(key, newDataValue);
            }
        }

        return this;
    }

    /**
     * This method allows to store additional data in the context variables, e.g. variables needed by functions in the pipeline.
     * These "variables" are visible also to semantic functions using the "{{varName}}" syntax,
     * allowing to inject more information into prompt templates.
     *
     * @param name Variable name.
     * @param value Value to store. If the value is NULL the variable is deleted.
     */
    public set(name: string, value?: string): void {
        // TODO: support for more complex data types, and plan for rendering these values into prompt templates.
        Verify.notEmpty(name, `The variable name is empty`);
        if (value) {
            this._variables.set(name, value);
        } else {
            this._variables.delete(name);
        }
    }

    /**
     * Fetch a variable value from the context variables.
     *
     * @param name Variable name.
     * @param value Value.
     * @returns Whether the value exists in the context variables.
     */
    public get(name: string): string | undefined {
        return this._variables.get(name);
    }

    /**
     * Get all context variables.
     *
     * @returns Context variables.
     */
    public getAll(): CaseInsensitiveMap<string, string> {
        return this._variables;
    }

    /**
     * Returns true if there is a variable with the given name
     *
     * @param name Variable name
     * @returns True if there is a variable with the given name, false otherwise
     */
    public has(name: string): boolean {
        return this._variables.has(name);
    }

    /**
     * Print the processed input, aka the current data after any processing occurred.
     *
     * @returns Processed input, aka result
     */
    public toString(): string {
        return this.input;
    }
}
