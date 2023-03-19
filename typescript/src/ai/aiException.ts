// Copyright (c) Microsoft Corporation. All rights reserved.

export enum AIExceptionErrorCode {
    // Unknown error.
    UnknownError = -1,

    // No response.
    NoResponse = 0,

    // Access is denied.
    AccessDenied = 1,

    // The request was invalid.
    InvalidRequest = 2,

    // The content of the response was invalid.
    InvalidResponseContent = 3,

    // The request was throttled.
    Throttling = 4,

    // The request timed out.
    RequestTimeout = 5,

    // There was an error in the service.
    ServiceError = 6,

    // The requested model is not available.
    ModelNotAvailable = 7,

    // The supplied configuration was invalid.
    InvalidConfiguration = 8,

    // The function is not supported.
    FunctionTypeNotSupported = 9,
}

/**
 * AI logic exception
 */
export class AIException extends Error {
    private _errorCode: AIExceptionErrorCode;

    public constructor(errorCode: AIExceptionErrorCode) {
        super();
        this._errorCode = errorCode;
    }

    public get errorCode(): AIExceptionErrorCode {
        return this._errorCode;
    }
}
