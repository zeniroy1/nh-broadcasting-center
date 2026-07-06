using System.Text.Json;
using System.IO;
using HamShare.Core.Protocol;

namespace HamShare.Receiver.Services;

public sealed class ReceiverSettings
{
    public string DeviceId { get; set; } = Guid.NewGuid().ToString("N");
    public string DeviceName { get; set; } = Environment.MachineName;
    public int Port { get; set; } = ProtocolConstants.DefaultPort;
    public string ReceiveDirectory { get; set; } = DefaultReceiveDirectory();

    private static string DefaultReceiveDirectory()
    {
        const string preferred = @"D:\codding\HAMSHARE\Received";
        if (Directory.Exists(@"D:\codding\HAMSHARE")) return preferred;
        return Path.Combine(Environment.GetFolderPath(Environment.SpecialFolder.MyPictures), "HAMSHARE");
    }
}

public sealed class SettingsStore
{
    private static readonly JsonSerializerOptions JsonOptions = new() { WriteIndented = true };
    private readonly string _directory = Path.Combine(
        Environment.GetFolderPath(Environment.SpecialFolder.LocalApplicationData), "HAMSHARE");
    private string FilePath => Path.Combine(_directory, "settings.json");

    public ReceiverSettings Load()
    {
        try
        {
            if (File.Exists(FilePath))
                return JsonSerializer.Deserialize<ReceiverSettings>(File.ReadAllText(FilePath), JsonOptions) ?? new ReceiverSettings();
        }
        catch { /* 손상된 설정은 기본값으로 복구 */ }
        return new ReceiverSettings();
    }

    public void Save(ReceiverSettings settings)
    {
        Directory.CreateDirectory(_directory);
        File.WriteAllText(FilePath, JsonSerializer.Serialize(settings, JsonOptions));
    }
}
