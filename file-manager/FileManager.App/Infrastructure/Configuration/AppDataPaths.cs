using System;
using System.IO;

namespace FileManager.App.Infrastructure.Configuration;

public sealed class AppDataPaths
{
    private AppDataPaths(string rootPath)
    {
        Root = rootPath;
        DatabasePath = Path.Combine(Root, "filemanager.db");
    }

    public string Root { get; }

    public string DatabasePath { get; }

    public static AppDataPaths Create(string applicationName)
    {
        var root = TryGetKnownFolder(Environment.SpecialFolder.LocalApplicationData)
                   ?? TryGetKnownFolder(Environment.SpecialFolder.ApplicationData)
                   ?? Path.Combine(Environment.GetFolderPath(Environment.SpecialFolder.UserProfile), $".{applicationName.ToLowerInvariant()}");

        root = Path.Combine(root, applicationName);

        Directory.CreateDirectory(root);

        return new AppDataPaths(root);
    }

    private static string? TryGetKnownFolder(Environment.SpecialFolder folder)
    {
        try
        {
            var path = Environment.GetFolderPath(folder);
            return string.IsNullOrWhiteSpace(path) ? null : path;
        }
        catch
        {
            return null;
        }
    }
}

