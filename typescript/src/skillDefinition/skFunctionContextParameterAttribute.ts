import { Verify } from '../utils/verify';
import { ParameterView } from './parameterView';

export class SKFunctionContextParameterAttribute {
    private _name: string = '';

    // Parameter name. Alphanumeric chars + "_" only.
    public get name(): string {
        return this._name;
    }
    public set name(value: string) {
        Verify.validFunctionParamName(value);
        this._name = value;
    }

    // Parameter description.
    public description: string = '';

    // Default value when the value is not provided.
    public defaultValue: string = '';

    public toParameterView(): ParameterView {
        Verify.notEmpty(this.name, 'The parameter name is missing');

        return new ParameterView(this.name, this.description, this.defaultValue);
    }
}
