// Copyright (c) Microsoft. All rights reserved.
package com.microsoft.semantickernel;

/** Kernel logic exception */
public class KernelException extends RuntimeException {

    /*
        /// <summary>
        /// Semantic kernel error codes.
        /// </summary>
        public enum ErrorCodes {
            /// <summary>
            /// Unknown error.
            /// </summary>
            UnknownError =-1,

            /// <summary>
            /// Invalid function description.
            /// </summary>
            InvalidFunctionDescription,

            /// <summary>
            /// Function overload not supported.
            /// </summary>
            FunctionOverloadNotSupported,

            /// <summary>
            /// Function not available.
            /// </summary>
            FunctionNotAvailable,

            /// <summary>
            /// Function type not supported.
            /// </summary>
            FunctionTypeNotSupported,

            /// <summary>
            /// Invalid function type.
            /// </summary>
            InvalidFunctionType,

            /// <summary>
            /// Invalid service configuration.
            /// </summary>
            InvalidServiceConfiguration,

            /// <summary>
            /// Service not found.
            /// </summary>
            ServiceNotFound,

            /// <summary>
            /// Skill collection not set.
            /// </summary>
            SkillCollectionNotSet,

            /// <summary>
            /// Represents an error that occurs when invoking a function.
            /// </summary>
            FunctionInvokeError,
        }

        /// <summary>
        /// Error code.
        /// </summary>
        public ErrorCodes ErrorCode

        {
            get;
            set;
        }

        /// <summary>
    /// Constructor for KernelException.
    /// </summary>
    /// <param name="errCode">Error code to put in KernelException.</param>
    /// <param name="message">Message to put in KernelException.</param>
        public KernelException(ErrorCodes errCode, string?message=null) :

        base(errCode, message) {
            this.ErrorCode = errCode;
        }

        /// <summary>
    /// Constructor for KernelException.
    /// </summary>
    /// <param name="errCode">Error code to put in KernelException.</param>
    /// <param name="message">Message to put in KernelException.</param>
    /// <param name="e">Exception to embed in KernelException.</param>
        public KernelException(ErrorCodes errCode, string message, Exception?e) :

        base(errCode, message, e) {
            this.ErrorCode = errCode;
        }

            #region private ================================================================================

        private KernelException() {
            // Not allowed, error code is required
        }

        private KernelException(string message) :

        base(message) {
            // Not allowed, error code is required
        }

        private KernelException(string message, Exception innerException) :

        base(message, innerException) {
            // Not allowed, error code is required
        }

            #endregion

         */
}
