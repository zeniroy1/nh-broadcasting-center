using System;
using System.Collections.Concurrent;
using System.Collections.Generic;
using System.Diagnostics;
using System.Drawing;
using System.IO;
using System.Linq;
using System.Windows.Forms;

namespace HyunsikArchive
{
    static class Program
    {
        [STAThread]
        static void Main()
        {
            Application.EnableVisualStyles();
            Application.SetCompatibleTextRenderingDefault(false);
            Application.Run(new MainForm());
        }
    }

    public partial class MainForm : Form
    {
        private readonly string _targetPath = @"C:\Users\BSS 3\OneDrive\바탕 화면";
        private ConcurrentDictionary<string, FileItem> _fileCache = new ConcurrentDictionary<string, FileItem>();
        private List<FileItem> _filteredList = new List<FileItem>();
        private FileSystemWatcher _watcher;
        private System.Windows.Forms.Timer _resourceTimer;

        private readonly HashSet<string> _allowedExtensions = new HashSet<string>(StringComparer.OrdinalIgnoreCase)
        {
            ".hwp", ".pdf", ".xlsx", ".xls", ".docx", ".doc", ".txt", ".log", ".mp4", ".mkv", ".png", ".jpg"
        };

        private TextBox txtSearch;
        private DataGridView dgvResults;
        private StatusStrip statusStrip;
        private ToolStripStatusLabel lblStatus;
        private ToolStripStatusLabel lblResource;
        private NotifyIcon trayIcon;

        public MainForm()
        {
            InitializeComponent();
            ApplyDarkTheme();
            InitSystemTray();
            CheckEnvironment();
            StartRealTimeMonitoring();
            StartResourceMonitor();
            RefreshCache();
        }

        private void InitializeComponent()
        {
            this.Text = "현식전용검색기 (색상구분형)";
            this.Size = new Size(1100, 750);
            this.StartPosition = FormStartPosition.CenterScreen;

            Panel pnlTop = new Panel { Dock = DockStyle.Top, Height = 70, Padding = new Padding(15) };
            txtSearch = new TextBox { Dock = DockStyle.Fill, Font = new Font("맑은 고딕", 14, FontStyle.Bold) };
            txtSearch.PlaceholderText = " 검색어를 입력하세요...";
            txtSearch.TextChanged += (s, e) => SearchFiles(txtSearch.Text);

            Button btnRefresh = new Button { Text = "새로고침(F5)", Width = 110, Dock = DockStyle.Right, FlatStyle = FlatStyle.Flat };
            btnRefresh.Click += (s, e) => RefreshCache();

            pnlTop.Controls.Add(txtSearch);
            pnlTop.Controls.Add(btnRefresh);

            dgvResults = new DataGridView
            {
                Dock = DockStyle.Fill,
                AutoSizeColumnsMode = DataGridViewAutoSizeColumnsMode.Fill,
                ReadOnly = true,
                SelectionMode = DataGridViewSelectionMode.FullRowSelect,
                RowHeadersVisible = false,
                AllowUserToAddRows = false,
                BorderStyle = BorderStyle.None,
                VirtualMode = true,
                RowTemplate = { Height = 35 }
            };

            // 컬럼 생성 및 중앙 정렬 설정
            var colExt = new DataGridViewTextBoxColumn { Name = "Ext", HeaderText = "형식", Width = 80 };
            var colName = new DataGridViewTextBoxColumn { Name = "Name", HeaderText = "파일명", Width = 400 };
            var colPath = new DataGridViewTextBoxColumn { Name = "Path", HeaderText = "전체 경로" };

            // 모든 컬럼 중앙 정렬 적용
            colExt.DefaultCellStyle.Alignment = DataGridViewContentAlignment.MiddleCenter;
            colName.DefaultCellStyle.Alignment = DataGridViewContentAlignment.MiddleCenter;
            colPath.DefaultCellStyle.Alignment = DataGridViewContentAlignment.MiddleCenter;
            dgvResults.ColumnHeadersDefaultCellStyle.Alignment = DataGridViewContentAlignment.MiddleCenter;

            dgvResults.Columns.AddRange(colExt, colName, colPath);
            
            dgvResults.CellValueNeeded += DgvResults_CellValueNeeded;
            dgvResults.CellFormatting += DgvResults_CellFormatting; // 색상 구분 이벤트
            dgvResults.CellDoubleClick += (s, e) => OpenSelected();
            InitContextMenu();

            statusStrip = new StatusStrip();
            lblStatus = new ToolStripStatusLabel { Text = "준비 완료", Spring = true, TextAlign = ContentAlignment.MiddleLeft };
            lblResource = new ToolStripStatusLabel { Text = "리소스 확인 중..." };
            statusStrip.Items.AddRange(new ToolStripItem[] { lblStatus, lblResource });

            this.Controls.Add(dgvResults);
            this.Controls.Add(pnlTop);
            this.Controls.Add(statusStrip);

            this.KeyPreview = true;
            this.KeyDown += (s, e) => { if (e.KeyCode == Keys.F5) RefreshCache(); };
        }

