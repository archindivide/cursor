## Overview

The File Manager is a cross-platform desktop application built with Avalonia (`net8.0`) that helps users curate and organize arbitrary folders on their machines. Users can register one or more folders for the application to manage; the app then scans every file in those locations, classifies them into categories, and exposes tooling to review, refine, and persist those categorizations.

## Goals

- Make it easy to register system folders for automated organization.
- Provide a fast, responsive UI on Windows, macOS, and Linux.
- Offer sensible default categorization while letting users override results.
- Persist categorizations and metadata locally via SQLite.
- Support incremental rescans so subsequent runs only process deltas.

## High-Level Architecture

| Layer | Projects / Namespaces | Responsibilities |
| --- | --- | --- |
| Presentation | `FileManager.App` | Avalonia UI, view models (CommunityToolkit MVVM), navigation, user interactions. |
| Application | `FileManager.App.Application` (namespace) | Folder registration orchestration, scan scheduling, background workers, mediating between UI and domain. |
| Domain | `FileManager.App.Domain` | Core models (`ManagedFolder`, `ManagedFile`, `Category`, `Tag`) and classification logic abstractions. |
| Infrastructure | `FileManager.App.Infrastructure` | SQLite data access (EF Core or Dapper), file system services, classification providers, platform-specific helpers. |

We keep everything in a single project for the initial iteration but use namespaces/folders to reflect the layer above, so future extraction into separate projects is straightforward.

## Key Components

- **FolderRegistryService**  
  Tracks folders under management, kicks off scans when users add/remove folders, persists state to the database.

- **ScanPipeline**  
  Coordinates file system enumeration, metadata extraction, and classification. Runs in a background task queue to keep the UI responsive. Supports cancellation and incremental scans (only reprocess files whose hash/timestamp changed since the last run).

- **ClassificationEngine**  
  Pluggable strategy interface with default heuristics (extension-based, MIME lookup, name patterns). Designed to plug in richer classifiers later (e.g., ML, LLM). Produces `ClassificationResult` objects with category suggestions and confidence scores.

- **MetadataStore**  
  Thin repository layer over SQLite to persist folders, files, categories, and audit information. Abstracts the `DbContext`/connection details away from the rest of the application.

- **SyncStatusTracker**  
  Exposes progress metrics (files processed, pending, errors) to the UI. Sends updates through an observable/event aggregator so view models stay updated.

## Data Model (Initial)

```text
ManagedFolder
  - Id (GUID)
  - Path
  - DisplayName
  - LastScanUtc
  - IsActive

ManagedFile
  - Id (GUID)
  - FolderId (FK -> ManagedFolder)
  - RelativePath
  - FileName
  - Extension
  - SizeBytes
  - ModifiedUtc
  - Hash
  - CategoryId (FK -> Category)
  - Confidence

Category
  - Id (GUID)
  - Name
  - Description
  - Color

Tag
  - Id (GUID)
  - Name

ManagedFileTag (many-to-many)
  - FileId
  - TagId

ScanLog
  - Id (GUID)
  - FolderId
  - StartedUtc
  - CompletedUtc
  - FilesProcessed
  - Errors
```

## Technology Choices

- **UI**: Avalonia MVVM for cross-platform desktop.
- **State Management**: CommunityToolkit.Mvvm for observable properties and commands.
- **Database**: SQLite + EF Core 8 with migrations. Consider `sqlite-net` for lighter footprint if needed.
- **Dependency Injection**: `Microsoft.Extensions.Hosting` with `HostApplicationBuilder` for consistent configuration, logging, and lifetime management.
- **File System**: System.IO abstractions with optional wrappers for unit testing.
- **Background Work**: `IHostedService`/`BackgroundService` hosted inside the desktop app to run scans and scheduled tasks.

## User Experience Flow

1. **Registration**: User selects folders with a system file picker; the app validates access and stores entries in SQLite.
2. **Scanning**: A background pipeline enumerates files, updates metadata, and runs classifiers. Progress appears in the UI with live updates.
3. **Categorization Review**: Files appear grouped by category with confidence indicators. Users can override categories, create custom categories/tags, and bulk apply changes.
4. **Maintenance**: Scheduled or manual rescans keep the database in sync. The app highlights new or unreviewed files.

## Next Steps

- Wire up dependency injection and hosting infrastructure within `Program.cs`.
- Implement EF Core data access layer with initial migrations.
- Scaffold view models and views for folder registration and scan dashboards.
- Build the scan pipeline with extension-based classifiers and progress reporting.
- Add unit tests for classification and metadata services.

