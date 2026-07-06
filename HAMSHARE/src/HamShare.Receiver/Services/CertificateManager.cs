using System.Net;
using System.Security.Cryptography;
using System.Security.Cryptography.X509Certificates;

namespace HamShare.Receiver.Services;

public static class CertificateManager
{
    public static X509Certificate2 GetOrCreate(string deviceId)
    {
        var subject = $"CN=HAMSHARE-{deviceId}";
        using var store = new X509Store(StoreName.My, StoreLocation.CurrentUser);
        store.Open(OpenFlags.ReadWrite);
        var existing = store.Certificates
            .Find(X509FindType.FindBySubjectDistinguishedName, subject, false)
            .OfType<X509Certificate2>()
            .FirstOrDefault(certificate => certificate.NotAfter > DateTime.Now.AddDays(30) && certificate.HasPrivateKey);
        if (existing is not null) return existing;

        using var ephemeral = CreateEphemeral(deviceId);
        var persisted = new X509Certificate2(ephemeral.Export(X509ContentType.Pfx), (string?)null,
            X509KeyStorageFlags.PersistKeySet | X509KeyStorageFlags.UserKeySet | X509KeyStorageFlags.Exportable);
        store.Add(persisted);
        return persisted;
    }

    public static X509Certificate2 CreateEphemeral(string deviceId)
    {
        using var rsa = RSA.Create(2048);
        var subject = $"CN=HAMSHARE-{deviceId}";
        var request = new CertificateRequest(subject, rsa, HashAlgorithmName.SHA256, RSASignaturePadding.Pkcs1);
        request.CertificateExtensions.Add(new X509BasicConstraintsExtension(false, false, 0, false));
        request.CertificateExtensions.Add(new X509KeyUsageExtension(X509KeyUsageFlags.DigitalSignature | X509KeyUsageFlags.KeyEncipherment, false));
        request.CertificateExtensions.Add(new X509EnhancedKeyUsageExtension(
            new OidCollection { new Oid("1.3.6.1.5.5.7.3.1", "Server Authentication") }, false));
        request.CertificateExtensions.Add(new X509SubjectKeyIdentifierExtension(request.PublicKey, false));
        var san = new SubjectAlternativeNameBuilder();
        san.AddDnsName("hamshare.local");
        san.AddIpAddress(IPAddress.Loopback);
        san.AddIpAddress(IPAddress.IPv6Loopback);
        request.CertificateExtensions.Add(san.Build());

        using var generated = request.CreateSelfSigned(DateTimeOffset.UtcNow.AddMinutes(-5), DateTimeOffset.UtcNow.AddYears(5));
        return new X509Certificate2(generated.Export(X509ContentType.Pfx), (string?)null,
            X509KeyStorageFlags.EphemeralKeySet | X509KeyStorageFlags.Exportable);
    }

    public static string Fingerprint(X509Certificate2 certificate)
        => Convert.ToHexString(SHA256.HashData(certificate.RawData));

    public static string ShortFingerprint(X509Certificate2 certificate)
    {
        var full = Fingerprint(certificate);
        return string.Join('-', Enumerable.Range(0, 6).Select(index => full.Substring(index * 2, 2)));
    }

    public static void Remove(string deviceId)
    {
        var subject = $"CN=HAMSHARE-{deviceId}";
        using var store = new X509Store(StoreName.My, StoreLocation.CurrentUser);
        store.Open(OpenFlags.ReadWrite);
        foreach (var certificate in store.Certificates.Find(X509FindType.FindBySubjectDistinguishedName, subject, false))
            store.Remove(certificate);
    }
}