        // 확장자별 색상 구분 로직
        private void DgvResults_CellFormatting(object sender, DataGridViewCellFormattingEventArgs e)
        {
            if (e.RowIndex < 0 || e.RowIndex >= _filteredList.Count) return;

            // '형식(Ext)' 컬럼에만 색상 적용
            if (dgvResults.Columns[e.ColumnIndex].Name == "Ext")
            {
                string ext = e.Value?.ToString().ToUpper();
                switch (ext)
                {
                    case "XLSX": case "XLS":
                        e.CellStyle.ForeColor = Color.LimeGreen; break; // 엑셀: 초록
                    case "HWP": case "DOCX": case "DOC":
                        e.CellStyle.ForeColor = Color.SkyBlue; break;  // 문서: 하늘색
                    case "PDF":
                        e.CellStyle.ForeColor = Color.Tomato; break;   // PDF: 주황빛 빨강
                    case "LOG": case "TXT":
                        e.CellStyle.ForeColor = Color.LightGray; break; // 로그: 회색
                    case "MP4": case "MKV":
                        e.CellStyle.ForeColor = Color.MediumPurple; break; // 영상: 보라
                    case "PNG": case "JPG":
                        e.CellStyle.ForeColor = Color.SandyBrown; break; // 이미지: 갈색
                }
                e.CellStyle.Font = new Font(dgvResults.Font, FontStyle.Bold);
            }
        }

        private void ApplyDarkTheme()
        {
            Color bgColor = Color.FromArgb(30, 30, 30);
            this.BackColor = bgColor;
            dgvResults.BackgroundColor = bgColor;
            dgvResults.DefaultCellStyle.BackColor = Color.FromArgb(40, 40, 40);
            dgvResults.DefaultCellStyle.ForeColor = Color.White;
            dgvResults.ColumnHeadersDefaultCellStyle.BackColor = Color.FromArgb(60, 60, 60);
            dgvResults.ColumnHeadersDefaultCellStyle.ForeColor = Color.White;
            dgvResults.EnableHeadersVisualStyles = false;
            txtSearch.BackColor = Color.FromArgb(50, 50, 50);
            txtSearch.ForeColor = Color.White;
            statusStrip.BackColor = Color.FromArgb(25, 25, 25);
            statusStrip.ForeColor = Color.White;
        }

        private void RefreshCache()
        {
            lblStatus.Text = "🔄 동기화 중...";
            _fileCache.Clear();
            try {
                if (Directory.Exists(_targetPath)) {
                    var files = Directory.EnumerateFiles(_targetPath, "*.*", SearchOption.AllDirectories)
                                .Where(p => IsValidFile(p));
                    foreach (var f in files) _fileCache.TryAdd(f, new FileItem(f));
                }
            } catch { }
            SearchFiles(txtSearch.Text);
            lblStatus.Text = $"✔ 최신 상태 ({_fileCache.Count}개)";
        }

        private bool IsValidFile(string path)
        {
            string name = Path.GetFileName(path);
            string ext = Path.GetExtension(path);
            if (name.StartsWith("~$") || name.Equals("desktop.ini", StringComparison.OrdinalIgnoreCase)) return false;
            return _allowedExtensions.Contains(ext);
        }

        private void SearchFiles(string keyword)
        {
            var query = keyword.Trim().ToLower();
            _filteredList = _fileCache.Values
                .Where(f => string.IsNullOrEmpty(query) || f.FileName.ToLower().Contains(query))
                .OrderByDescending(f => f.LastWriteTime).ToList();
            dgvResults.RowCount = _filteredList.Count;
            dgvResults.Refresh();
        }

