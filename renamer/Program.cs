using System;
using System.IO;
using System.Text.RegularExpressions;

class Program
{
    static bool MANUAL_MODE = false;
    static bool TEST_MODE = false;
    static bool SIMPLIFY_FOLDER_STRUCTURE = false;
    static string[] REMOVE_SYMBOLS = { " ", "_", "-", "|", ":", ";", ",", "~", "`", "@", ")", "(", "[", "]" };
    static string[] ACCEPTABLE_NAME_REGEX = ["^S[0-9]{2,3}E[0-9]{2,3}"];
    static string ORIGINAL_FOLDER_PATH = "";
    static void Main(string[] args)
    {

        // Argument parser for -t or -test as testFolderPath, and a separate folderPath variable
        ORIGINAL_FOLDER_PATH = Directory.GetCurrentDirectory();

        for (int i = 0; i < args.Length; i++)
        {
            if (args[i] == "-h" || args[i] == "--help")
            {
                Console.WriteLine("Usage: Renamer [folderPath] [options]");
                Console.WriteLine();
                Console.WriteLine("Options:");
                Console.WriteLine("  folderPath           Path of the folder to process. Defaults to current directory if not specified.");
                Console.WriteLine("  -t, --test           Enable test mode.");
                Console.WriteLine("  -m, --manual         Enable manual mode.");
                Console.WriteLine("  -s, --simplify       Simplify folder structure on transformation.");
                Console.WriteLine("  -h, --help           Display this help message.");
                return;
            }
            else if (args[i] == "-t" || args[i] == "--test")
            {
                TEST_MODE = true;
            }
            else if (args[i] == "-m" || args[i] == "--manual")
            {
                MANUAL_MODE = true;
            }
            else if (args[i] == "-s" || args[i] == "--simplify")
            {
                SIMPLIFY_FOLDER_STRUCTURE = true;
            }
            else if (!args[i].StartsWith("-") && ORIGINAL_FOLDER_PATH == Directory.GetCurrentDirectory())
            {
                // set folderPath only if it's not already set by a non-default value
                ORIGINAL_FOLDER_PATH = args[i];
            }
        }

        if (!Directory.Exists(ORIGINAL_FOLDER_PATH))
        {
            Console.WriteLine($"Error: The folder '{ORIGINAL_FOLDER_PATH}' does not exist.");
            return;
        }

        Console.WriteLine($"Recursively looping through files in: {ORIGINAL_FOLDER_PATH}");
        Console.WriteLine(new string('-', 60));

        int fileCount = 0;
        int folderCount = 0;

        try
        {
            // Recursively loop through all files
            LoopThroughFiles(ORIGINAL_FOLDER_PATH, ref fileCount, ref folderCount);
        }
        catch (Exception ex)
        {
            Console.WriteLine($"Error: {ex.Message}");
            return;
        }

        Console.WriteLine(new string('-', 60));
        Console.WriteLine($"Total files found: {fileCount}");
        Console.WriteLine($"Total folders processed: {folderCount}");
    }

    static void LoopThroughFiles(string folderPath, ref int fileCount, ref int folderCount)
    {
        try
        {
            // Process all files in the current directory
            string[] files = Directory.GetFiles(folderPath);
            foreach (string file in files)
            {
                fileCount++;
                FileInfo fileInfo = new FileInfo(file);
                /* Console.WriteLine($"File: {file}");
                Console.WriteLine($"  Size: {fileInfo.Length:N0} bytes");
                Console.WriteLine($"  Modified: {fileInfo.LastWriteTime}");
                Console.WriteLine(); */
                TransformFile(fileInfo);
            }

            // Recursively process all subdirectories
            string[] subdirectories = Directory.GetDirectories(folderPath);
            foreach (string subdirectory in subdirectories)
            {
                folderCount++;
                //Console.WriteLine($"Entering folder: {subdirectory}");
                LoopThroughFiles(subdirectory, ref fileCount, ref folderCount);
            }

            // Clean up empty folders if simplify folder structure is enabled
            if (SIMPLIFY_FOLDER_STRUCTURE)
            {
                if (Directory.GetFiles(folderPath).Length == 0 && Directory.GetDirectories(folderPath).Length == 0)
                {
                    Console.WriteLine($"{(TEST_MODE ? "[TEST] " : "")}Deleting folder: {folderPath}");
                    if (!TEST_MODE)
                    {
                        Directory.Delete(folderPath, false);
                    }
                }
            }
        }
        catch (UnauthorizedAccessException)
        {
            Console.WriteLine($"Access denied to: {folderPath}");
        }
        catch (Exception ex)
        {
            Console.WriteLine($"Error processing {folderPath}: {ex.Message}");
        }
    }

