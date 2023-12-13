// Copyright (c) Microsoft. All rights reserved.
package com.microsoft.semantickernel.exceptions;

import com.microsoft.semantickernel.SKException;
import javax.annotation.Nonnull;
import javax.annotation.Nullable;

public class NotSupportedException extends SKException {

    private final ErrorCodes errorCode;

    public NotSupportedException(@Nonnull ErrorCodes errorCode) {
        this(errorCode, null, null);
    }

    public NotSupportedException(@Nonnull ErrorCodes errorCode, @Nullable String message) {
        this(errorCode, message, null);
    }

    public NotSupportedException(
            @Nonnull ErrorCodes errorCode, @Nullable String message, @Nullable Throwable cause) {
        super(formatDefaultMessage(errorCode.getMessage(), message), cause);
        this.errorCode = errorCode;
    }

    public ErrorCodes getErrorCode() {
        return errorCode;
    }

    public enum ErrorCodes {
        NOT_SUPPORTED("Not Supported");

        final String message;

        ErrorCodes(String message) {
            this.message = message;
        }

        String getMessage() {
            return message;
        }
    }
}
