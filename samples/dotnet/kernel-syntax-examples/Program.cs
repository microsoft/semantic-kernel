// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Threading.Tasks;

public static class Program
{
    // ReSharper disable once InconsistentNaming
    public static async Task Main()
    {
        //await Example22_OpenApiSkill.RunAsync();
        //Console.WriteLine("== DONE ==");

        await Example22_OpenApiSkill_Jira.RunAsync();
        Console.WriteLine("== DONE ==");
    }
}
