using System.Security.Cryptography;
using System.Security.Authentication;
using System.Net;
using System.Net.Http.Headers;
using System.Net.Http.Json;
using System.Net.Sockets;
using System.Text.Json;
using HamShare.Core.Protocol;
using HamShare.Core.Security;
using HamShare.Core.Storage;
using HamShare.Receiver.Services;

var tests = new List<(string Name, Func<Task> Run)>
{
    ("파일명에서 경로를 제거한다", TestPathTraversal),
    ("Windows 예약 파일명을 안전하게 바꾼다", TestReservedName),
    ("중복 파일명에 번호를 붙인다", TestUniqueName),
    ("토큰을 고정 시간 비교한다", TestTokenHash),
    ("스트리밍 저장과 SHA-256을 검증한다", TestStreamingUpload),
    ("손상된 파일을 거부하고 partial을 제거한다", TestHashMismatch),
    ("HTTPS API로 등록하고 파일을 전송한다", TestReceiverApi)
};

var failed = 0;
foreach (var test in tests)
{
    try
    {
        await test.Run();
        Console.WriteLine($"[PASS] {test.Name}");
    }
    catch (Exception ex)
    {
        failed++;
        Console.WriteLine($"[FAIL] {test.Name}: {ex}");
    }
}

Console.WriteLine($"\n총 {tests.Count}개 / 성공 {tests.Count - failed}개 / 실패 {failed}개");
return failed == 0 ? 0 : 1;

static Task TestPathTraversal()
{
    Equal("photo.jpg", SafeFileName.Normalize("../../secret/photo.jpg"));
    return Task.CompletedTask;
}

static Task TestReservedName()
{
    Equal("_CON.txt", SafeFileName.Normalize("CON.txt"));
    return Task.CompletedTask;
}

static Task TestUniqueName()
{
    var root = NewTempDirectory();
    try
    {
        File.WriteAllText(Path.Combine(root, "photo.jpg"), "existing");
        Equal("photo (1).jpg", Path.GetFileName(SafeFileName.CreateUniquePath(root, "photo.jpg")));
    }
    finally { Directory.Delete(root, true); }
    return Task.CompletedTask;
}

static Task TestTokenHash()
{
    var token = SecretTools.CreateAccessToken();
    var hash = SecretTools.HashToken(token);
    True(SecretTools.FixedTimeTokenEquals(token, hash));
    True(!SecretTools.FixedTimeTokenEquals(token + "x", hash));
    return Task.CompletedTask;
}

static async Task TestStreamingUpload()
{
    var root = NewTempDirectory();
    try
    {
        var bytes = RandomNumberGenerator.GetBytes(2 * 1024 * 1024 + 31);
        var hash = Convert.ToHexString(SHA256.HashData(bytes));
        var coordinator = new TransferCoordinator(root);
        var session = coordinator.Begin(new TransferManifest("phone-1", [new FileDescriptor(0, "test.bin", bytes.Length, hash)]));
        await using var input = new MemoryStream(bytes);
        var result = await coordinator.SaveFileAsync(session.Id, 0, input);
        True(result.Completed);
        Equal(bytes.Length, checked((int)new FileInfo(Path.Combine(root, result.SavedName)).Length));
    }
    finally { Directory.Delete(root, true); }
}

static async Task TestHashMismatch()
{
    var root = NewTempDirectory();
    try
    {
        var bytes = new byte[] { 1, 2, 3, 4 };
        var coordinator = new TransferCoordinator(root);
        var session = coordinator.Begin(new TransferManifest("phone-1", [new FileDescriptor(0, "broken.bin", bytes.Length, new string('0', 64))]));
        await using var input = new MemoryStream(bytes);
        await ThrowsAsync<InvalidDataException>(() => coordinator.SaveFileAsync(session.Id, 0, input));
        True(!Directory.EnumerateFiles(root).Any());
    }
    finally { Directory.Delete(root, true); }
}

