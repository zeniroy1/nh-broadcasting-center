using HamShare.Core.Protocol;

namespace HamShare.Core.Storage;

public sealed class TransferSession
{
    private readonly Dictionary<int, FileDescriptor> _files;
    private readonly HashSet<int> _completed = [];

    public TransferSession(string id, TransferManifest manifest)
    {
        Id = id;
        DeviceId = manifest.DeviceId;
        CreatedAt = DateTimeOffset.UtcNow;
        _files = manifest.Files.ToDictionary(file => file.Index);
    }

    public string Id { get; }
    public string DeviceId { get; }
    public DateTimeOffset CreatedAt { get; }
    public IReadOnlyCollection<FileDescriptor> Files => _files.Values;
    public bool IsCompleted { get { lock (_completed) return _completed.Count == _files.Count; } }

    public FileDescriptor GetFile(int index)
        => _files.TryGetValue(index, out var file)
            ? file
            : throw new KeyNotFoundException($"파일 인덱스 {index}가 전송 목록에 없습니다.");

    public void MarkCompleted(int index)
    {
        lock (_completed) _completed.Add(index);
    }
}

