import { Verify } from '../utils/verify';

/**
 * Optional attribute to set the name used for the function in the skill collection.
 */
export class SKFunctionNameAttribute {
    // Function name
    public readonly name: string;

    /**
     * Tag a C# function as a native function available to SK.
     * @param name Function name.
     */
    public constructor(name: string) {
        Verify.validFunctionName(name);
        this.name = name;
    }
}