    static bool IsAcceptableFileName(string fileName)
    {
        // Remove extension for checking
        string nameWithoutExtension = Path.GetFileNameWithoutExtension(fileName);

        // Check if the filename matches any of the acceptable regex patterns
        foreach (string pattern in ACCEPTABLE_NAME_REGEX)
        {
            Regex regex = new Regex(pattern);
            if (regex.IsMatch(nameWithoutExtension))
            {
                return true;
            }
        }

        return false;
    }

    static void TransformFile(FileInfo file)
    {
        string fileName = file.Name;

        if (IsAcceptableFileName(fileName) && !SIMPLIFY_FOLDER_STRUCTURE)
        {
            Console.WriteLine($"No transformation made for file: {fileName}");
            return;
        }

        //Attempt to extract season and episode from the filename - ex source: "SomeShit.E01.S01.SomeOtherShit.mkv"
        Regex regex = new Regex("\\D*?([Ss][0-9]{1,3})\\D*?([Ee][0-9]{1,3})\\D*?");
        Match match = regex.Match(fileName);
        string trySeason = "";
        string tryEpisode = "";
        if (match.Success)
        {
            if (TEST_MODE) Console.WriteLine("Path 1");
            trySeason = match.Groups[1].Value.ToUpper();
            tryEpisode = match.Groups[2].Value.ToUpper();
            //Console.WriteLine($"Season: {season}, Episode: {episode}");
        }
        else
        {
            //Method 2 - ex source: "SomeShit.1x01.SomeOtherShit.mkv"
            regex = new Regex("\\D?(\\d{1,2})[Xx](\\d{1,3})\\D?");
            match = regex.Match(fileName);
            if (match.Success)
            {
                if (TEST_MODE) Console.WriteLine("Path 2");
                trySeason = $"S{int.Parse(match.Groups[1].Value):00}";
                tryEpisode = $"E{int.Parse(match.Groups[2].Value):00}"; //Change to 000 for 3 digits
            }
            else
            {
                //Method 3 - ex source: "01.01 - SomeShit.mkv"
                regex = new Regex("(\\d{1,2})\\D+?(\\d{1,2})\\D*?");
                match = regex.Match(fileName);
                if (match.Success)
                {
                    if (TEST_MODE) Console.WriteLine("Path 3");
                    trySeason = $"S{int.Parse(match.Groups[1].Value):00}";
                    tryEpisode = $"E{int.Parse(match.Groups[2].Value):00}";
                }
            }
        }

        string newFileName = "";
        if (trySeason != "" && tryEpisode != "")
        {
            //Output format: S01E01.mkv
            newFileName = $"{trySeason}{tryEpisode}{file.Extension}";
        }

        //Attempt to remove unnecessary symbols from the fileName, only used if can't identify season and episode
        if (newFileName == "")
        {
            var tempFileName = fileName;
            foreach (string symbol in REMOVE_SYMBOLS)
            {
                tempFileName = tempFileName.Replace(symbol, "");
            }
            newFileName = tempFileName;
        }

        //Manual changes
        if (MANUAL_MODE && !IsAcceptableFileName(fileName))
        {
            //Usage for 0101, 1403 (SSEE) or 101, 911 (SEE)
            trySeason = "";
            tryEpisode = "";

            Regex findEpisodeRegex = new Regex("(?<=\\D)?(\\d{1,4})(?=\\D)");
            Match findEpisodeMatch = findEpisodeRegex.Match(fileName);
            if (findEpisodeMatch.Success)
            {
                //Console.WriteLine($"Match: {findEpisodeMatch.Groups[1].Value}");
                string episodeNumber = findEpisodeMatch.Groups[1].Value;

                tryEpisode = episodeNumber.Substring(episodeNumber.Length - 2, 2);
                trySeason = episodeNumber.Substring(0, episodeNumber.Length - 2);
                trySeason = $"S{int.Parse(trySeason):00}";
                tryEpisode = $"E{int.Parse(tryEpisode):00}";
            }

            /* //Usage for only episode 001, 002, 1, 2, SomeShow.01.SomeOtherShit.mkv, etc have to manually split seasons or create logic for it
            trySeason = "S01";
            tryEpisode = "";
            Regex findEpisodeRegex = new Regex("(?<=\\D)?(\\d{1,3})(?=\\D)");
            Match findEpisodeMatch = findEpisodeRegex.Match(fileName);
            if (findEpisodeMatch.Success)
            {
                //Console.WriteLine($"Match: {findEpisodeMatch.Groups[1].Value}");
                tryEpisode = $"E{int.Parse(findEpisodeMatch.Groups[1].Value):00}"; //Change to 000 for 3 digits
            } */

            /* //Custom logic for splitting seasons and episodes, ex E01-E13 = S01E01.mkv, E14-E26 = S02E01.mkv, etc
            trySeason = "";
            tryEpisode = "";
            Regex findEpisodeRegex = new Regex("(?<=\\D)?(\\d{1,3})(?=\\D)");
            Match findEpisodeMatch = findEpisodeRegex.Match(fileName);
            if (findEpisodeMatch.Success)
            {
                //Console.WriteLine($"Match: {findEpisodeMatch.Groups[1].Value}");
                int episodeNumberRaw = int.Parse(findEpisodeMatch.Groups[1].Value);
                switch (episodeNumberRaw)
                {
                    case <= 49:
                        trySeason = "S01";
                        tryEpisode = $"E{episodeNumberRaw:00}";
                        break;
                    case <= (49 + 48):
                        trySeason = "S02";
                        tryEpisode = $"E{episodeNumberRaw - 49:00}";
                        break;
                    case <= (49 + 48 + 47):
                        trySeason = "S03";
                        tryEpisode = $"E{episodeNumberRaw - 49 - 48:00}";
                        break;
                    case <= (49 + 48 + 47 + 40):
                        trySeason = "S04";
                        tryEpisode = $"E{episodeNumberRaw - 49 - 48 - 47:00}";
                        break;
                    case <= (49 + 48 + 47 + 40 + 40):
                        trySeason = "S05";
                        tryEpisode = $"E{episodeNumberRaw - 49 - 48 - 47 - 40:00}";
                        break;
                }
            } */

            //Output format: S01E01.mkv
            newFileName = $"{trySeason}{tryEpisode}{file.Extension}";
        }

        //Detect unusual characters in file name, report them
        Regex unusualCharactersRegex = new Regex("[^a-zA-Z0-9.]");
        Match unusualCharactersMatch = unusualCharactersRegex.Match(newFileName);
        if (unusualCharactersMatch.Success)
        {
            Console.WriteLine($"Unusual characters found in file name: {unusualCharactersMatch.Value}");
        }

        if (newFileName != "")
        {
            if (TEST_MODE)
                Console.WriteLine($"[TEST] {fileName} -> {newFileName}");
            else
            {
                Console.WriteLine($"Changing name from: {file.FullName}");
                Console.WriteLine($"Changing to: {newFileName}");
            }

            //Console.WriteLine($"Output path: {Path.Combine(file.DirectoryName!, newFileName)}");

            string folderPath = file.DirectoryName!;

            if (SIMPLIFY_FOLDER_STRUCTURE)
            {
                //Simplify folder structure on transformation (move file up one directory)
                string? parent = Path.GetDirectoryName(folderPath.TrimEnd(Path.DirectorySeparatorChar, Path.AltDirectorySeparatorChar));
                if (parent != null)
                    folderPath = parent;
                //if folder path is contained in the original folder path, that means the folder either matches or is a parent directory
                //We don't want the application to impact anything not in the parent directory, so that is the top level

                //Console.WriteLine($"folderPath = {folderPath}, ORIGINAL_FOLDER_PATH = {ORIGINAL_FOLDER_PATH}");
                if (ORIGINAL_FOLDER_PATH.Contains(folderPath) && ORIGINAL_FOLDER_PATH != folderPath)
                {
                    folderPath = ORIGINAL_FOLDER_PATH;
                }
                Console.WriteLine($"{(TEST_MODE ? "[TEST] " : "")}Changing folder path to: {folderPath}");
            }

            if (!TEST_MODE)
            {
                file.MoveTo(Path.Combine(folderPath, newFileName), overwrite: true);
            }
        }
        else
        {
            Console.WriteLine($"No transformation made for file: {file.FullName}");
        }
    }
}


