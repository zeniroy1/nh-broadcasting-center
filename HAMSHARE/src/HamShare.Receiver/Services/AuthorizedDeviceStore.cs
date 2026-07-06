using System.Text.Json;
using System.IO;
using HamShare.Core.Security;

namespace HamShare.Receiver.Services;

public sealed record AuthorizedDevice(string DeviceId, string DeviceName, string TokenHash, DateTimeOffset PairedAt);

public sealed class AuthorizedDeviceStore
{
    private static readonly JsonSerializerOptions JsonOptions = new() { WriteIndented = true };
    private readonly object _sync = new();
    private readonly string _filePath;
    private List<AuthorizedDevice> _devices;

    public AuthorizedDeviceStore(string? filePath = null)
    {
        var directory = Path.Combine(Environment.GetFolderPath(Environment.SpecialFolder.LocalApplicationData), "HAMSHARE");
        _filePath = filePath ?? Path.Combine(directory, "authorized-devices.json");
        _devices = Load();
    }

    public IReadOnlyList<AuthorizedDevice> All { get { lock (_sync) return _devices.ToArray(); } }

    public string Register(string deviceId, string deviceName)
    {
        var token = SecretTools.CreateAccessToken();
        var item = new AuthorizedDevice(deviceId, deviceName.Trim(), SecretTools.HashToken(token), DateTimeOffset.UtcNow);
        lock (_sync)
        {
            _devices.RemoveAll(device => device.DeviceId == deviceId);
            _devices.Add(item);
            Save();
        }
        return token;
    }

    public bool Validate(string deviceId, string token)
    {
        lock (_sync)
        {
            var device = _devices.FirstOrDefault(candidate => candidate.DeviceId == deviceId);
            return device is not null && SecretTools.FixedTimeTokenEquals(token, device.TokenHash);
        }
    }

    public void Remove(string deviceId)
    {
        lock (_sync)
        {
            _devices.RemoveAll(device => device.DeviceId == deviceId);
            Save();
        }
    }

    private List<AuthorizedDevice> Load()
    {
        try
        {
            return File.Exists(_filePath)
                ? JsonSerializer.Deserialize<List<AuthorizedDevice>>(File.ReadAllText(_filePath), JsonOptions) ?? []
                : [];
        }
        catch { return []; }
    }

    private void Save()
    {
        Directory.CreateDirectory(Path.GetDirectoryName(_filePath)!);
        File.WriteAllText(_filePath, JsonSerializer.Serialize(_devices, JsonOptions));
    }
}
