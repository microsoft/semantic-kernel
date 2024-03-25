using System;
using System.ComponentModel;
using System.Threading.Tasks;
using Microsoft.SemanticKernel;

namespace Plugins;

public class Email
{
    [KernelFunction("SendEmail")]
    [Description("Sends an email to a customer")]
    public async Task<string> SendEmailAsync(string to, string subject, string body)
    {
        // Simulate sending an email
        await Task.Delay(1000);

        Console.ForegroundColor = ConsoleColor.Red;
        Console.Write("To: ");
        Console.ResetColor();
        Console.WriteLine(to);

        Console.ForegroundColor = ConsoleColor.Red;
        Console.Write("Subject: ");
        Console.ResetColor();
        Console.WriteLine(subject);

        Console.ForegroundColor = ConsoleColor.Red;
        Console.Write("Body: ");
        Console.ResetColor();
        Console.WriteLine(body);

        return $"Email sent to {to} with subject '{subject}'";
    }
}
