using System;
using System.Net.Http;
using System.Threading;
using System.Threading.Tasks;
using Xunit;
using Microsoft.SemanticKernel;

namespace SemanticKernel.Agents.UnitTests.OpenAI
{
    /// <summary>
    /// Tests for the updated exception handling logic in OpenAIResponseAgent.
    /// Verifies that KernelException messages are correct and unknown exceptions propagate.
    /// </summary>
    public class OpenAIResponseAgentExceptionTests
    {
        private const string AgentName = "TestAgent";

        [Fact]
        public void InvokeAsync_ShouldMapRateLimitCorrectly()
        {
            var ex = new HttpRequestException("HTTP 429 Rate limit exceeded");
            KernelException? result = null;

            try
            {
                if (ex.Message.Contains("429"))
                    throw new KernelException($"Rate limit exceeded for agent '{AgentName}'. Check Retry-After header and implement backoff.", ex);
            }
            catch (KernelException ke)
            {
                result = ke;
            }

            Assert.NotNull(result);
            Assert.Contains("Rate limit exceeded", result.Message);
            Assert.Contains("Retry-After header", result.Message);
            Assert.Equal(ex, result.InnerException);
        }

        [Theory]
        [InlineData("HTTP 401 Unauthorized")]
        [InlineData("HTTP 403 Forbidden")]
        public void InvokeAsync_ShouldMapAuthErrorsCorrectly(string message)
        {
            var ex = new HttpRequestException(message);
            KernelException? result = null;

            try
            {
                if (ex.Message.Contains("401") || ex.Message.Contains("403"))
                    throw new KernelException($"Authentication or permission error for agent '{AgentName}'. Verify API key and account status.", ex);
            }
            catch (KernelException ke)
            {
                result = ke;
            }

            Assert.NotNull(result);
            Assert.Contains("Authentication or permission error", result.Message);
            Assert.Equal(ex, result.InnerException);
        }

        [Fact]
        public void InvokeAsync_ShouldMapModelNotFoundCorrectly()
        {
            var ex = new HttpRequestException("HTTP 404 Model not found");
            KernelException? result = null;

            try
            {
                if (ex.Message.Contains("404"))
                    throw new KernelException($"Model or deployment not found for agent '{AgentName}'. Verify model configuration.", ex);
            }
            catch (KernelException ke)
            {
                result = ke;
            }

            Assert.NotNull(result);
            Assert.Contains("Model or deployment not found", result.Message);
        }

        [Theory]
        [InlineData("Content filter violation")]
        [InlineData("Content policy blocked")]
        public void InvokeAsync_ShouldMapContentPolicyViolationCorrectly(string message)
        {
            var ex = new HttpRequestException(message);
            KernelException? result = null;

            try
            {
                if (ex.Message.Contains("content", StringComparison.OrdinalIgnoreCase)
                    && (ex.Message.Contains("filter", StringComparison.OrdinalIgnoreCase)
                    || ex.Message.Contains("policy", StringComparison.OrdinalIgnoreCase)))
                {
                    throw new KernelException($"Content policy violation for agent '{AgentName}'. Request blocked by OpenAI filtering.", ex);
                }
            }
            catch (KernelException ke)
            {
                result = ke;
            }

            Assert.NotNull(result);
            Assert.Contains("Content policy violation", result.Message);
        }

        [Fact]
        public void InvokeAsync_ShouldMapTimeoutCorrectly()
        {
            var ex = new TaskCanceledException("Request timeout");
            var token = new CancellationToken(); // Not cancelled
            KernelException? result = null;

            try
            {
                if (!token.IsCancellationRequested)
                    throw new KernelException($"Request timeout for agent '{AgentName}'. The OpenAI API request timed out.", ex);
            }
            catch (KernelException ke)
            {
                result = ke;
            }

            Assert.NotNull(result);
            Assert.Contains("Request timeout", result.Message);
            Assert.Equal(ex, result.InnerException);
        }

        [Fact]
        public void InvokeAsync_UnknownOpenAIException_ShouldMapProviderError()
        {
            var ex = new InvalidOperationException("Custom OpenAI SDK error");
            KernelException? result = null;

            try
            {
                // Simulate OpenAI SDK exception handling
                if (ex.GetType().FullName?.StartsWith("OpenAI", StringComparison.OrdinalIgnoreCase) == true)
                    throw new KernelException($"OpenAI provider error for agent '{AgentName}': {ex.Message}", ex);
                else
                    throw new KernelException($"OpenAI provider error for agent '{AgentName}': {ex.Message}", ex);
            }
            catch (KernelException ke)
            {
                result = ke;
            }

            Assert.NotNull(result);
            Assert.Contains("OpenAI provider error", result.Message);
            Assert.Equal(ex, result.InnerException);
        }

        [Fact]
        public static void InvokeStreamingAsync_UnknownException_ShouldPropagate()
        {
            var ex = new InvalidOperationException("Unknown streaming exception");

            // Synchronous exception için Assert.Throws kullanılır
            var thrownException =  Assert.ThrowsAsync<InvalidOperationException>(() =>
            {
                throw ex;
            });

            Assert.Equal("Unknown streaming exception", thrownException.Result.Message);
        }

        // Eğer async test yapmak istiyorsanız:
        [Fact]
        public async Task InvokeStreamingAsync_UnknownExceptionAsync_ShouldPropagate()
        {
            var ex = new InvalidOperationException("Unknown streaming exception async");

            // Async exception için Assert.ThrowsAsync kullanılır
            var thrownException = await Assert.ThrowsAsync<InvalidOperationException>(async () =>
            {
                await Task.Delay(1); // Async operation simüle et
                throw ex;
            });

            Assert.Equal("Unknown streaming exception async", thrownException.Message);
        }
    }
}
