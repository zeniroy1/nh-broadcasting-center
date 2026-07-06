using HamShare.Core.Security;

namespace HamShare.Receiver.Services;

public sealed class PairingManager
{
    private readonly object _sync = new();
    private string _pin = SecretTools.CreatePin();
    private DateTimeOffset _expiresAt = DateTimeOffset.UtcNow.AddMinutes(10);

    public string CurrentPin { get { lock (_sync) return _pin; } }
    public DateTimeOffset ExpiresAt { get { lock (_sync) return _expiresAt; } }

    public string Refresh()
    {
        lock (_sync)
        {
            _pin = SecretTools.CreatePin();
            _expiresAt = DateTimeOffset.UtcNow.AddMinutes(10);
            return _pin;
        }
    }

    public bool TryConsume(string suppliedPin)
    {
        lock (_sync)
        {
            if (DateTimeOffset.UtcNow > _expiresAt || suppliedPin != _pin) return false;
            Refresh();
            return true;
        }
    }
}

