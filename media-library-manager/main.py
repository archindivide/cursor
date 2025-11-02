#!/usr/bin/env python3
"""Main CLI entry point for Media Library Manager."""

import click
import sys
from pathlib import Path
from tqdm import tqdm

from media_manager import Config, setup_logger
from media_manager.core.scanner import MediaScanner
from media_manager.core.hasher import FileHasher
from media_manager.core.duplicate_finder import DuplicateFinder
from media_manager.organizer.file_organizer import FileOrganizer
from media_manager.utils.file_utils import format_file_size
from media_manager.utils.plan_manager import PlanManager


@click.group()
@click.option('--config', type=click.Path(exists=True), help='Path to configuration file')
@click.option('--log-level', default='INFO', help='Logging level (DEBUG, INFO, WARNING, ERROR)')
@click.pass_context
def cli(ctx, config, log_level):
    """Media Library Manager - Organize and maintain your media library."""
    ctx.ensure_object(dict)
    
    # Load configuration
    try:
        ctx.obj['config'] = Config(config_path=config)
    except FileNotFoundError as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)
    
    # Setup logging
    log_config = ctx.obj['config'].get('logging', {})
    ctx.obj['logger'] = setup_logger(
        level=log_level,
        log_file=log_config.get('file'),
        console=log_config.get('console', True)
    )


@cli.command()
@click.argument('directory', type=click.Path(exists=True))
@click.pass_context
def scan(ctx, directory):
    """Scan directory for media files."""
    logger = ctx.obj['logger']
    config = ctx.obj['config']
    
    logger.info(f"Scanning directory: {directory}")
    
    scanner = MediaScanner(config, logger)
    files = scanner.scan_directory(directory, progress_bar=tqdm(desc="Scanning files", unit="file", ncols=100))
    
    click.echo(f"\nFound {len(files)} media files")
    
    # Show file types breakdown
    from collections import Counter
    types = Counter(scanner._detect_media_type(f) for f in files)
    
    for media_type, count in types.items():
        click.echo(f"  {media_type}: {count}")


@cli.command()
@click.argument('directory', type=click.Path(exists=True))
@click.option('--quick', is_flag=True, help='Quick mode: use filename and size instead of hashing (faster but less accurate)')
@click.option('--save-plan', type=click.Path(), help='Save detection results to a plan file for later use')
@click.pass_context
def detect_duplicates(ctx, directory, quick, save_plan):
    """Detect duplicate files in directory."""
    logger = ctx.obj['logger']
    config = ctx.obj['config']
    
    mode = "quick (filename + size)" if quick else "hash-based"
    logger.info(f"Scanning for duplicates in: {directory} (mode: {mode})")
    
    # Scan for media files
    scanner = MediaScanner(config, logger)
    files = scanner.scan_directory(directory, progress_bar=tqdm(desc="Scanning files", unit="file", ncols=100))
    
    if not files:
        click.echo("No media files found.")
        return
    
    # Find duplicates with progress bar
    hasher = FileHasher(config, logger)
    if quick:
        duplicates = hasher.find_quick_duplicates(files, progress_bar=tqdm(total=len(files), desc="Checking files", unit="file", ncols=100))
        click.echo("\n[WARNING] Quick mode: Detection based on filename and size only (may have false positives)")
    else:
        duplicates = hasher.find_hash_duplicates(files, progress_bar=tqdm(total=len(files), desc="Hashing files", unit="file", ncols=100))
    
    if not duplicates:
        click.echo("\nNo duplicates found!")
        return
    
    # Organize duplicates to determine what to keep/remove
    finder = DuplicateFinder(config, logger)
    organized = finder.organize_duplicates(duplicates)
    
    # Display results
    report = finder.format_duplicate_report(duplicates)
    click.echo(report)
    
    # Save plan if requested
    if save_plan:
        plan_manager = PlanManager(logger)
        plan_path = Path(save_plan)
        if plan_manager.save_duplicate_plan(duplicates, organized, plan_path, directory):
            click.echo(f"\nPlan saved to: {plan_path.absolute()}")
            click.echo("Use this plan file with 'remove-duplicates --plan-file' to avoid rescanning.")
        else:
            click.echo(f"\nError: Failed to save plan file to {plan_path}", err=True)
    else:
        # Save to default location
        plan_manager = PlanManager(logger)
        default_plan = plan_manager.get_default_plan_path('duplicate_removal')
        if plan_manager.save_duplicate_plan(duplicates, organized, default_plan, directory):
            click.echo(f"\nPlan automatically saved to: {default_plan.absolute()}")
            click.echo(f"Use 'remove-duplicates --plan-file {default_plan.name}' to delete duplicates without rescanning.")


