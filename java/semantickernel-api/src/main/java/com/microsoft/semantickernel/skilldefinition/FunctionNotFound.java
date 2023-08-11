// Copyright (c) Microsoft. All rights reserved.
package com.microsoft.semantickernel.skilldefinition;

import com.microsoft.semantickernel.SKException;
import javax.annotation.Nonnull;
import javax.annotation.Nullable;

public class FunctionNotFound extends SKException {

  private final ErrorCodes errorCode;

  public FunctionNotFound(@Nonnull ErrorCodes errorCodes) {
    this(errorCodes, null, null);
  }

  public FunctionNotFound(@Nonnull ErrorCodes errorCodes, @Nullable String functionName) {
    this(errorCodes, functionName, null);
  }

  public FunctionNotFound(@Nonnull ErrorCodes errorCodes, @Nullable String functionName, @Nullable Throwable cause) {
      super(formatDefaultMessage(errorCodes.getMessage(), functionName), cause);
      this.errorCode = errorCodes;
  }

    public ErrorCodes getErrorCode() {
        return errorCode;
    }

    public enum ErrorCodes {
        FUNCTION_NOT_FOUND("Function not found");

        final String message;

        ErrorCodes(String message) {
            this.message = message;
        }

        String getMessage() {
            return message;
        }
    }
}
