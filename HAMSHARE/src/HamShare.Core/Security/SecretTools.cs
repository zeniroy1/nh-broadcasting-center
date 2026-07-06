using System.Security.Cryptography;
using System.Text;

namespace HamShare.Core.Security;

public static class SecretTools
{
    public static string CreatePin() => RandomNumberGenerator.GetInt32(0, 1_000_000).ToString("D6");

    public static string CreateAccessToken(int byteCount = 32)
        => Convert.ToBase64String(RandomNumberGenerator.GetBytes(byteCount));

    public static string HashToken(string token)
        => Convert.ToHexString(SHA256.HashData(Encoding.UTF8.GetBytes(token)));

    public static bool FixedTimeTokenEquals(string token, string expectedHash)
    {
        var actual = SHA256.HashData(Encoding.UTF8.GetBytes(token));
        try
        {
            var expected = Convert.FromHexString(expectedHash);
            return expected.Length == actual.Length && CryptographicOperations.FixedTimeEquals(actual, expected);
        }
        catch (FormatException)
        {
            return false;
        }
    }
}

