// Copyright (c) Microsoft. All rights reserved.

using MCPServer.ProjectResources;
using Microsoft.SemanticKernel;
using ModelContextProtocol.Protocol.Types;
using ModelContextProtocol.Server;

namespace MCPServer.Tools;

/// <summary>
/// A collection of utility methods for working with mailbox.
/// </summary>
internal sealed class MailboxUtils
{
    /// <summary>
    /// Summarizes unread emails in the mailbox by using MCP sampling
    /// mechanism for summarization.
    /// </summary>
    [KernelFunction]
    public static async Task<string> SummarizeUnreadEmailsAsync([FromKernelServices] IMcpServer server)
    {
        if (server.ClientCapabilities?.Sampling is null)
        {
            throw new InvalidOperationException("The client does not support sampling.");
        }

        // Create two sample emails with attachments
        var email1 = new Email
        {
            Sender = "sales.report@example.com",
            Subject = "Carretera Sales Report - Jan & Jun 2014",
            Body = "Hi there, I hope this email finds you well! Please find attached the sales report for the first half of 2014. " +
                   "Please review the report and provide your feedback today, if possible." +
                   "By the way, we're having a BBQ this Saturday at my place, and you're welcome to join. Let me know if you can make it!",
            Attachments = [EmbeddedResource.ReadAsBytes("SalesReport2014.png")]
        };

        var email2 = new Email
        {
            Sender = "hr.department@example.com",
            Subject = "Employee Birthdays and Positions",
            Body = "Attached is the list of employee birthdays and their positions. Please check it and let me know of any updates by tomorrow." +
                   "Also, we're planning a hike this Sunday morning. It would be great if you could join us. Let me know if you're interested!",
            Attachments = [EmbeddedResource.ReadAsBytes("EmployeeBirthdaysAndPositions.png")]
        };

        CreateMessageRequestParams request = new()
        {
            SystemPrompt = "You are a helpful assistant. You will be provided with a list of emails. Please summarize them. Each email is followed by its attachments.",
            Messages = CreateMessagesFromEmails(email1, email2),
            Temperature = 0
        };

        // Send the sampling request to the client to summarize the emails
        CreateMessageResult result = await server.RequestSamplingAsync(request, cancellationToken: CancellationToken.None);

        // Assuming the response is a text message
        return result.Content.Text!;
    }

    /// <summary>
    /// Creates a list of SamplingMessage objects from a list of emails.
    /// </summary>
    /// <param name="emails">The list of emails.</param>
    /// <returns>A list of SamplingMessage objects.</returns>
    private static List<SamplingMessage> CreateMessagesFromEmails(params Email[] emails)
    {
        var messages = new List<SamplingMessage>();

        foreach (var email in emails)
        {
            messages.Add(new SamplingMessage
            {
                Role = Role.User,
                Content = new Content
                {
                    Text = $"Email from {email.Sender} with subject {email.Subject}. Body: {email.Body}",
                    Type = "text",
                    MimeType = "text/plain"
                }
            });

            if (email.Attachments != null && email.Attachments.Count != 0)
            {
                foreach (var attachment in email.Attachments)
                {
                    messages.Add(new SamplingMessage
                    {
                        Role = Role.User,
                        Content = new Content
                        {
                            Type = "image",
                            Data = Convert.ToBase64String(attachment),
                            MimeType = "image/png",
                        }
                    });
                }
            }
        }

        return messages;
    }

    /// <summary>
    /// Represents an email.
    /// </summary>
    private sealed class Email
    {
        /// <summary>
        /// Gets or sets the email sender.
        /// </summary>
        public required string Sender { get; set; }

        /// <summary>
        /// Gets or sets the email subject.
        /// </summary>
        public required string Subject { get; set; }

        /// <summary>
        /// Gets or sets the email body.
        /// </summary>
        public required string Body { get; set; }

        /// <summary>
        /// Gets or sets the email attachments.
        /// </summary>
        public List<byte[]>? Attachments { get; set; }
    }
}
