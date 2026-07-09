using FileManager.App.Domain.Entities;
using Microsoft.EntityFrameworkCore;

namespace FileManager.App.Infrastructure.Data;

public class FileManagerDbContext : DbContext
{
    public FileManagerDbContext(DbContextOptions<FileManagerDbContext> options)
        : base(options)
    {
    }

    public DbSet<ManagedFolder> ManagedFolders => Set<ManagedFolder>();

    public DbSet<ManagedFile> ManagedFiles => Set<ManagedFile>();

    public DbSet<Category> Categories => Set<Category>();

    public DbSet<Tag> Tags => Set<Tag>();

    public DbSet<ManagedFileTag> ManagedFileTags => Set<ManagedFileTag>();

    public DbSet<ScanLog> ScanLogs => Set<ScanLog>();

    protected override void OnModelCreating(ModelBuilder modelBuilder)
    {
        base.OnModelCreating(modelBuilder);

        modelBuilder.Entity<ManagedFolder>(builder =>
        {
            builder.ToTable("ManagedFolders");
            builder.HasKey(x => x.Id);
            builder.Property(x => x.Path).IsRequired();
            builder.HasIndex(x => x.Path).IsUnique();
            builder.Property(x => x.DisplayName).HasMaxLength(256);
            builder.Property(x => x.CreatedUtc).IsRequired();
        });

        modelBuilder.Entity<ManagedFile>(builder =>
        {
            builder.ToTable("ManagedFiles");
            builder.HasKey(x => x.Id);
            builder.Property(x => x.RelativePath).IsRequired();
            builder.Property(x => x.FileName).IsRequired();
            builder.Property(x => x.Extension).HasMaxLength(128);
            builder.HasOne(x => x.Folder)
                .WithMany(x => x.Files)
                .HasForeignKey(x => x.FolderId)
                .OnDelete(DeleteBehavior.Cascade);
            builder.HasOne(x => x.Category)
                .WithMany(x => x.Files)
                .HasForeignKey(x => x.CategoryId);
        });

        modelBuilder.Entity<Category>(builder =>
        {
            builder.ToTable("Categories");
            builder.HasKey(x => x.Id);
            builder.Property(x => x.Name).IsRequired().HasMaxLength(128);
        });

        modelBuilder.Entity<Tag>(builder =>
        {
            builder.ToTable("Tags");
            builder.HasKey(x => x.Id);
            builder.Property(x => x.Name).IsRequired().HasMaxLength(128);
        });

        modelBuilder.Entity<ManagedFileTag>(builder =>
        {
            builder.ToTable("ManagedFileTags");
            builder.HasKey(x => new { x.FileId, x.TagId });
            builder.HasOne(x => x.File)
                .WithMany(x => x.Tags)
                .HasForeignKey(x => x.FileId);
            builder.HasOne(x => x.Tag)
                .WithMany(x => x.Files)
                .HasForeignKey(x => x.TagId);
        });

        modelBuilder.Entity<ScanLog>(builder =>
        {
            builder.ToTable("ScanLogs");
            builder.HasKey(x => x.Id);
            builder.Property(x => x.StartedUtc).IsRequired();
            builder.HasOne(x => x.Folder)
                .WithMany(x => x.ScanLogs)
                .HasForeignKey(x => x.FolderId);
        });
    }
}

