// Copyright (c) Microsoft. All rights reserved.

using System.Text.Json;
using Microsoft.Extensions.Logging;
using Spectre.Console;
using Spectre.Console.Json;

public class SemanticKernelLogger : ILogger
{
    public IDisposable? BeginScope<TState>(TState state) where TState : notnull
    {
        return null;
    }

    public bool IsEnabled(LogLevel logLevel)
    {
        return true;
    }

    public void Log<TState>(LogLevel logLevel, EventId eventId, TState state, Exception? exception, Func<TState, Exception?, string> formatter)
    {
        if (!this.IsEnabled(logLevel))
        {
            return;
        }

        // You can reformat the message here
        var message = formatter(state, exception);
        if (!this.PrintMessageBetweenTags(message, "Rendered prompt", "[FUNCTIONS]", "[END FUNCTIONS]")
            && !this.PrintMessageWithALabelAndJson("Function result:", message)
            && !this.PrintMessageWithALabelAndJson("Function arguments:", message)
            && !this.PrintMessageWithALabelAndJson("Plan result:", message))
        {
            AnsiConsole.MarkupLine($"[green]{logLevel}[/] {Markup.Escape(message)}");
        }
    }

    private bool PrintMessageWithALabelAndJson(string label, string message)
    {
        if (message.StartsWith(label, System.StringComparison.Ordinal))
        {
            var json = message.Substring(label.Length).Trim();

            try
            {
                var jsonText = new JsonText(json);
                AnsiConsole.Write(
                    new Panel(jsonText)
                        .Header(label)
                        .Collapse()
                        .RoundedBorder()
                        .BorderColor(Color.Yellow));
            }
            catch
            {
                AnsiConsole.MarkupLine(Markup.Escape(message));
            }

            string[] nestedJsonObjectLabels = ["available_functions", "Content"];
            foreach (var nestedJsonObjectLabel in nestedJsonObjectLabels)
            {
                try
                {
                    var jsonDoc = JsonDocument.Parse(json);
                    var content = jsonDoc.RootElement.GetProperty(nestedJsonObjectLabel).GetString();
                    if (content != null)
                    {
                        var jsonText = new JsonText(content);
                        AnsiConsole.Write(
                            new Panel(jsonText)
                                .Header(nestedJsonObjectLabel)
                                .Collapse()
                                .RoundedBorder()
                                .BorderColor(Color.Yellow));
                    }
                }
                catch
                {
                    // ignored
                }
            }

            return true;
        }

        return false;
    }

    private bool PrintMessageBetweenTags(string message, string label, string startTag, string endTag)
    {
        if (message.StartsWith(label, System.StringComparison.Ordinal))
        {
            var split = message.Split(startTag);
            AnsiConsole.MarkupLine($"[green]{this.EscapeMarkup(split[0])}[/]");
            if (split.Length > 1)
            {
                var split2 = split[1].Split(endTag);
                try
                {
                    var jsonText = new JsonText(this.EscapeMarkup(split2[0]));
                    AnsiConsole.Write(
                        new Panel(jsonText)
                            .Header("Functions")
                            .Collapse()
                            .RoundedBorder()
                            .BorderColor(Color.Yellow));
                }
                catch
                {
                    AnsiConsole.MarkupLine(this.EscapeMarkup(split2[0]));
                }

                AnsiConsole.MarkupLine(this.EscapeMarkup(split2[1]));
                return true;
            }
        }

        return false;
    }

    private string EscapeMarkup(string text)
    {
        return text.Replace("[", "[[").Replace("]", "]]");
    }
}