        private void StartRealTimeMonitoring()
        {
            if (!Directory.Exists(_targetPath)) return;
            _watcher = new FileSystemWatcher(_targetPath) { IncludeSubdirectories = true, EnableRaisingEvents = true };
            _watcher.Created += (s, e) => this.Invoke((MethodInvoker)delegate { RefreshCache(); });
            _watcher.Deleted += (s, e) => this.Invoke((MethodInvoker)delegate { RefreshCache(); });
            _watcher.Renamed += (s, e) => this.Invoke((MethodInvoker)delegate { RefreshCache(); });
            _watcher.Changed += (s, e) => this.Invoke((MethodInvoker)delegate { RefreshCache(); });
        }

        private void StartResourceMonitor()
        {
            _resourceTimer = new System.Windows.Forms.Timer { Interval = 2000 };
            _resourceTimer.Tick += (s, e) => {
                var proc = Process.GetCurrentProcess();
                lblResource.Text = $"| RAM: {proc.PrivateMemorySize64 / 1024 / 1024}MB | 모니터링 중";
            };
            _resourceTimer.Start();
        }

        private void InitContextMenu()
        {
            ContextMenuStrip menu = new ContextMenuStrip();
            menu.Items.Add("파일 열기", null, (s, e) => OpenSelected());
            menu.Items.Add("폴더 위치 열기", null, (s, e) => OpenLocation());
            menu.Items.Add(new ToolStripSeparator());
            menu.Items.Add("내 바탕화면으로 복사", null, (s, e) => QuickCopy());
            dgvResults.ContextMenuStrip = menu;
        }

        private void QuickCopy()
        {
            var item = GetSelectedItem();
            if (item == null) return;
            string dest = Path.Combine(Environment.GetFolderPath(Environment.SpecialFolder.Desktop), item.FileName);
            try { File.Copy(item.FullPath, dest, true); lblStatus.Text = $"✔ 복사 완료: {item.FileName}"; } catch { }
        }

        private void OpenSelected() { var item = GetSelectedItem(); if (item != null) Process.Start(new ProcessStartInfo(item.FullPath) { UseShellExecute = true }); }
        private void OpenLocation() { var item = GetSelectedItem(); if (item != null) Process.Start("explorer.exe", $"/select,\"{item.FullPath}\""); }
        private FileItem GetSelectedItem() => dgvResults.CurrentRow?.Index >= 0 ? _filteredList[dgvResults.CurrentRow.Index] : null;

        private void DgvResults_CellValueNeeded(object sender, DataGridViewCellValueEventArgs e) {
            if (e.RowIndex >= _filteredList.Count) return;
            var item = _filteredList[e.RowIndex];
            if (e.ColumnIndex == 0) e.Value = item.Extension;
            else if (e.ColumnIndex == 1) e.Value = item.FileName;
            else if (e.ColumnIndex == 2) e.Value = item.FullPath;
        }

        private void CheckEnvironment() {
            bool exists = Directory.Exists(_targetPath);
            statusStrip.BackColor = exists ? Color.DarkGreen : Color.DarkRed;
            lblStatus.Text = exists ? "✔ BSS 3 연결 성공" : "✘ 연결 실패";
        }

        private void InitSystemTray() {
            ContextMenuStrip trayMenu = new ContextMenuStrip();
            trayMenu.Items.Add("프로그램 열기", null, (s, e) => { this.Show(); this.WindowState = FormWindowState.Normal; });
            trayMenu.Items.Add("완전히 종료", null, (s, e) => { 
                trayIcon.Visible = false;
                Application.Exit(); 
            });

            trayIcon = new NotifyIcon { 
                Icon = SystemIcons.Application, 
                Visible = true, 
                Text = "현식전용검색기",
                ContextMenuStrip = trayMenu
            };
            
            trayIcon.DoubleClick += (s, e) => { this.Show(); this.WindowState = FormWindowState.Normal; };
            this.FormClosing += (s, e) => { if (e.CloseReason == CloseReason.UserClosing) { e.Cancel = true; this.Hide(); } };
        }
    }

    public class FileItem
    {
        public string FileName { get; set; }
        public string FullPath { get; set; }
        public string Extension { get; set; }
        public DateTime LastWriteTime { get; set; }
        public FileItem(string path) { 
            FullPath = path; 
            FileName = Path.GetFileName(path); 
            Extension = Path.GetExtension(path).ToUpper().Replace(".", ""); 
            try { LastWriteTime = File.GetLastWriteTime(path); } catch { LastWriteTime = DateTime.MinValue; }
        }
    }
}