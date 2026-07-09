using System;
using System.Linq;
using Avalonia.Controls;
using Avalonia;
using Avalonia.Platform.Storage;
using Avalonia.VisualTree;
using FileManager.App.ViewModels;
using Microsoft.Extensions.DependencyInjection;

namespace FileManager.App.Views;

public partial class MainWindow : Window
{
    private readonly MainWindowViewModel _viewModel;

    public MainWindow() : this(App.Services.GetRequiredService<MainWindowViewModel>())
    {
    }

    public MainWindow(MainWindowViewModel viewModel)
    {
        InitializeComponent();
        DataContext = _viewModel = viewModel;

        Opened += OnWindowOpened;
        Closed += OnWindowClosed;
    }

    private async void OnWindowOpened(object? sender, EventArgs e)
    {
        await _viewModel.LoadAsync();
    }

    private void OnWindowClosed(object? sender, EventArgs e)
    {
        Opened -= OnWindowOpened;
        Closed -= OnWindowClosed;
    }

    private async void OnAddFolderClicked(object? sender, Avalonia.Interactivity.RoutedEventArgs e)
    {
        if (_viewModel.IsBusy)
        {
            return;
        }

        var topLevel = this.GetVisualRoot() as TopLevel ?? TopLevel.GetTopLevel(this);
        if (topLevel?.StorageProvider is not { } storageProvider)
        {
            return;
        }

        var results = await storageProvider.OpenFolderPickerAsync(new FolderPickerOpenOptions
        {
            AllowMultiple = false
        });

        if (results is { Count: > 0 })
        {
            var path = results.First().Path.LocalPath;
            await _viewModel.AddFolderAsync(path);
        }
    }
}