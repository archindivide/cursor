using System;
using System.Threading;
using System.Threading.Tasks;

namespace FileManager.App.Application.Abstractions;

public interface IScanScheduler
{
    Task QueueScanAsync(Guid folderId, CancellationToken cancellationToken = default);
}

