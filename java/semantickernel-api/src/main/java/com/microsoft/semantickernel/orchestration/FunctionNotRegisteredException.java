// Copyright (c) Microsoft. All rights reserved.
package com.microsoft.semantickernel.orchestration;

import com.microsoft.semantickernel.SKException;
import javax.annotation.Nonnull;

public class FunctionNotRegisteredException extends SKException {

  @Nonnull
  private final ErrorCodes errorCode;

  public FunctionNotRegisteredException(@Nonnull ErrorCodes errorCode) {
    this(errorCode, null);
  }
  public FunctionNotRegisteredException(@Nonnull ErrorCodes errorCode, String name) {
    this(errorCode, name, null);
  }

  public FunctionNotRegisteredException(@Nonnull ErrorCodes errorCode, String name, Throwable cause) {
    super(formatDefaultMessage(errorCode, name), cause);
    this.errorCode = errorCode;
  }

  public ErrorCodes getErrorCode() {
    return errorCode;
  }

  private static String formatDefaultMessage(@Nonnull ErrorCodes errorCode, String name) {
    if (name != null) {
      String detailedMessage = String.format(
              "It does not appear this function(%s) has been registered on a kernel.%n"
                  + "Register it on a kernel either by passing it to "
                  + "KernelConfig.Builder().addSkill() when building the kernel, or%n"
                  + "passing it to Kernel.registerSemanticFunction",
              name);
      return SKException.formatDefaultMessage(errorCode.getErrorMessage(), detailedMessage);
    }
    return errorCode.getErrorMessage();
  }

  public enum ErrorCodes {
      FUNCTION_NOT_REGISTERED("Function not registered");

      private final String errorMessage;

      ErrorCodes(String errorMessage) {
          this.errorMessage = errorMessage;
      }

      public String getErrorMessage() {
          return errorMessage;
      }
  }
}
