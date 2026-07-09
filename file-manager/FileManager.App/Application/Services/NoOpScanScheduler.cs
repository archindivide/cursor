using System;
using System.Threading;
using System.Threading.Tasks;
using FileManager.App.Application.Abstractions;
using Microsoft.Extensions.Logging;

namespace FileManager.App.Application.Services;

public class NoOpScanScheduler : IScanScheduler
{
    private readonly ILogger<NoOpScanScheduler> _logger;

    public NoOpScanScheduler(ILogger<NoOpScanScheduler> logger)
    {
        _logger = logger;
    }

    public Task QueueScanAsync(Guid folderId, CancellationToken cancellationToken = default)
    {
        _logger.LogInformation("Scan for folder {FolderId} queued (no-op placeholder).", folderId);
        return Task.CompletedTask;
    }
}

