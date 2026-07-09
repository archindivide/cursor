using System;
using System.Collections.Generic;

namespace FileManager.App.Domain.Entities;

public class ManagedFolder
{
    public Guid Id { get; set; } = Guid.NewGuid();

    public string Path { get; set; } = string.Empty;

    public string? DisplayName { get; set; }

    public bool IsActive { get; set; } = true;

    public DateTimeOffset CreatedUtc { get; set; } = DateTimeOffset.UtcNow;

    public DateTimeOffset? LastScanUtc { get; set; }

    public ICollection<ManagedFile> Files { get; set; } = new List<ManagedFile>();

    public ICollection<ScanLog> ScanLogs { get; set; } = new List<ScanLog>();
}

