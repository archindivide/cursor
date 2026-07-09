using System;
using System.Collections.Generic;

namespace FileManager.App.Domain.Entities;

public class Tag
{
    public Guid Id { get; set; } = Guid.NewGuid();

    public string Name { get; set; } = string.Empty;

    public ICollection<ManagedFileTag> Files { get; set; } = new List<ManagedFileTag>();
}

