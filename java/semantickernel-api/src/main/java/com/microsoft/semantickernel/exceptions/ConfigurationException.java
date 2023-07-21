// Copyright (c) Microsoft. All rights reserved.
package com.microsoft.semantickernel.exceptions;

import javax.annotation.Nonnull;
import javax.annotation.Nullable;

/** Kernel logic exception */
public class ConfigurationException extends Exception {

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
        super(getDefaultMessage(errorCode, message), innerException);
        this.errorCode = errorCode;
    }

    public ErrorCodes getErrorCode() {
        return errorCode;
    }

    /* Translate the error code into a default message */
    private static String getDefaultMessage(
            @Nonnull ErrorCodes errorCode, @Nullable String message) {
        return String.format("%s: %s", errorCode.getMessage(), message);
    }

    public enum ErrorCodes {
        UnknownError("Unknown error"),

        ConfigurationNotFound("Could not find configuration file"),

        CouldNotReadConfiguration("Could not parse or load configuration file"),
        NoValidConfigurationsFound("Could not find any valid configuration settings"),
        ValueNotFound("Could not find value for configuration key");

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
