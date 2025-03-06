// Copyright (c) Microsoft. All rights reserved.

using System.ComponentModel.DataAnnotations;
using System.ComponentModel.DataAnnotations.Schema;

#pragma warning disable CA2007, VSTHRD111 // .ConfigureAwait(false)

namespace StructuredDataConnector;

internal sealed class MyEntity
{
    [Key, DatabaseGenerated(DatabaseGeneratedOption.Identity)]
    public Guid? Id { get; set; }

    public string? Description { get; set; }

    public DateTime? DateCreated { get; set; }
}
