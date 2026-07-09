using System;
using System.Collections.Generic;

namespace FileManager.App.Domain.Entities;

public class ManagedFile
{
    public Guid Id { get; set; } = Guid.NewGuid();

    public Guid FolderId { get; set; }

    public ManagedFolder? Folder { get; set; }

    public string RelativePath { get; set; } = string.Empty;

    public string FileName { get; set; } = string.Empty;

    public string Extension { get; set; } = string.Empty;

    public long SizeBytes { get; set; }

    public DateTimeOffset ModifiedUtc { get; set; }

    public string? Hash { get; set; }

    public Guid? CategoryId { get; set; }

    public Category? Category { get; set; }

    public double? Confidence { get; set; }

    public ICollection<ManagedFileTag> Tags { get; set; } = new List<ManagedFileTag>();
}

