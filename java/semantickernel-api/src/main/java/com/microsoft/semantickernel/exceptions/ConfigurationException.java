// Copyright (c) Microsoft. All rights reserved.
package com.microsoft.semantickernel.exceptions;

import com.microsoft.semantickernel.SKCheckedException;
import javax.annotation.Nonnull;
import javax.annotation.Nullable;

/** Kernel logic exception */
public class ConfigurationException extends SKCheckedException {

    @Nonnull private final ErrorCodes errorCode;

    public ConfigurationException(@Nonnull ErrorCodes error) {
        this(error, null, null);
    }

    public ConfigurationException(@Nonnull ErrorCodes errorCode, @Nullable String message) {
        this(errorCode, message, null);
    }

    public ConfigurationException(
            @Nonnull ErrorCodes errorCode,
            @Nullable String message,
            @Nullable Throwable innerException) {
        super(formatDefaultMessage(errorCode.getMessage(), message), innerException);
        this.errorCode = errorCode;
    }

    public ErrorCodes getErrorCode() {
        return errorCode;
    }

    public enum ErrorCodes {
        UNKNOWN_ERROR("Unknown error"),

        CONFIGURATION_NOT_FOUND("Could not find configuration file"),

        COULD_NOT_READ_CONFIGURATION("Could not parse or load configuration file"),
        NO_VALID_CONFIGURATIONS_FOUND("Could not find any valid configuration settings"),
        VALUE_NOT_FOUND("Could not find value for configuration key");

        private final String message;

        ErrorCodes(String message) {
            this.message = message;
        }

        public String getMessage() {
            return message;
        }

        public String getMessage(String param) {
            return String.format(message, param);
        }
    }
}