@cli.command()
@click.argument('directory', type=click.Path(exists=True), required=False)
@click.option('--plan-file', type=click.Path(exists=True), help='Load duplicates from a previously saved plan file')
@click.option('--dry-run', is_flag=True, help='Show what would be removed without deleting')
@click.confirmation_option(prompt='Are you sure you want to remove duplicates?')
@click.pass_context
def remove_duplicates(ctx, directory, plan_file, dry_run):
    """Remove duplicate files. Can load from a plan file to avoid rescanning."""
    logger = ctx.obj['logger']
    config = ctx.obj['config']
    
    plan_manager = PlanManager(logger)
    organized = None
    
    # Try to load from plan file first
    if plan_file:
        logger.info(f"Loading duplicate plan from: {plan_file}")
        plan_data = plan_manager.load_duplicate_plan(Path(plan_file))
        
        if plan_data:
            organized = plan_data['organized']
            click.echo(f"\nLoaded plan created: {plan_data.get('timestamp')}")
            click.echo(f"Source directory: {plan_data.get('source_directory')}")
            
            # Count files to remove
            total_to_remove = sum(len(info['remove']) for info in organized.values())
            click.echo(f"Files in plan: {total_to_remove} duplicates to remove")
        else:
            click.echo(f"Error: Failed to load plan file: {plan_file}", err=True)
            sys.exit(1)
    
    # If no plan file, scan and find duplicates
    if not organized:
        if not directory:
            click.echo("Error: Either --plan-file or directory argument is required", err=True)
            sys.exit(1)
        
        logger.info(f"Scanning for duplicates in: {directory}")
        
        # Find duplicates with progress bars
        scanner = MediaScanner(config, logger)
        files = scanner.scan_directory(directory, progress_bar=tqdm(desc="Scanning files", unit="file", ncols=100))
        
        hasher = FileHasher(config, logger)
        duplicates = hasher.find_hash_duplicates(files, progress_bar=tqdm(total=len(files), desc="Hashing files", unit="file", ncols=100))
        
        if not duplicates:
            click.echo("No duplicates found.")
            return
        
        # Organize duplicates
        finder = DuplicateFinder(config, logger)
        organized = finder.organize_duplicates(duplicates)
    
    if not organized:
        click.echo("No duplicates to remove.")
        return
    
    if dry_run:
        click.echo("\nDRY RUN MODE - No files will be deleted\n")
    
    # Count total files to remove
    total_to_remove = sum(len(info['remove']) for info in organized.values())
    
    # Remove duplicates with progress bar
    removed_count = 0
    saved_space = 0
    errors = 0
    
    remove_progress = tqdm(total=total_to_remove, desc="Removing duplicates", unit="file", ncols=100)
    
    for file_hash, info in organized.items():
        for file_path in info['remove']:
            # Verify file still exists before attempting to remove
            if not file_path.exists():
                logger.warning(f"File no longer exists, skipping: {file_path}")
                remove_progress.update(1)
                continue
            
            if not dry_run:
                try:
                    file_size = file_path.stat().st_size
                    file_path.unlink()
                    logger.info(f"Removed duplicate: {file_path}")
                    saved_space += file_size
                except OSError as e:
                    logger.error(f"Failed to remove {file_path}: {e}")
                    errors += 1
                    remove_progress.update(1)
                    continue
            
            removed_count += 1
            if dry_run:
                # In dry run, get size for preview
                try:
                    saved_space += file_path.stat().st_size
                except OSError:
                    pass
            remove_progress.update(1)
    
    remove_progress.close()
    
    action = "Would remove" if dry_run else "Removed"
    click.echo(f"\n{action} {removed_count} duplicate files")
    if errors > 0:
        click.echo(f"Errors encountered: {errors} files could not be removed")
    click.echo(f"Saved {format_file_size(saved_space)} of disk space")


