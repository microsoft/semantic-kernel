import { IAskInput } from './Ask';

export interface IAskResult {
    value: string;

    state: IAskInput[];
}
