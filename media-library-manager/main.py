#!/usr/bin/env python3
"""Main CLI entry point for Media Library Manager."""

import click
import sys
from pathlib import Path

from media_manager import Config, setup_logger
from media_manager.core.scanner import MediaScanner
from media_manager.core.hasher import FileHasher
from media_manager.core.duplicate_finder import DuplicateFinder
from media_manager.organizer.file_organizer import FileOrganizer
from media_manager.utils.file_utils import format_file_size


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
    files = scanner.scan_directory(directory)
    
    click.echo(f"\nFound {len(files)} media files")
    
    # Show file types breakdown
    from collections import Counter
    types = Counter(scanner._detect_media_type(f) for f in files)
    
    for media_type, count in types.items():
        click.echo(f"  {media_type}: {count}")


@cli.command()
@click.argument('directory', type=click.Path(exists=True))
@click.pass_context
def detect_duplicates(ctx, directory):
    """Detect duplicate files in directory."""
    logger = ctx.obj['logger']
    config = ctx.obj['config']
    
    logger.info(f"Scanning for duplicates in: {directory}")
    
    # Scan for media files
    scanner = MediaScanner(config, logger)
    files = scanner.scan_directory(directory)
    
    if not files:
        click.echo("No media files found.")
        return
    
    # Find duplicates
    hasher = FileHasher(config, logger)
    duplicates = hasher.find_hash_duplicates(files)
    
    if not duplicates:
        click.echo("\nNo duplicates found!")
        return
    
    # Display results
    finder = DuplicateFinder(config, logger)
    report = finder.format_duplicate_report(duplicates)
    click.echo(report)


@cli.command()
@click.argument('directory', type=click.Path(exists=True))
@click.option('--dry-run', is_flag=True, help='Show what would be removed without deleting')
@click.confirmation_option(prompt='Are you sure you want to remove duplicates?')
@click.pass_context
def remove_duplicates(ctx, directory, dry_run):
    """Remove duplicate files."""
    logger = ctx.obj['logger']
    config = ctx.obj['config']
    
    logger.info(f"Removing duplicates in: {directory}")
    
    # Find duplicates
    scanner = MediaScanner(config, logger)
    files = scanner.scan_directory(directory)
    
    hasher = FileHasher(config, logger)
    duplicates = hasher.find_hash_duplicates(files)
    
    if not duplicates:
        click.echo("No duplicates found.")
        return
    
    # Organize duplicates
    finder = DuplicateFinder(config, logger)
    organized = finder.organize_duplicates(duplicates)
    
    if dry_run:
        click.echo("\nDRY RUN MODE - No files will be deleted\n")
    
    # Remove duplicates
    removed_count = 0
    saved_space = 0
    
    for file_hash, info in organized.items():
        for file_path in info['remove']:
            if not dry_run:
                try:
                    file_path.unlink()
                    logger.info(f"Removed duplicate: {file_path}")
                except OSError as e:
                    logger.error(f"Failed to remove {file_path}: {e}")
                    continue
            
            removed_count += 1
            saved_space += file_path.stat().st_size
    
    action = "Would remove" if dry_run else "Removed"
    click.echo(f"\n{action} {removed_count} duplicate files")
    click.echo(f"Saved {format_file_size(saved_space)} of disk space")


@cli.command()
@click.argument('directory', type=click.Path(exists=True))
@click.option('--dry-run', is_flag=True, help='Preview changes without making them')
@click.option('--output-dir', type=click.Path(), help='Output directory for organized files')
@click.pass_context
def organize(ctx, directory, dry_run, output_dir):
    """Organize and standardize file names and structure."""
    logger = ctx.obj['logger']
    config = ctx.obj['config']
    
    logger.info(f"Organizing files in: {directory}")
    
    # Scan for media files
    scanner = MediaScanner(config, logger)
    files = scanner.scan_directory(directory)
    
    if not files:
        click.echo("No media files found.")
        return
    
    # Create organizer
    organizer = FileOrganizer(config, logger)
    
    # Set output directory
    if output_dir:
        output_path = Path(output_dir)
    else:
        output_path = Path(config.get('organization.output_directory', 'organized_media'))
    
    if dry_run:
        click.echo("\n=== DRY RUN MODE - No files will be modified ===\n")
        click.echo(f"Files will be organized into: {output_path.absolute()}")
    
    # Plan and show changes
    changed_count = 0
    total_count = len(files)
    
    # Group by media type for better display
    media_groups = {}
    
    for file_path in files:
        move_plan = organizer.plan_file_move(file_path, output_path)
        
        if move_plan['changed']:
            changed_count += 1
            media_type = move_plan['media_type']
            
            if media_type not in media_groups:
                media_groups[media_type] = []
            
            media_groups[media_type].append(move_plan)
    
    # Display organized by media type
    for media_type, plans in media_groups.items():
        click.echo(f"\n{media_type.upper()}:")
        click.echo("-" * 40)
        
        for plan in plans:
            click.echo(f"\n{plan['from'].name}")
            click.echo(f"  -> {plan['to']}")
            
            # Show associated files
            if plan['associated']:
                click.echo("  Associated files:")
                for assoc in plan['associated']:
                    click.echo(f"    {assoc['from'].name} -> {assoc['to']}")
    
    if not changed_count:
        click.echo("\nNo files need to be organized!")
        return
    
    click.echo(f"\n{'='*60}")
    click.echo(f"Total files: {total_count}")
    click.echo(f"Files to organize: {changed_count}")
    click.echo(f"Output directory: {output_path.absolute()}")
    click.echo(f"{'='*60}")
    
    if not dry_run:
        if not click.confirm(f"\nProceed with organizing {changed_count} files?"):
            click.echo("Cancelled.")
            return
        
        # Execute moves
        success_count = 0
        for file_path in files:
            move_plan = organizer.plan_file_move(file_path, output_path)
            if move_plan['changed']:
                if organizer.execute_move(move_plan, dry_run=False):
                    success_count += 1
        
        click.echo(f"\nSuccessfully organized {success_count} files!")
        click.echo(f"Check the organized structure in: {output_path.absolute()}")
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
