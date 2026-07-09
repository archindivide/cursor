using System.Threading;
using System.Threading.Tasks;
using FileManager.App.Infrastructure.Data;
using Microsoft.EntityFrameworkCore;
using Microsoft.Extensions.Logging;

namespace FileManager.App.Infrastructure.Initialization;

public class DatabaseInitializer
{
    private readonly IDbContextFactory<FileManagerDbContext> _dbContextFactory;
    private readonly ILogger<DatabaseInitializer> _logger;

    public DatabaseInitializer(
        IDbContextFactory<FileManagerDbContext> dbContextFactory,
        ILogger<DatabaseInitializer> logger)
    {
        _dbContextFactory = dbContextFactory;
        _logger = logger;
    }

    public async Task InitializeAsync(CancellationToken cancellationToken = default)
    {
        await using var context = await _dbContextFactory.CreateDbContextAsync(cancellationToken);

        _logger.LogInformation("Ensuring local database is created at {Database}", context.Database.GetConnectionString());
        await context.Database.EnsureCreatedAsync(cancellationToken);
    }
}

