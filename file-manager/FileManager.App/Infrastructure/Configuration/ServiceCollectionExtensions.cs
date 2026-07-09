using FileManager.App.Application.Abstractions;
using FileManager.App.Application.Services;
using FileManager.App.Infrastructure.Data;
using FileManager.App.Infrastructure.Initialization;
using Microsoft.EntityFrameworkCore;
using Microsoft.Extensions.Configuration;
using Microsoft.Extensions.DependencyInjection;

namespace FileManager.App.Infrastructure.Configuration;

public static class ServiceCollectionExtensions
{
    private const string ConnectionStringKey = "Database:ConnectionString";

    public static IServiceCollection AddApplicationCore(this IServiceCollection services, IConfiguration configuration)
    {
        services.AddSingleton(provider => AppDataPaths.Create("FileManager"));

        services.AddDbContextFactory<FileManagerDbContext>((provider, options) =>
        {
            var paths = provider.GetRequiredService<AppDataPaths>();
            var configuredConnection = configuration[ConnectionStringKey];
            var connectionString = string.IsNullOrWhiteSpace(configuredConnection)
                ? $"Data Source={paths.DatabasePath}"
                : configuredConnection;

            options.UseSqlite(connectionString);
        });

        services.AddSingleton<DatabaseInitializer>();

        services.AddScoped<IFolderRegistryService, FolderRegistryService>();
        services.AddSingleton<IScanScheduler, NoOpScanScheduler>();

        return services;
    }
}

