namespace HamShare.Core.Protocol;

public static class ProtocolConstants
{
    public const string Version = "1.0";
    public const int DefaultPort = 57321;
    public const int MaxFilesPerTransfer = 1_000;
    public const long MaxTransferBytes = 20L * 1024 * 1024 * 1024;
}

public sealed record HealthResponse(
    string ProtocolVersion,
    string DeviceName,
    string DeviceId,
    string CertificateFingerprint,
    DateTimeOffset ServerTime);

public sealed record PairRequest(string DeviceId, string DeviceName, string Pin);

public sealed record PairResponse(
    string DeviceId,
    string DeviceName,
    string AccessToken,
    string CertificateFingerprint);

public sealed record FileDescriptor(
    int Index,
    string Name,
    long Size,
    string Sha256,
    string? MimeType = null,
    long? LastModifiedUnixMilliseconds = null);

public sealed record TransferManifest(string DeviceId, IReadOnlyList<FileDescriptor> Files);

public sealed record TransferCreatedResponse(string TransferId, int FileCount, long TotalBytes);

public sealed record UploadResult(
    string TransferId,
    int FileIndex,
    string OriginalName,
    string SavedName,
    long BytesWritten,
    string Sha256,
    bool Completed);

public sealed record ApiError(string Code, string Message);

public enum TransferState
{
    Waiting,
    Receiving,
    Completed,
    Failed,
    Cancelled
}

public sealed record TransferProgress(
    string TransferId,
    int FileIndex,
    string FileName,
    long BytesTransferred,
    long TotalBytes,
    double BytesPerSecond,
    TransferState State,
    string? Message = null);

