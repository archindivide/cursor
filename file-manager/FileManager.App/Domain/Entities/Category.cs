using System;
using System.Collections.Generic;

namespace FileManager.App.Domain.Entities;

public class Category
{
    public Guid Id { get; set; } = Guid.NewGuid();

    public string Name { get; set; } = string.Empty;

    public string? Description { get; set; }

    public string? Color { get; set; }

    public ICollection<ManagedFile> Files { get; set; } = new List<ManagedFile>();
}

