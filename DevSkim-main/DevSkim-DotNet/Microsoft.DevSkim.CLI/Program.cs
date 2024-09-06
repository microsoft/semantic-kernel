// Copyright (C) Microsoft. All rights reserved. Licensed under the MIT License.

using System.Linq;
using CommandLine;
using Microsoft.DevSkim.CLI.Commands;
using Microsoft.DevSkim.CLI.Options;

namespace Microsoft.DevSkim.CLI
{
    internal class Program
    {
        private static int Main(string[] args)
        {
            return Parser.Default.ParseArguments<AnalyzeCommandOptions, FixCommandOptions, VerifyCommandOptions, SuppressionCommandOptions>(args)
                .MapResult(
                    (AnalyzeCommandOptions opts) => new AnalyzeCommand(opts).Run(),
                    (FixCommandOptions opts) => new FixCommand(opts).Run(),
                    (VerifyCommandOptions opts) => new VerifyCommand(opts).Run(),
                    (SuppressionCommandOptions opts) => new SuppressionCommand(opts).Run(),
                    errs =>
                        errs.Any(x =>
                            x.Tag is not ErrorType.VersionRequestedError
                            and not ErrorType.HelpVerbRequestedError
                            and not ErrorType.HelpRequestedError)
                                ? (int)ExitCode.ArgumentParsingError : (int)ExitCode.Okay);
        }
    }
}