using System.Text;

namespace HamShare.Core.Storage;

public static class SafeFileName
{
    private const int MaxLength = 180;

    public static string Normalize(string? name)
    {
        if (string.IsNullOrWhiteSpace(name))
            return "unnamed-file";

        var leaf = Path.GetFileName(name.Trim()).Normalize(NormalizationForm.FormC);
        var invalid = Path.GetInvalidFileNameChars().ToHashSet();
        var chars = leaf.Select(c => invalid.Contains(c) || char.IsControl(c) ? '_' : c).ToArray();
        var safe = new string(chars).Trim().TrimEnd('.');

        if (safe is "." or ".." or "")
            safe = "unnamed-file";

        if (IsReservedWindowsName(Path.GetFileNameWithoutExtension(safe)))
            safe = "_" + safe;

        if (safe.Length > MaxLength)
        {
            var extension = Path.GetExtension(safe);
            var baseLength = Math.Max(1, MaxLength - extension.Length);
            safe = safe[..baseLength] + extension;
        }

        return safe;
    }

    public static string CreateUniquePath(string directory, string requestedName)
    {
        Directory.CreateDirectory(directory);
        var safeName = Normalize(requestedName);
        var candidate = Path.Combine(directory, safeName);
        if (!File.Exists(candidate) && !File.Exists(candidate + ".partial"))
            return candidate;

        var stem = Path.GetFileNameWithoutExtension(safeName);
        var extension = Path.GetExtension(safeName);
        for (var suffix = 1; suffix < 100_000; suffix++)
        {
            candidate = Path.Combine(directory, $"{stem} ({suffix}){extension}");
            if (!File.Exists(candidate) && !File.Exists(candidate + ".partial"))
                return candidate;
        }

        throw new IOException("고유한 파일 이름을 만들 수 없습니다.");
    }

    private static bool IsReservedWindowsName(string value)
    {
        var upper = value.ToUpperInvariant();
        return upper is "CON" or "PRN" or "AUX" or "NUL"
            || (upper.Length == 4 && (upper.StartsWith("COM") || upper.StartsWith("LPT"))
                && upper[3] is >= '1' and <= '9');
    }
}

