using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Threading;
using System.Threading.Tasks;
using FileManager.App.Application.Abstractions;
using FileManager.App.Domain.Entities;
using FileManager.App.Infrastructure.Data;
using Microsoft.EntityFrameworkCore;
using Microsoft.Extensions.Logging;

namespace FileManager.App.Application.Services;

public class FolderRegistryService : IFolderRegistryService
{
    private readonly IDbContextFactory<FileManagerDbContext> _dbContextFactory;
    private readonly IScanScheduler _scanScheduler;
    private readonly ILogger<FolderRegistryService> _logger;

    public FolderRegistryService(
        IDbContextFactory<FileManagerDbContext> dbContextFactory,
        IScanScheduler scanScheduler,
        ILogger<FolderRegistryService> logger)
    {
        _dbContextFactory = dbContextFactory;
        _scanScheduler = scanScheduler;
        _logger = logger;
    }

    public async Task<IReadOnlyList<ManagedFolder>> GetFoldersAsync(CancellationToken cancellationToken = default)
    {
        await using var context = await _dbContextFactory.CreateDbContextAsync(cancellationToken);
        var items = await context.ManagedFolders
            .OrderBy(x => x.DisplayName ?? x.Path)
            .AsNoTracking()
            .ToListAsync(cancellationToken);

        return items;
    }

    public async Task<ManagedFolder> AddFolderAsync(string folderPath, string? displayName = null, CancellationToken cancellationToken = default)
    {
        if (string.IsNullOrWhiteSpace(folderPath))
        {
            throw new ArgumentException("Folder path must be provided.", nameof(folderPath));
        }

        if (!Directory.Exists(folderPath))
        {
            throw new DirectoryNotFoundException($"The folder '{folderPath}' could not be found.");
        }

        var normalizedPath = Path.GetFullPath(folderPath.Trim());

        await using var context = await _dbContextFactory.CreateDbContextAsync(cancellationToken);

        var existing = await context.ManagedFolders
            .AsNoTracking()
            .FirstOrDefaultAsync(x => x.Path == normalizedPath, cancellationToken);

        if (existing is not null)
        {
            _logger.LogInformation("Folder {Path} is already registered.", normalizedPath);
            return existing;
        }

        var folder = new ManagedFolder
        {
            Path = normalizedPath,
            DisplayName = string.IsNullOrWhiteSpace(displayName) ? null : displayName.Trim(),
            CreatedUtc = DateTimeOffset.UtcNow,
            IsActive = true
        };

        context.ManagedFolders.Add(folder);
        await context.SaveChangesAsync(cancellationToken);

        _logger.LogInformation("Registered folder {Path}", normalizedPath);

        await _scanScheduler.QueueScanAsync(folder.Id, cancellationToken);

        return folder;
    }

    public async Task RemoveFolderAsync(Guid folderId, CancellationToken cancellationToken = default)
    {
        await using var context = await _dbContextFactory.CreateDbContextAsync(cancellationToken);

        var folder = await context.ManagedFolders.FirstOrDefaultAsync(x => x.Id == folderId, cancellationToken);

        if (folder is null)
        {
            return;
        }

        context.ManagedFolders.Remove(folder);
        await context.SaveChangesAsync(cancellationToken);

        _logger.LogInformation("Removed folder {FolderId}", folderId);
    }
}

