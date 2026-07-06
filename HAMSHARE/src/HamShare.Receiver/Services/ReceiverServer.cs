using System.Security.Cryptography.X509Certificates;
using System.Security.Authentication;
using System.IO;
using HamShare.Core.Protocol;
using HamShare.Core.Storage;
using Microsoft.AspNetCore.Builder;
using Microsoft.AspNetCore.Http;
using Microsoft.AspNetCore.Hosting;
using Microsoft.AspNetCore.Server.Kestrel.Https;
using Microsoft.Extensions.Hosting;

namespace HamShare.Receiver.Services;

public sealed class ReceiverServer : IAsyncDisposable
{
    private readonly ReceiverSettings _settings;
    private readonly X509Certificate2 _certificate;
    private readonly PairingManager _pairing;
    private readonly AuthorizedDeviceStore _devices;
    private readonly TransferCoordinator _transfers;
    private WebApplication? _application;

    public ReceiverServer(
        ReceiverSettings settings,
        X509Certificate2 certificate,
        PairingManager pairing,
        AuthorizedDeviceStore devices,
        TransferCoordinator transfers)
    {
        _settings = settings;
        _certificate = certificate;
        _pairing = pairing;
        _devices = devices;
        _transfers = transfers;
    }

    public bool IsRunning => _application is not null;
    public event EventHandler<string>? LogMessage;

    public async Task StartAsync(CancellationToken cancellationToken = default)
    {
        if (_application is not null) return;

        var options = new WebApplicationOptions
        {
            ApplicationName = typeof(ReceiverServer).Assembly.FullName,
            ContentRootPath = AppContext.BaseDirectory,
            EnvironmentName = Environments.Production
        };
        var builder = WebApplication.CreateBuilder(options);
        builder.WebHost.ConfigureKestrel(server =>
        {
            server.Limits.MaxRequestBodySize = ProtocolConstants.MaxTransferBytes;
            server.ListenAnyIP(_settings.Port, endpoint => endpoint.UseHttps(https =>
            {
                https.ServerCertificate = _certificate;
                https.ClientCertificateMode = ClientCertificateMode.NoCertificate;
                https.SslProtocols = SslProtocols.Tls12 | SslProtocols.Tls13;
            }));
        });
        var app = builder.Build();

        app.MapGet("/api/v1/health", () => Results.Ok(new HealthResponse(
            ProtocolConstants.Version,
            _settings.DeviceName,
            _settings.DeviceId,
            CertificateManager.Fingerprint(_certificate),
            DateTimeOffset.UtcNow)));

        app.MapPost("/api/v1/pair", (PairRequest request) =>
        {
            if (string.IsNullOrWhiteSpace(request.DeviceId) || string.IsNullOrWhiteSpace(request.DeviceName))
                return Results.BadRequest(new ApiError("INVALID_DEVICE", "장치 정보가 올바르지 않습니다."));
            if (!_pairing.TryConsume(request.Pin))
                return Results.Json(new ApiError("INVALID_PIN", "PIN이 틀렸거나 만료되었습니다."), statusCode: StatusCodes.Status401Unauthorized);

            var token = _devices.Register(request.DeviceId.Trim(), request.DeviceName.Trim());
            WriteLog($"새 장치 등록: {request.DeviceName}");
            return Results.Ok(new PairResponse(
                _settings.DeviceId,
                _settings.DeviceName,
                token,
                CertificateManager.Fingerprint(_certificate)));
        });

        app.MapPost("/api/v1/transfers", (HttpRequest http, TransferManifest manifest) =>
        {
            if (!TryAuthenticate(http, out var deviceId, out var error)) return error;
            if (!string.Equals(deviceId, manifest.DeviceId, StringComparison.Ordinal))
                return Results.Json(new ApiError("DEVICE_MISMATCH", "인증 장치와 전송 장치가 다릅니다."), statusCode: 403);
            try
            {
                var session = _transfers.Begin(manifest);
                var total = manifest.Files.Sum(file => file.Size);
                WriteLog($"전송 시작: {manifest.Files.Count}개, {FormatBytes(total)}");
                return Results.Ok(new TransferCreatedResponse(session.Id, manifest.Files.Count, total));
            }
            catch (Exception ex) when (ex is InvalidDataException or OverflowException)
            {
                return Results.BadRequest(new ApiError("INVALID_MANIFEST", ex.Message));
            }
        });

        app.MapPut("/api/v1/transfers/{transferId}/files/{fileIndex:int}", async (
            HttpRequest http, string transferId, int fileIndex, CancellationToken cancellationToken) =>
        {
            if (!TryAuthenticate(http, out var deviceId, out var error)) return error;
            try
            {
                var session = _transfers.Get(transferId);
                if (!string.Equals(session.DeviceId, deviceId, StringComparison.Ordinal))
                    return Results.Json(new ApiError("DEVICE_MISMATCH", "이 전송을 업로드할 권한이 없습니다."), statusCode: 403);

                var result = await _transfers.SaveFileAsync(transferId, fileIndex, http.Body, cancellationToken);
                WriteLog($"수신 완료: {result.SavedName} ({FormatBytes(result.BytesWritten)})");
                return Results.Ok(result);
            }
            catch (KeyNotFoundException ex)
            {
                return Results.NotFound(new ApiError("NOT_FOUND", ex.Message));
            }
            catch (InvalidDataException ex)
            {
                return Results.BadRequest(new ApiError("INVALID_FILE", ex.Message));
            }
        });

        app.MapGet("/api/v1/devices", (HttpRequest http) =>
        {
            if (!TryAuthenticate(http, out _, out var error)) return error;
            return Results.Ok(_devices.All.Select(device => new { device.DeviceId, device.DeviceName, device.PairedAt }));
        });

        await app.StartAsync(cancellationToken);
        _application = app;
        WriteLog($"HTTPS 수신 시작: 포트 {_settings.Port}");
    }

    public async Task StopAsync(CancellationToken cancellationToken = default)
    {
        var app = _application;
        _application = null;
        if (app is null) return;
        await app.StopAsync(cancellationToken);
        await app.DisposeAsync();
        WriteLog("수신 서버 중지");
    }

    public async ValueTask DisposeAsync() => await StopAsync();

    private bool TryAuthenticate(HttpRequest request, out string deviceId, out IResult error)
    {
        deviceId = request.Headers["X-HAMSHARE-DEVICE-ID"].ToString();
        var authorization = request.Headers.Authorization.ToString();
        var token = authorization.StartsWith("Bearer ", StringComparison.OrdinalIgnoreCase)
            ? authorization[7..].Trim()
            : string.Empty;
        if (string.IsNullOrWhiteSpace(deviceId) || string.IsNullOrWhiteSpace(token) || !_devices.Validate(deviceId, token))
        {
            error = Results.Json(new ApiError("UNAUTHORIZED", "등록되지 않은 장치입니다."), statusCode: StatusCodes.Status401Unauthorized);
            return false;
        }
        error = Results.Empty;
        return true;
    }

    private void WriteLog(string message) => LogMessage?.Invoke(this, $"{DateTime.Now:HH:mm:ss}  {message}");

    private static string FormatBytes(long value)
    {
        string[] units = ["B", "KB", "MB", "GB"];
        double number = value;
        var unit = 0;
        while (number >= 1024 && unit < units.Length - 1) { number /= 1024; unit++; }
        return $"{number:0.##} {units[unit]}";
    }
}
