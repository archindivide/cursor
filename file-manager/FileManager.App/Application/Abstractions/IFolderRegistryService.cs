using System;
using System.Collections.Generic;
using System.Threading;
using System.Threading.Tasks;
using FileManager.App.Domain.Entities;

namespace FileManager.App.Application.Abstractions;

public interface IFolderRegistryService
{
    Task<IReadOnlyList<ManagedFolder>> GetFoldersAsync(CancellationToken cancellationToken = default);

    Task<ManagedFolder> AddFolderAsync(string folderPath, string? displayName = null, CancellationToken cancellationToken = default);

    Task RemoveFolderAsync(Guid folderId, CancellationToken cancellationToken = default);
}