static async Task TestReceiverApi()
{
    var root = NewTempDirectory();
    var port = FreeTcpPort();
    using var certificate = CertificateManager.GetOrCreate("integration-test");
    var settings = new ReceiverSettings
    {
        DeviceId = "receiver-test",
        DeviceName = "HAMSHARE-TEST",
        Port = port,
        ReceiveDirectory = root
    };
    var pairing = new PairingManager();
    var devices = new AuthorizedDeviceStore(Path.Combine(root, "devices.json"));
    var coordinator = new TransferCoordinator(root);
    await using var server = new ReceiverServer(settings, certificate, pairing, devices, coordinator);
    await server.StartAsync();
    try
    {
        using var handler = new HttpClientHandler
        {
            ServerCertificateCustomValidationCallback = (_, _, _, _) => true,
            ClientCertificateOptions = ClientCertificateOption.Manual,
            SslProtocols = SslProtocols.Tls12
        };
        using var client = new HttpClient(handler) { BaseAddress = new Uri($"https://127.0.0.1:{port}") };
        var health = await client.GetFromJsonAsync<HealthResponse>("/api/v1/health");
        Equal("receiver-test", health?.DeviceId);

        var pairResponse = await client.PostAsJsonAsync("/api/v1/pair", new PairRequest("phone-test", "S23+ TEST", pairing.CurrentPin));
        pairResponse.EnsureSuccessStatusCode();
        var pair = await pairResponse.Content.ReadFromJsonAsync<PairResponse>();
        True(pair is not null && !string.IsNullOrWhiteSpace(pair.AccessToken));

        var bytes = RandomNumberGenerator.GetBytes(1024 * 1024 + 17);
        var hash = Convert.ToHexString(SHA256.HashData(bytes));
        var manifest = new TransferManifest("phone-test", [new FileDescriptor(0, "api-test.bin", bytes.Length, hash)]);
        using var manifestRequest = new HttpRequestMessage(HttpMethod.Post, "/api/v1/transfers")
        {
            Content = JsonContent.Create(manifest)
        };
        Authorize(manifestRequest, "phone-test", pair!.AccessToken);
        var manifestResponse = await client.SendAsync(manifestRequest);
        manifestResponse.EnsureSuccessStatusCode();
        var created = await manifestResponse.Content.ReadFromJsonAsync<TransferCreatedResponse>();
        True(created is not null);

        using var uploadRequest = new HttpRequestMessage(HttpMethod.Put, $"/api/v1/transfers/{created!.TransferId}/files/0")
        {
            Content = new ByteArrayContent(bytes)
        };
        Authorize(uploadRequest, "phone-test", pair.AccessToken);
        var uploadResponse = await client.SendAsync(uploadRequest);
        uploadResponse.EnsureSuccessStatusCode();
        var upload = await uploadResponse.Content.ReadFromJsonAsync<UploadResult>();
        True(upload?.Completed == true);
        True(File.Exists(Path.Combine(root, "api-test.bin")));
    }
    finally
    {
        await server.StopAsync();
        CertificateManager.Remove("integration-test");
        Directory.Delete(root, true);
    }
}

static string NewTempDirectory()
{
    var path = Path.Combine(Path.GetTempPath(), "hamshare-tests", Guid.NewGuid().ToString("N"));
    Directory.CreateDirectory(path);
    return path;
}

static int FreeTcpPort()
{
    var listener = new TcpListener(IPAddress.Loopback, 0);
    listener.Start();
    var port = ((IPEndPoint)listener.LocalEndpoint).Port;
    listener.Stop();
    return port;
}

static void Authorize(HttpRequestMessage request, string deviceId, string token)
{
    request.Headers.Authorization = new AuthenticationHeaderValue("Bearer", token);
    request.Headers.Add("X-HAMSHARE-DEVICE-ID", deviceId);
}

static void True(bool condition)
{
    if (!condition) throw new Exception("조건이 참이 아닙니다.");
}

static void Equal<T>(T expected, T actual)
{
    if (!EqualityComparer<T>.Default.Equals(expected, actual))
        throw new Exception($"예상: {expected}, 실제: {actual}");
}

static async Task ThrowsAsync<TException>(Func<Task> action) where TException : Exception
{
    try { await action(); }
    catch (TException) { return; }
    throw new Exception($"{typeof(TException).Name} 예외가 발생하지 않았습니다.");
}
