using System;

namespace FileManager.App.Domain.Entities;

public class ManagedFileTag
{
    public Guid FileId { get; set; }

    public ManagedFile? File { get; set; }

    public Guid TagId { get; set; }

    public Tag? Tag { get; set; }
}

