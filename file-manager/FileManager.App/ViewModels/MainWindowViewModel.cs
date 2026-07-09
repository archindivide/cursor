using System;
using System.Collections.ObjectModel;
using System.Linq;
using System.Threading;
using System.Threading.Tasks;
using CommunityToolkit.Mvvm.ComponentModel;
using CommunityToolkit.Mvvm.Input;
using FileManager.App.Application.Abstractions;
using FileManager.App.Domain.Entities;
using Microsoft.Extensions.Logging;

namespace FileManager.App.ViewModels;

public partial class MainWindowViewModel : ViewModelBase
{
    private readonly IFolderRegistryService _folderRegistryService;
    private readonly ILogger<MainWindowViewModel> _logger;

    public MainWindowViewModel(
        IFolderRegistryService folderRegistryService,
        ILogger<MainWindowViewModel> logger)
    {
        _folderRegistryService = folderRegistryService;
        _logger = logger;

        RefreshCommand = new AsyncRelayCommand(LoadAsync);
        RemoveFolderCommand = new AsyncRelayCommand<ManagedFolderItemViewModel>(RemoveFolderAsync);
    }

    public ObservableCollection<ManagedFolderItemViewModel> Folders { get; } = new();

    public IAsyncRelayCommand RefreshCommand { get; }

    public IAsyncRelayCommand<ManagedFolderItemViewModel> RemoveFolderCommand { get; }

    [ObservableProperty]
    private bool _isBusy;

    public bool IsIdle => !IsBusy;

    [ObservableProperty]
    private string? _statusMessage;

    partial void OnIsBusyChanged(bool value)
    {
        OnPropertyChanged(nameof(IsIdle));
    }

    public async Task LoadAsync(CancellationToken cancellationToken = default)
    {
        if (IsBusy)
        {
            return;
        }

        try
        {
            IsBusy = true;
            StatusMessage = "Loading folders...";

            var folders = await _folderRegistryService.GetFoldersAsync(cancellationToken);

            Folders.Clear();
            foreach (var folder in folders.Select(ManagedFolderItemViewModel.FromEntity))
            {
                Folders.Add(folder);
            }

            StatusMessage = Folders.Count == 0
                ? "No folders registered yet."
                : $"Loaded {Folders.Count} folder(s).";
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Failed to load folders.");
            StatusMessage = "Failed to load folders.";
        }
        finally
        {
            IsBusy = false;
        }
    }

    public async Task AddFolderAsync(string folderPath, CancellationToken cancellationToken = default)
    {
        if (IsBusy)
        {
            return;
        }

        try
        {
            IsBusy = true;
            StatusMessage = "Adding folder...";

            var folder = await _folderRegistryService.AddFolderAsync(folderPath, cancellationToken: cancellationToken);

            var existing = Folders.FirstOrDefault(x => x.Id == folder.Id);
            if (existing is null)
            {
                Folders.Add(ManagedFolderItemViewModel.FromEntity(folder));
            }
            else
            {
                existing.UpdateFrom(folder);
            }

            StatusMessage = $"Registered folder: {folder.Path}";
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Could not add folder {FolderPath}", folderPath);
            StatusMessage = ex.Message;
        }
        finally
        {
            IsBusy = false;
        }
    }

    private async Task RemoveFolderAsync(ManagedFolderItemViewModel? item)
    {
        if (item is null || IsBusy)
        {
            return;
        }

        try
        {
            IsBusy = true;
            StatusMessage = "Removing folder...";

            await _folderRegistryService.RemoveFolderAsync(item.Id);

            Folders.Remove(item);
            StatusMessage = $"Removed folder: {item.FolderPath}";
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Failed to remove folder {FolderId}", item.Id);
            StatusMessage = "Failed to remove folder.";
        }
        finally
        {
            IsBusy = false;
        }
    }
}
