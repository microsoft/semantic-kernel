import { ParameterView } from './parameterView';

/**
 * Attribute to describe the main parameter required by a native function,
 * e.g. the first "string" parameter, if the function requires one.
 */
export class SKFunctionInputAttribute {
    // Parameter description.
    public description: string = '';
    // Default value when the value is not provided.
    public defaultValue: string = '';

    /**
     * Creates a parameter view, using information from an instance of this class.
     * @returns Parameter view.
     */
    public toParameterView(): ParameterView {
        return new ParameterView('input', this.description, this.defaultValue);
    }
}
