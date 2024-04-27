// Copyright (c) Microsoft. All rights reserved.

using System.ComponentModel.DataAnnotations;

namespace ContentSafety.Models;

public class ChatModel
{
    [Required]
    public string Message { get; set; }
}
