using System.Collections.Concurrent;
using System.Diagnostics;
using System.Security.Cryptography;
using HamShare.Core.Protocol;

namespace HamShare.Core.Storage;

public sealed class TransferCoordinator
{
    private readonly ConcurrentDictionary<string, TransferSession> _sessions = new();
    private readonly ConcurrentDictionary<string, SemaphoreSlim> _fileLocks = new();
    private string _receiveDirectory;

    public TransferCoordinator(string receiveDirectory)
    {
        _receiveDirectory = Path.GetFullPath(receiveDirectory);
        Directory.CreateDirectory(_receiveDirectory);
    }

    public event EventHandler<TransferProgress>? ProgressChanged;

    public string ReceiveDirectory
    {
        get => _receiveDirectory;
        set
        {
            var fullPath = Path.GetFullPath(value);
            Directory.CreateDirectory(fullPath);
            _receiveDirectory = fullPath;
        }
    }

    public TransferSession Begin(TransferManifest manifest)
    {
        ValidateManifest(manifest);
        var id = Guid.NewGuid().ToString("N");
        var session = new TransferSession(id, manifest);
        if (!_sessions.TryAdd(id, session))
            throw new InvalidOperationException("전송 세션을 만들 수 없습니다.");
        return session;
    }

    public TransferSession Get(string transferId)
        => _sessions.TryGetValue(transferId, out var session)
            ? session
            : throw new KeyNotFoundException("전송 세션을 찾을 수 없습니다.");

    public async Task<UploadResult> SaveFileAsync(
        string transferId,
        int fileIndex,
        Stream source,
        CancellationToken cancellationToken = default)
    {
        var session = Get(transferId);
        var descriptor = session.GetFile(fileIndex);
        var lockKey = $"{transferId}:{fileIndex}";
        var gate = _fileLocks.GetOrAdd(lockKey, _ => new SemaphoreSlim(1, 1));
        await gate.WaitAsync(cancellationToken).ConfigureAwait(false);

        string? partialPath = null;
        try
        {
            var finalPath = SafeFileName.CreateUniquePath(_receiveDirectory, descriptor.Name);
            partialPath = finalPath + ".partial";
            var stopwatch = Stopwatch.StartNew();
            long written = 0;
            var buffer = new byte[1024 * 1024];
            using var hasher = IncrementalHash.CreateHash(HashAlgorithmName.SHA256);
            await using (var destination = new FileStream(
                partialPath,
                FileMode.CreateNew,
                FileAccess.Write,
                FileShare.None,
                buffer.Length,
                FileOptions.Asynchronous | FileOptions.SequentialScan))
            {
                while (true)
                {
                    var read = await source.ReadAsync(buffer, cancellationToken).ConfigureAwait(false);
                    if (read == 0) break;
                    written += read;
                    if (written > descriptor.Size)
                        throw new InvalidDataException("선언된 파일 크기보다 많은 데이터가 수신되었습니다.");

                    hasher.AppendData(buffer, 0, read);
                    await destination.WriteAsync(buffer.AsMemory(0, read), cancellationToken).ConfigureAwait(false);
                    var elapsed = Math.Max(0.001, stopwatch.Elapsed.TotalSeconds);
                    ProgressChanged?.Invoke(this, new TransferProgress(
                        transferId, fileIndex, descriptor.Name, written, descriptor.Size,
                        written / elapsed, TransferState.Receiving));
                }
                await destination.FlushAsync(cancellationToken).ConfigureAwait(false);
            }

            if (written != descriptor.Size)
                throw new InvalidDataException($"파일 크기가 일치하지 않습니다. 예상 {descriptor.Size}, 수신 {written}");

            var actualHash = Convert.ToHexString(hasher.GetHashAndReset());
            if (!actualHash.Equals(descriptor.Sha256, StringComparison.OrdinalIgnoreCase))
                throw new InvalidDataException("SHA-256 무결성 검증에 실패했습니다.");

            File.Move(partialPath, finalPath);
            partialPath = null;
            session.MarkCompleted(fileIndex);
            ProgressChanged?.Invoke(this, new TransferProgress(
                transferId, fileIndex, descriptor.Name, written, descriptor.Size,
                written / Math.Max(0.001, stopwatch.Elapsed.TotalSeconds), TransferState.Completed));

            return new UploadResult(transferId, fileIndex, descriptor.Name, Path.GetFileName(finalPath), written, actualHash, true);
        }
        catch (OperationCanceledException)
        {
            ProgressChanged?.Invoke(this, new TransferProgress(
                transferId, fileIndex, descriptor.Name, 0, descriptor.Size, 0, TransferState.Cancelled, "사용자가 취소했습니다."));
            throw;
        }
        catch (Exception ex)
        {
            ProgressChanged?.Invoke(this, new TransferProgress(
                transferId, fileIndex, descriptor.Name, 0, descriptor.Size, 0, TransferState.Failed, ex.Message));
            throw;
        }
        finally
        {
            if (partialPath is not null)
            {
                try { File.Delete(partialPath); } catch { /* 다음 시작 시 정리 대상 */ }
            }
            gate.Release();
            _fileLocks.TryRemove(lockKey, out _);
            gate.Dispose();
        }
    }

    private static void ValidateManifest(TransferManifest manifest)
    {
        if (string.IsNullOrWhiteSpace(manifest.DeviceId))
            throw new InvalidDataException("장치 ID가 없습니다.");
        if (manifest.Files.Count is < 1 or > ProtocolConstants.MaxFilesPerTransfer)
            throw new InvalidDataException($"파일 개수는 1~{ProtocolConstants.MaxFilesPerTransfer}개여야 합니다.");
        if (manifest.Files.Select(file => file.Index).Distinct().Count() != manifest.Files.Count)
            throw new InvalidDataException("파일 인덱스가 중복되었습니다.");

        long total = 0;
        foreach (var file in manifest.Files)
        {
            if (file.Index < 0 || file.Size < 0)
                throw new InvalidDataException("잘못된 파일 인덱스 또는 크기입니다.");
            if (file.Sha256.Length != 64 || !file.Sha256.All(Uri.IsHexDigit))
                throw new InvalidDataException("SHA-256 형식이 올바르지 않습니다.");
            checked { total += file.Size; }
        }
        if (total > ProtocolConstants.MaxTransferBytes)
            throw new InvalidDataException("1회 전송 최대 용량을 초과했습니다.");
    }
}
