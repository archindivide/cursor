using System;

namespace FileManager.App.Domain.Entities;

public class ScanLog
{
    public Guid Id { get; set; } = Guid.NewGuid();

    public Guid FolderId { get; set; }

    public ManagedFolder? Folder { get; set; }

    public DateTimeOffset StartedUtc { get; set; }

    public DateTimeOffset? CompletedUtc { get; set; }

    public int FilesProcessed { get; set; }

    public string? Error { get; set; }
}

