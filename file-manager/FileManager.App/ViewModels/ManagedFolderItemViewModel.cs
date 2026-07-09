using System;
using System.IO;
using CommunityToolkit.Mvvm.ComponentModel;
using FileManager.App.Domain.Entities;

namespace FileManager.App.ViewModels;

public partial class ManagedFolderItemViewModel : ObservableObject
{
    public ManagedFolderItemViewModel(Guid id, string folderPath, string? displayName, DateTimeOffset? lastScanUtc)
    {
        Id = id;
        FolderPath = folderPath;
        DisplayName = displayName;
        LastScanUtc = lastScanUtc;
    }

    public Guid Id { get; }

    [ObservableProperty]
    private string _folderPath;

    [ObservableProperty]
    private string? _displayName;

    [ObservableProperty]
    private DateTimeOffset? _lastScanUtc;

    public string DisplayLabel => string.IsNullOrWhiteSpace(DisplayName)
        ? System.IO.Path.GetFileName(FolderPath.TrimEnd(System.IO.Path.DirectorySeparatorChar, System.IO.Path.AltDirectorySeparatorChar))
        : DisplayName;

    public string LastScanDisplay => LastScanUtc.HasValue
        ? $"Last scan: {LastScanUtc.Value.LocalDateTime:g}"
        : "Never scanned";

    public static ManagedFolderItemViewModel FromEntity(ManagedFolder folder)
        => new(folder.Id, folder.Path, folder.DisplayName, folder.LastScanUtc);

    public void UpdateFrom(ManagedFolder folder)
    {
        if (folder.Id != Id)
        {
            throw new InvalidOperationException("Cannot update from a different folder.");
        }

        FolderPath = folder.Path;
        DisplayName = folder.DisplayName;
        LastScanUtc = folder.LastScanUtc;
    }
}