@cli.command()
@click.argument('directory', type=click.Path(exists=True))
@click.option('--dry-run', is_flag=True, help='Preview changes without making them')
@click.option('--output-dir', type=click.Path(), help='Base output directory for organized files (overrides config)')
@click.option('--movies-dir', type=click.Path(), help='Output directory for movies')
@click.option('--tv-shows-dir', type=click.Path(), help='Output directory for TV shows')
@click.option('--music-dir', type=click.Path(), help='Output directory for music')
@click.option('--photos-dir', type=click.Path(), help='Output directory for photos')
@click.pass_context
def organize(ctx, directory, dry_run, output_dir, movies_dir, tv_shows_dir, music_dir, photos_dir):
    """Organize and standardize file names and structure."""
    logger = ctx.obj['logger']
    config = ctx.obj['config']
    
    logger.info(f"Organizing files in: {directory}")
    
    # Scan for media files with progress bar
    scanner = MediaScanner(config, logger)
    files = scanner.scan_directory(directory, progress_bar=tqdm(desc="Scanning files", unit="file", ncols=100))
    
    if not files:
        click.echo("No media files found.")
        return
    
    # Create organizer
    organizer = FileOrganizer(config, logger)
    
    # Handle per-category output directories from CLI
    if movies_dir or tv_shows_dir or music_dir or photos_dir:
        # Update config temporarily for this run
        output_dirs = config.get('organization.output_directories', {}).copy()
        if movies_dir:
            output_dirs['movies'] = movies_dir
        if tv_shows_dir:
            output_dirs['tv_shows'] = tv_shows_dir
        if music_dir:
            output_dirs['music'] = music_dir
        if photos_dir:
            output_dirs['photos'] = photos_dir
        config.set('organization.output_directories', output_dirs)
    
    # Set base output directory (if specified, overrides config)
    if output_dir:
        config.set('organization.output_directory', output_dir)
    
    # Display output directories
    if dry_run:
        click.echo("\n=== DRY RUN MODE - No files will be modified ===\n")
        
        output_dirs = config.get('organization.output_directories', {})
        default_output = Path(config.get('organization.output_directory', 'organized_media'))
        
        click.echo("Output directories:")
        for category in ['movies', 'tv_shows', 'music', 'photos']:
            cat_dir = output_dirs.get(category, '')
            if cat_dir and cat_dir.strip():
                click.echo(f"  {category}: {Path(cat_dir).absolute()}")
            else:
                click.echo(f"  {category}: {default_output.absolute() / category}")
    
    # Plan and show changes with progress bar
    changed_count = 0
    total_count = len(files)
    
    # Group by media type for better display
    media_groups = {}
    
    plan_progress = tqdm(total=total_count, desc="Planning moves", unit="file", ncols=100)
    
    for file_path in files:
        move_plan = organizer.plan_file_move(file_path, None)
        plan_progress.update(1)
        
        if move_plan['changed']:
            changed_count += 1
            media_type = move_plan['media_type']
            
            if media_type not in media_groups:
                media_groups[media_type] = []
            
            media_groups[media_type].append(move_plan)
    
    plan_progress.close()
    
    # Display organized by media type (concise format)
    for media_type, plans in media_groups.items():
        click.echo(f"\n{media_type.upper()}: {len(plans)} file(s)")
        
        # Only show details if there are few files or in verbose mode
        show_details = len(plans) <= 10
        
        if show_details:
            for plan in plans:
                click.echo(f"  {plan['from'].name} -> {plan['to'].name}")
                
                # Show associated files briefly
                if plan['associated']:
                    assoc_names = [assoc['from'].name for assoc in plan['associated']]
                    click.echo(f"    (+ {len(plan['associated'])} associated: {', '.join(assoc_names[:3])}{'...' if len(assoc_names) > 3 else ''})")
    
    # Clean up output directory structure even if no files need organizing
    output_dirs = config.get('organization.output_directories', {})
    default_output = Path(config.get('organization.output_directory', 'organized_media'))
    
    # Clean up output directories
    output_to_clean = [default_output]
    for category, cat_dir in output_dirs.items():
        if cat_dir and cat_dir.strip():
            output_to_clean.append(Path(cat_dir))
    
    for output_dir in set(output_to_clean):  # Remove duplicates
        if output_dir.exists():
            click.echo(f"\nCleaning up output directory: {output_dir}")
            cleanup_stats = organizer._cleanup_output_directory(output_dir)
            
            total_cleaned = sum(cleanup_stats.values())
            if total_cleaned > 0:
                click.echo(f"  Removed {cleanup_stats['empty_dirs_removed']} empty directory(ies)")
                if cleanup_stats['files_moved_to_unorganized'] > 0:
                    click.echo(f"  Moved {cleanup_stats['files_moved_to_unorganized']} file(s) to unorganized_files/")
                if cleanup_stats['dirs_moved_to_unorganized'] > 0:
                    click.echo(f"  Moved {cleanup_stats['dirs_moved_to_unorganized']} directory(ies) to unorganized_files/")
            else:
                click.echo("  Output directory is clean")
    
    if not changed_count:
        click.echo("\nNo files need to be organized!")
        return
    
    # Summary
    click.echo(f"\n{'='*60}")
    click.echo(f"Summary: {changed_count} of {total_count} files to organize")
    
    # Show output directories summary (only if different from default or if custom dirs set)
    output_dirs = config.get('organization.output_directories', {})
    default_output = Path(config.get('organization.output_directory', 'organized_media'))
    has_custom_dirs = any(cat_dir and cat_dir.strip() for cat_dir in output_dirs.values())
    
    if has_custom_dirs or output_dir:
        click.echo("\nOutput directories:")
        for category in ['movies', 'tv_shows', 'music', 'photos']:
            cat_dir = output_dirs.get(category, '')
            if cat_dir and cat_dir.strip():
                click.echo(f"  {category}: {Path(cat_dir).absolute()}")
            else:
                click.echo(f"  {category}: {default_output.absolute() / category}")
    click.echo(f"{'='*60}")
    
    if not dry_run:
        if not click.confirm(f"\nProceed with organizing {changed_count} files?"):
            click.echo("Cancelled.")
            return
        
        # Execute moves with progress bar
        success_count = 0
        move_progress = tqdm(total=changed_count, desc="Organizing files", unit="file", ncols=100)
        
        # Track all source directories for cleanup
        source_directories = set()
        
        for file_path in files:
            move_plan = organizer.plan_file_move(file_path, None)
            if move_plan['changed']:
                if organizer.execute_move(move_plan, dry_run=False):
                    success_count += 1
                    # Track source directory for cleanup
                    source_dir = move_plan['from'].parent
                    if source_dir.exists() and source_dir != move_plan['to'].parent:
                        source_directories.add(source_dir)
                move_progress.update(1)
        
        move_progress.close()
        
        # Clean up empty directories (only if we actually moved files)
        if source_directories:
            click.echo("\nCleaning up empty directories...")
            removed_count = organizer._cleanup_empty_directories(list(source_directories), recursive=True)
            if removed_count > 0:
                click.echo(f"Removed {removed_count} empty directory(ies)")
        
        # Clean up output directory structure again after moves
        # This ensures any new junk files created during organization are cleaned up
        output_dirs = config.get('organization.output_directories', {})
        default_output = Path(config.get('organization.output_directory', 'organized_media'))
        
        # Clean up output directories
        output_to_clean = [default_output]
        for category, cat_dir in output_dirs.items():
            if cat_dir and cat_dir.strip():
                output_to_clean.append(Path(cat_dir))
        
        for output_dir in set(output_to_clean):  # Remove duplicates
            if output_dir.exists():
                click.echo(f"\nFinal cleanup of output directory: {output_dir}")
                cleanup_stats = organizer._cleanup_output_directory(output_dir)
                
                total_cleaned = sum(cleanup_stats.values())
                if total_cleaned > 0:
                    click.echo(f"  Removed {cleanup_stats['empty_dirs_removed']} empty directory(ies)")
                    if cleanup_stats['files_moved_to_unorganized'] > 0:
                        click.echo(f"  Moved {cleanup_stats['files_moved_to_unorganized']} file(s) to unorganized_files/")
                    if cleanup_stats['dirs_moved_to_unorganized'] > 0:
                        click.echo(f"  Moved {cleanup_stats['dirs_moved_to_unorganized']} directory(ies) to unorganized_files/")
                else:
                    click.echo("  Output directory is clean")
        
        click.echo(f"\nSuccessfully organized {success_count} files!")
        
        # Show output directories if custom paths were used
        output_dirs = config.get('organization.output_directories', {})
        has_custom_dirs = any(cat_dir and cat_dir.strip() for cat_dir in output_dirs.values())
        
        if has_custom_dirs or output_dir:
            default_output = Path(config.get('organization.output_directory', 'organized_media'))
            click.echo("Organized into:")
            for category in ['movies', 'tv_shows', 'music', 'photos']:
                cat_dir = output_dirs.get(category, '')
                if cat_dir and cat_dir.strip():
                    click.echo(f"  {category}: {Path(cat_dir).absolute()}")
                else:
                    click.echo(f"  {category}: {default_output.absolute() / category}")
    else:
        click.echo("\nRun without --dry-run to apply changes")


@cli.command()
@click.pass_context
def info(ctx):
    """Display configuration information."""
    config = ctx.obj['config']
    
    click.echo("Media Library Manager Configuration\n")
    click.echo("Media Paths:")
    
    paths = config.get_media_paths()
    for media_type, path_list in paths.items():
        click.echo(f"  {media_type}: {path_list if path_list else '(not configured)'}")
    
    click.echo(f"\nSupported Extensions: {len(config.get_all_extensions())}")


if __name__ == '__main__':
    cli()
