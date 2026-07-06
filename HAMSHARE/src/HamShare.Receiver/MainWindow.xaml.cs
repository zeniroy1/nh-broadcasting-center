using System.Collections.ObjectModel;
using System.ComponentModel;
using System.Runtime.CompilerServices;
using System.Security.Cryptography.X509Certificates;
using System.Windows;
using System.Windows.Media;
using HamShare.Core.Protocol;
using HamShare.Core.Storage;
using HamShare.Receiver.Services;
using Microsoft.Win32;

namespace HamShare.Receiver;

public partial class MainWindow : Window
{
    private readonly SettingsStore _settingsStore = new();
    private readonly ReceiverSettings _settings;
    private readonly X509Certificate2 _certificate;
    private readonly PairingManager _pairing = new();
    private readonly AuthorizedDeviceStore _devices = new();
    private readonly TransferCoordinator _transfers;
    private readonly ReceiverServer _server;
    private readonly Dictionary<string, TransferRow> _rowIndex = new();
    private bool _closing;

    public MainWindow()
    {
        InitializeComponent();
        DataContext = this;
        _settings = _settingsStore.Load();
        _certificate = CertificateManager.GetOrCreate(_settings.DeviceId);
        _transfers = new TransferCoordinator(_settings.ReceiveDirectory);
        _server = new ReceiverServer(_settings, _certificate, _pairing, _devices, _transfers);
        _server.LogMessage += (_, message) => Dispatcher.Invoke(() => AddLog(message));
        _transfers.ProgressChanged += (_, progress) => Dispatcher.Invoke(() => UpdateProgress(progress));

        Loaded += async (_, _) => await StartServerAsync();
        Closing += Window_Closing;
        RefreshView();
        AddLog("수신기 초기화 완료");
    }

    public ObservableCollection<TransferRow> TransferRows { get; } = [];

    private void RefreshView()
    {
        var addresses = NetworkAddress.GetLocalIpv4Addresses();
        AddressText.Text = addresses.Count == 0
            ? $"https://<PC-IP>:{_settings.Port}"
            : string.Join("   ", addresses.Select(address => $"https://{address}:{_settings.Port}"));
        FingerprintText.Text = CertificateManager.ShortFingerprint(_certificate);
        FingerprintText.ToolTip = CertificateManager.Fingerprint(_certificate);
        FolderText.Text = _settings.ReceiveDirectory;
        PinText.Text = _pairing.CurrentPin;
        PinExpiryText.Text = $"{_pairing.ExpiresAt.ToLocalTime():HH:mm}까지 유효";
        DeviceList.ItemsSource = _devices.All;
    }

    private async Task StartServerAsync()
    {
        try
        {
            await _server.StartAsync();
            SetRunning(true);
        }
        catch (Exception ex)
        {
            AddLog($"수신 시작 실패: {ex.Message}");
            SetRunning(false);
            MessageBox.Show(this, $"수신 서버를 시작하지 못했습니다.\n\n{ex.Message}", "HAMSHARE", MessageBoxButton.OK, MessageBoxImage.Error);
        }
    }

    private async void StartButton_Click(object sender, RoutedEventArgs e) => await StartServerAsync();

    private async void StopButton_Click(object sender, RoutedEventArgs e)
    {
        await _server.StopAsync();
        SetRunning(false);
    }

    private void RefreshPin_Click(object sender, RoutedEventArgs e)
    {
        _pairing.Refresh();
        RefreshView();
        AddLog("새 등록 PIN 생성");
    }

    private void ChooseFolder_Click(object sender, RoutedEventArgs e)
    {
        var dialog = new OpenFolderDialog { Title = "HAMSHARE 수신 폴더 선택", InitialDirectory = _settings.ReceiveDirectory };
        if (dialog.ShowDialog(this) != true) return;
        _settings.ReceiveDirectory = dialog.FolderName;
        _transfers.ReceiveDirectory = dialog.FolderName;
        _settingsStore.Save(_settings);
        RefreshView();
        AddLog($"수신 폴더 변경: {dialog.FolderName}");
    }

    private void RemoveDevice_Click(object sender, RoutedEventArgs e)
    {
        if (DeviceList.SelectedItem is not AuthorizedDevice selected) return;
        var answer = MessageBox.Show(this, $"'{selected.DeviceName}' 장치 등록을 해제할까요?", "HAMSHARE", MessageBoxButton.YesNo, MessageBoxImage.Question);
        if (answer != MessageBoxResult.Yes) return;
        _devices.Remove(selected.DeviceId);
        RefreshView();
        AddLog($"장치 등록 해제: {selected.DeviceName}");
    }

    private async void Window_Closing(object? sender, CancelEventArgs e)
    {
        if (_closing) return;
        _closing = true;
        e.Cancel = true;
        await _server.StopAsync();
        _certificate.Dispose();
        e.Cancel = false;
        Close();
    }

    private void SetRunning(bool running)
    {
        StatusText.Text = running ? "수신 대기 중" : "중지됨";
        StatusDot.Fill = new SolidColorBrush((Color)ColorConverter.ConvertFromString(running ? "#43D39E" : "#FFC857"));
        StartButton.IsEnabled = !running;
        StopButton.IsEnabled = running;
        RefreshView();
    }

    private void UpdateProgress(TransferProgress progress)
    {
        var key = $"{progress.TransferId}:{progress.FileIndex}";
        if (!_rowIndex.TryGetValue(key, out var row))
        {
            row = new TransferRow(progress.FileName);
            _rowIndex[key] = row;
            TransferRows.Insert(0, row);
        }
        row.Update(progress);
    }

    private void AddLog(string message)
    {
        LogList.Items.Insert(0, message);
        while (LogList.Items.Count > 200) LogList.Items.RemoveAt(LogList.Items.Count - 1);
    }
}

public sealed class TransferRow : INotifyPropertyChanged
{
    private string _progressText = "0%";
    private string _speedText = "-";
    private string _stateText = "대기";

    public TransferRow(string fileName) => FileName = fileName;
    public string FileName { get; }
    public string ProgressText { get => _progressText; private set => SetField(ref _progressText, value); }
    public string SpeedText { get => _speedText; private set => SetField(ref _speedText, value); }
    public string StateText { get => _stateText; private set => SetField(ref _stateText, value); }
    public event PropertyChangedEventHandler? PropertyChanged;

    public void Update(TransferProgress progress)
    {
        var percent = progress.TotalBytes == 0 ? 100 : progress.BytesTransferred * 100d / progress.TotalBytes;
        ProgressText = $"{percent:0.0}%";
        SpeedText = FormatSpeed(progress.BytesPerSecond);
        StateText = progress.State switch
        {
            TransferState.Waiting => "대기",
            TransferState.Receiving => "수신 중",
            TransferState.Completed => "완료",
            TransferState.Failed => "실패",
            TransferState.Cancelled => "취소",
            _ => progress.State.ToString()
        };
    }

    private static string FormatSpeed(double bytesPerSecond)
        => bytesPerSecond >= 1024 * 1024
            ? $"{bytesPerSecond / 1024 / 1024:0.0} MB/s"
            : $"{bytesPerSecond / 1024:0} KB/s";

    private void SetField(ref string field, string value, [CallerMemberName] string? propertyName = null)
    {
        if (field == value) return;
        field = value;
        PropertyChanged?.Invoke(this, new PropertyChangedEventArgs(propertyName));
    }
}
