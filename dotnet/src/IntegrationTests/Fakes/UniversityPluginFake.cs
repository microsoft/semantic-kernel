// Copyright (c) Microsoft. All rights reserved.

using System.ComponentModel;
using System.Threading.Tasks;
using Microsoft.SemanticKernel;

namespace SemanticKernel.IntegrationTests.Fakes;

/// <summary>
/// Fake modeled after the Coursera API swagger
/// </summary>
internal sealed class UniversityPluginFake
{
    [KernelFunction, Description("Get the list of courses & their details for an optionally provided query string.")]
    public Task<Course[]> GetCoursesAsync(string? query)
    {
        return Task.FromResult(this._courses);
    }

    private readonly Course[] _courses = new Course[4]
    {
        new() { Name = "Deep Learning Capstone", IsOnline = false, Credits = 10 },
        new() { Name = "Intro to Generative AI", IsOnline = true, Credits = 6 },
        new() { Name = "LLMs and You", IsOnline = true, Credits = 3 },
        new() { Name = "ML for Climate Change", IsOnline = false, Credits = 6 }
    };

    internal sealed class Course
    {
        public string? Name { get; set; }
        public string? Description { get; set; }
        public bool IsOnline { get; set; }
        public int Credits { get; set; }
    }
}
