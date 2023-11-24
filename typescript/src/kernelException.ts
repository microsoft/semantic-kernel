type ErrorCodes = (typeof KernelException.ErrorCodes)[keyof typeof KernelException.ErrorCodes];

export class KernelException extends Error {
    static readonly ErrorCodes = {
        // Unknown error.
        UnknownError: -1,
        // Invalid function description.
        InvalidFunctionDescription: 0,
        // Function overload not supported.
        FunctionOverloadNotSupported: 1,
        // Function not available.
        FunctionNotAvailable: 2,
        // Function type not supported.
        FunctionTypeNotSupported: 3,
        // Invalid function type.
        InvalidFunctionType: 4,
        // Invalid service configuration.
        InvalidServiceConfiguration: 5,
        // Service not found.
        ServiceNotFound: 6,
        // Skill collection not set.
        SkillCollectionNotSet: 7,
        // Represents an error that occurs when invoking a function.
        FunctionInvokeError: 8,
        // Ambiguous implementation.
        AmbiguousImplementation: 9,
    } as const;

    constructor(
        public readonly errorCode: ErrorCodes,
        public override readonly message: string,
        public readonly innerException?: Error
    ) {
        super(message);
    }
}
