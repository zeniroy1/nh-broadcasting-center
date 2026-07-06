using System;
using System.IO;
using System.Drawing;
using System.Windows.Forms;
using System.Threading;
using System.Collections.Concurrent;
using System.Collections.Generic;
using System.Linq;
using System.Runtime.InteropServices;
using System.Diagnostics;

namespace NHArchiveExplorer
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

    #region Win32 Native API (Fast File Scanner)
    public static class FastDirectoryEnumerator
    {
        [DllImport("kernel32.dll", CharSet = CharSet.Unicode, SetLastError = true)]
        public static extern IntPtr FindFirstFile(string lpFileName, out WIN32_FIND_DATA lpFindFileData);

        [DllImport("kernel32.dll", CharSet = CharSet.Unicode, SetLastError = true)]
        public static extern bool FindNextFile(IntPtr hFindFile, out WIN32_FIND_DATA lpFindFileData);

        [DllImport("kernel32.dll", SetLastError = true)]
        public static extern bool FindClose(IntPtr hFindFile);

        [StructLayout(LayoutKind.Sequential, CharSet = CharSet.Unicode)]
        public struct WIN32_FIND_DATA
        {
            public uint dwFileAttributes;
            public System.Runtime.InteropServices.ComTypes.FILETIME ftCreationTime;
            public System.Runtime.InteropServices.ComTypes.FILETIME ftLastAccessTime;
            public System.Runtime.InteropServices.ComTypes.FILETIME ftLastWriteTime;
            public uint nFileSizeHigh;
            public uint nFileSizeLow;
            public uint dwReserved0;
            public uint dwReserved1;
            [MarshalAs(UnmanagedType.ByValTStr, SizeConst = 260)]
            public string cFileName;
            [MarshalAs(UnmanagedType.ByValTStr, SizeConst = 14)]
            public string cAlternateFileName;
        }

        public static void TraverseTree(string rootDir, Action<string, WIN32_FIND_DATA> onFileFound)
        {
            Stack<string> dirs = new Stack<string>();
            dirs.Push(rootDir);

            while (dirs.Count > 0)
            {
                string currentDir = dirs.Pop();
                WIN32_FIND_DATA findData;
                IntPtr hFind = FindFirstFile(Path.Combine(currentDir, "*"), out findData);

                if (hFind != new IntPtr(-1))
                {
                    do
                    {
                        if (findData.cFileName != "." && findData.cFileName != "..")
                        {
                            // Thumbs.db, desktop.ini, 임시파일(~) 제외
                            if (findData.cFileName.Equals("Thumbs.db", StringComparison.OrdinalIgnoreCase) ||
                                findData.cFileName.Equals("desktop.ini", StringComparison.OrdinalIgnoreCase) ||
                                findData.cFileName.StartsWith("~"))
                            {
                                continue;
                            }

                            if ((findData.dwFileAttributes & 0x10) != 0) 
                            {
                                dirs.Push(Path.Combine(currentDir, findData.cFileName));
                            }
                            else
                            {
                                onFileFound(currentDir, findData);
                            }
                        }
                    } while (FindNextFile(hFind, out findData));
                    FindClose(hFind);
                }
            }
        }
    }
    #endregion

    #region Models
    public class FileItem
    {
        public string FullPath { get; set; }
        public string FileName { get; set; }
        public string DirectoryName { get; set; }
        public string Extension { get; set; }
        public string TypeTag { get; set; }
        public DateTime LastWriteTime { get; set; }
        public DateTime CreationTime { get; set; }
        // 정렬 기준: 수정시각 vs 생성시각 중 더 최신 값 (카메라 MXF 등 장비에서 끝내온 파일의 내부 날짜 보정)
        public DateTime SortTime { get { return CreationTime > LastWriteTime ? CreationTime : LastWriteTime; } }
        public long Length { get; set; }
        public string DisplaySize { get; set; }
        public string DisplayDate { get; set; }
    }
    #endregion

    #region Core Engine
    public class SearchEngine
    {
        private ConcurrentDictionary<string, FileItem> _cache = new ConcurrentDictionary<string, FileItem>(StringComparer.OrdinalIgnoreCase);
        private FileSystemWatcher _watcher;
        public string TargetDirectory { get; private set; }
        
        public event Action<int> OnScanProgress;
        public event Action<int, long> OnScanCompleted;
        public event Action<string, string> OnSyncEvent; 
        public event Action<string> OnErrorEvent;

        public SearchEngine(string targetDir)
        {
            TargetDirectory = targetDir;
        }

        private bool _isScanning = false;

        public void Start()
        {
            if (_isScanning) return; // 중복 스캔 방지
            _isScanning = true;
            _cache.Clear();
            if (!Directory.Exists(TargetDirectory)) 
            {
                if(OnErrorEvent != null) OnErrorEvent(string.Format("대상 폴더({0})를 찾을 수 없거나 권한이 없습니다.", TargetDirectory));
                if(OnScanCompleted != null) OnScanCompleted(0, 0);
                _isScanning = false;
                return; 
            }
            
            Thread scanThread = new Thread(() => {
                Stopwatch sw = Stopwatch.StartNew();
                int count = 0;
                try {
                    FastDirectoryEnumerator.TraverseTree(TargetDirectory, (currentDir, findData) => {
                        AddToFileItemFast(currentDir, findData);
                        count++;
                        if (count % 1000 == 0) {
                            if (OnScanProgress != null) OnScanProgress(count);
                        }
                    });
                } catch(Exception ex) { 
                    if(OnErrorEvent != null) OnErrorEvent("스캔 중 예외 발생: " + ex.Message);
                } 
                sw.Stop();
                _isScanning = false;
                if (OnScanCompleted != null) OnScanCompleted(_cache.Count, sw.ElapsedMilliseconds);
            });
            scanThread.IsBackground = true;
            scanThread.Start();
            StartWatcher();
        }

        private void AddToFileItemFast(string directoryName, FastDirectoryEnumerator.WIN32_FIND_DATA findData)
        {
            try {
                string ext = Path.GetExtension(findData.cFileName).ToLower();
                long len = ((long)findData.nFileSizeHigh << 32) + findData.nFileSizeLow;
                string relativeDir = GetRelativeDirectory(directoryName);
                string fullPath = Path.Combine(directoryName, findData.cFileName);
                
                DateTime lastWrite;
                try {
                    long ft = ((long)findData.ftLastWriteTime.dwHighDateTime << 32) + (uint)findData.ftLastWriteTime.dwLowDateTime;
                    lastWrite = DateTime.FromFileTimeUtc(ft).ToLocalTime();
                } catch {
                    lastWrite = DateTime.MinValue;
                }

                DateTime creationTime;
                try {
                    long ft = ((long)findData.ftCreationTime.dwHighDateTime << 32) + (uint)findData.ftCreationTime.dwLowDateTime;
                    creationTime = DateTime.FromFileTimeUtc(ft).ToLocalTime();
                } catch {
                    creationTime = DateTime.MinValue;
                }

                // 표시 날짜: 두 시각 중 더 최신 것
                DateTime displayTime = creationTime > lastWrite ? creationTime : lastWrite;
                if (displayTime == DateTime.MinValue) displayTime = DateTime.Now;

                _cache[fullPath] = new FileItem {
                    FullPath = fullPath,
                    FileName = findData.cFileName,
                    DirectoryName = relativeDir,
                    Extension = ext,
                    TypeTag = GetTagFromExtension(ext),
                    LastWriteTime = lastWrite,
                    CreationTime = creationTime,
                    Length = len,
                    DisplayDate = displayTime.ToString("yy-MM-dd HH:mm"),
                    DisplaySize = FormatSize(len)
                };
            } catch (Exception ex) {
                Debug.WriteLine("파일 캐싱 오류: " + ex.Message);
            }
        }

        private void AddToFileItemSlow(string fullPath) {
            try {
                var info = new FileInfo(fullPath);
                
                // Thumbs.db, desktop.ini, 임시파일(~) 제외
                if (info.Name.Equals("Thumbs.db", StringComparison.OrdinalIgnoreCase) ||
                    info.Name.Equals("desktop.ini", StringComparison.OrdinalIgnoreCase) ||
                    info.Name.StartsWith("~")) {
                    return;
                }

                string ext = info.Extension.ToLower();
                DateTime lastWrite = DateTime.MinValue;
                DateTime creationTime = DateTime.MinValue;
                try { lastWrite = info.LastWriteTime; } catch { }
                try { creationTime = info.CreationTime; } catch { }
                DateTime displayTime = creationTime > lastWrite ? creationTime : lastWrite;
                if (displayTime == DateTime.MinValue) displayTime = DateTime.Now;

                _cache[fullPath] = new FileItem {
                    FullPath = info.FullName,
                    FileName = info.Name,
                    DirectoryName = GetRelativeDirectory(info.DirectoryName),
                    Extension = ext,
                    TypeTag = GetTagFromExtension(ext),
                    LastWriteTime = lastWrite,
                    CreationTime = creationTime,
                    Length = info.Length,
                    DisplayDate = displayTime.ToString("yy-MM-dd HH:mm"),
                    DisplaySize = FormatSize(info.Length)
                };
            } catch (Exception ex) {
                Debug.WriteLine("파일 캐싱 오류: " + ex.Message);
            }
        }

        private string GetTagFromExtension(string ext) {
            if(ext == ".mp4" || ext == ".avi" || ext == ".mkv" || ext == ".wmv" || ext == ".mov" || ext == ".mxf") return "VIDEO";
            if(ext == ".mp3" || ext == ".wav" || ext == ".m4a") return "AUDIO";
            if(ext == ".jpg" || ext == ".png" || ext == ".jpeg" || ext == ".bmp") return "IMAGE";
            if(ext == ".xls" || ext == ".xlsx" || ext == ".csv") return "EXCEL";
            if(ext == ".hwp" || ext == ".hwpx") return "HWP";
            if(ext == ".ppt" || ext == ".pptx") return "PPT";
            if(ext == ".doc" || ext == ".docx" || ext == ".pdf" || ext == ".txt") return "DOC";
            return "기타";
        }

        private string FormatSize(long len) {
            if(len > 1073741824) return (len / 1073741824.0).ToString("0.0") + " GB";
            if(len > 1048576) return (len / 1048576.0).ToString("0.0") + " MB";
            if(len == 0) return "0 KB";
            return (len / 1024.0).ToString("0") + " KB";
        }

        private string GetRelativeDirectory(string dir) {
            if(dir.StartsWith(TargetDirectory, StringComparison.OrdinalIgnoreCase)) {
                string rel = dir.Substring(TargetDirectory.Length);
                if(rel.StartsWith("\\")) rel = rel.Substring(1);
                return rel;
            }
            return dir;
        }

        private void StartWatcher()
        {
            if (_watcher != null) { _watcher.Dispose(); }
            if (!Directory.Exists(TargetDirectory)) return;
            try {
                _watcher = new FileSystemWatcher(TargetDirectory);
                _watcher.IncludeSubdirectories = true;      
                _watcher.EnableRaisingEvents = true;        

                _watcher.Created += (s, e) => {
                    AddToFileItemSlow(e.FullPath);
                    if (OnSyncEvent != null) OnSyncEvent("생성", e.Name);
                };
                _watcher.Changed += (s, e) => {
                    AddToFileItemSlow(e.FullPath);
                    if (OnSyncEvent != null) OnSyncEvent("수정", e.Name);
                };
                _watcher.Deleted += (s, e) => {
                    FileItem removed;
                    _cache.TryRemove(e.FullPath, out removed);
                    if (OnSyncEvent != null) OnSyncEvent("삭제", e.Name);
                };
                _watcher.Renamed += (s, e) => {
                    FileItem removed;
                    _cache.TryRemove(e.OldFullPath, out removed);
                    AddToFileItemSlow(e.FullPath);
                    // 이름 변경 / 폴더 이동 시 상단 노출: CreationTime을 현재 시각으로 갱신
                    FileItem item;
                    if (_cache.TryGetValue(e.FullPath, out item)) {
                        item.CreationTime = DateTime.Now;
                        item.DisplayDate = DateTime.Now.ToString("yy-MM-dd HH:mm");
                    }
                    if (OnSyncEvent != null) OnSyncEvent("이름/이동", e.Name);
                };
            } catch {
                if(OnErrorEvent != null) OnErrorEvent("동기화 감시망 시작 오류");
            }
        }

        public void Refresh() { Start(); }
        public int GetTotalCount() { return _cache.Count; }
        public List<FileItem> GetAllItems() { return _cache.Values.ToList(); }
    }
    #endregion

    #region GUI App
    class MainForm : Form
    {
        private TextBox txtSearch;
        private DataGridView dgvResults;
        private Label lblTotalCount;
        private ToolStripStatusLabel lblSyncMessage;
        private Button btnRefresh;
        private ContextMenuStrip dgvContextMenu; // 확장성을 위한 ContextMenu
        
        private SearchEngine _engine;
        
        private List<FileItem> _filteredList = new List<FileItem>();
        private List<FileItem> _fullList = new List<FileItem>();

        private string _sortColumn = "Date";
        private bool _sortAscending = false; 
        
        private PerformanceCounter cpuCounter;
        private PerformanceCounter ramCounter;
        private ToolStripStatusLabel lblResourceMon;
        
        public MainForm()
        {
            InitializeUI();
            InitializeContextMenu(); 
            
            string targetBssData = @"\\BSS-DATA\자료폴더";
            _engine = new SearchEngine(targetBssData);
            
            _engine.OnScanProgress += (c) => SafeInvoke(() => {
                lblTotalCount.Text = string.Format("스캐닝 중... {0:N0}건", c);
            });
            
            _engine.OnScanCompleted += (c, ms) => SafeInvoke(() => {
                _fullList = _engine.GetAllItems();
                RefreshFilter(); 
                lblTotalCount.Text = "검색 대기 중...";
                double seconds = ms / 1000.0;
                lblSyncMessage.Text = string.Format("✅ [UltraFast 스캔엔진] 완료: 총 {0:N0}건 캐싱 (초기 소요: {1:F2}초)", c, seconds);
            });
            
            _engine.OnSyncEvent += (type, name) => SafeInvoke(() => {
                _fullList = _engine.GetAllItems();
                RefreshFilter();
                lblSyncMessage.Text = string.Format("⚡ 감시 모드: {0} ({1:HH:mm:ss})", name, DateTime.Now);
            });

            _engine.OnErrorEvent += (msg) => SafeInvoke(() => {
                lblSyncMessage.Text = "❌ 오류: " + msg;
            });

            this.Load += (s, e) => {
                lblSyncMessage.Text = "네트워크 드라이브 스캔 진행 중입니다. 잊시만 기다려주세요...";
                _engine.Start();
                
                // 네트워크 드라이브 FileSystemWatcher 불안정 보완: 60초마다 자동 재스캔
                System.Windows.Forms.Timer autoRefreshTimer = new System.Windows.Forms.Timer();
                autoRefreshTimer.Interval = 60000; // 60초
                autoRefreshTimer.Tick += (autoSender, autoEvent) => {
                    _engine.Refresh();
                };
                autoRefreshTimer.Start();
            };
            
            btnRefresh.Click += (s, e) => {
                lblTotalCount.Text = "수동 스캔 중...";
                _engine.Refresh();
                txtSearch.Focus();
            };

            txtSearch.TextChanged += (s, e) => RefreshFilter();
        }

        // 스레드 안전성 강화를 위한 헬퍼 
        private void SafeInvoke(Action action)
        {
            if (this.IsHandleCreated && !this.IsDisposed)
            {
                this.BeginInvoke(action);
            }
        }

        // 추후 확장 기능을 위한 우클릭 컨텍스트 메뉴 초기화
        private void InitializeContextMenu()
        {
            dgvContextMenu = new ContextMenuStrip();
            dgvContextMenu.Font = new Font("Malgun Gothic", 10);
            
            ToolStripMenuItem itemOpen = new ToolStripMenuItem("▶ 파일 열기");
            itemOpen.Click += (s, e) => ExecuteSelectedAction(FileActionType.Open);
            
            ToolStripMenuItem itemOpenFolder = new ToolStripMenuItem("📂 파일 위치 열기");
            itemOpenFolder.Click += (s, e) => ExecuteSelectedAction(FileActionType.OpenFolder);

            ToolStripMenuItem itemCopyPath = new ToolStripMenuItem("📋 경로 복사");
            itemCopyPath.Click += (s, e) => ExecuteSelectedAction(FileActionType.CopyPath);

            dgvContextMenu.Items.AddRange(new ToolStripItem[] { itemOpen, itemOpenFolder, itemCopyPath });
            dgvResults.ContextMenuStrip = dgvContextMenu;

            // 우클릭 시 해당 행을 선택하도록 이벤트 연결
            dgvResults.CellMouseDown += (s, e) => {
                if (e.Button == MouseButtons.Right && e.RowIndex >= 0)
                {
                    dgvResults.ClearSelection();
                    dgvResults.Rows[e.RowIndex].Selected = true;
                }
            };
        }

        private enum FileActionType { Open, OpenFolder, CopyPath }

        private void ExecuteSelectedAction(FileActionType actionType)
        {
            if (dgvResults.SelectedRows.Count == 0) return;
            int rowIndex = dgvResults.SelectedRows[0].Index;
            if (rowIndex < 0 || rowIndex >= _filteredList.Count) return;
            
            string targetPath = _filteredList[rowIndex].FullPath;
            try 
            {
                switch (actionType)
                {
                    case FileActionType.Open:
                        if (File.Exists(targetPath)) Process.Start(targetPath);
                        else MessageBox.Show("파일이 손실되었습니다.", "오류", MessageBoxButtons.OK, MessageBoxIcon.Warning);
                        break;
                    case FileActionType.OpenFolder:
                        string folderPath = Path.GetDirectoryName(targetPath);
                        if (Directory.Exists(folderPath)) Process.Start("explorer.exe", folderPath);
                        break;
                    case FileActionType.CopyPath:
                        Clipboard.SetText(targetPath);
                        lblSyncMessage.Text = "클립보드에 파일 경로가 복사되었습니다.";
                        break;
                }
            } 
            catch (Exception ex) { MessageBox.Show("실행 오류: " + ex.Message, "오류", MessageBoxButtons.OK, MessageBoxIcon.Error); }
        }

        private void RefreshFilter()
        {
            string query = txtSearch.Text.Trim();
            List<FileItem> temp = null;

            if (string.IsNullOrEmpty(query))
            {
                temp = _fullList; 
            }
            else
            {
                string[] keywords = query.Split(new char[] { ',', ' ' }, StringSplitOptions.RemoveEmptyEntries);
                temp = _fullList.Where(item => 
                    keywords.All(k => 
                        item.FileName.IndexOf(k, StringComparison.OrdinalIgnoreCase) >= 0 ||
                        item.DirectoryName.IndexOf(k, StringComparison.OrdinalIgnoreCase) >= 0
                    )
                ).ToList();
            }

            if (_sortColumn == "No") _filteredList = temp;
            else if (_sortColumn == "Type") _filteredList = _sortAscending ? temp.OrderBy(x => x.TypeTag).ToList() : temp.OrderByDescending(x => x.TypeTag).ToList();
            else if (_sortColumn == "FileName") _filteredList = _sortAscending ? temp.OrderBy(x => x.FileName).ToList() : temp.OrderByDescending(x => x.FileName).ToList();
            else if (_sortColumn == "Path") _filteredList = _sortAscending ? temp.OrderBy(x => x.DirectoryName).ToList() : temp.OrderByDescending(x => x.DirectoryName).ToList();
            else if (_sortColumn == "Date") _filteredList = _sortAscending ? temp.OrderBy(x => x.SortTime).ToList() : temp.OrderByDescending(x => x.SortTime).ToList();
            else if (_sortColumn == "Size") _filteredList = _sortAscending ? temp.OrderBy(x => x.Length).ToList() : temp.OrderByDescending(x => x.Length).ToList();
            else _filteredList = temp.OrderByDescending(x => x.SortTime).ToList();

            dgvResults.RowCount = 0; 
            dgvResults.RowCount = _filteredList.Count;
            dgvResults.Invalidate(); 
            lblTotalCount.Text = string.Format("{0:N0} 건 표출 됨", _filteredList.Count);
        }

        private void InitializeUI()
        {
            this.Text = "농협 방송단 Bss-DATA SEVER 검색기";
            this.Size = new Size(1300, 800);
            this.StartPosition = FormStartPosition.CenterScreen;
            this.Font = new Font("Malgun Gothic", 10);
            
            Color bgDark = Color.FromArgb(10, 15, 30);
            Color panelDark = Color.FromArgb(20, 30, 50);
            Color textLight = Color.FromArgb(230, 240, 255);
            Color textMuted = Color.FromArgb(150, 160, 180);
            Color borderDark = Color.FromArgb(40, 50, 70);
            Color accentBlue = Color.FromArgb(59, 130, 246);

            this.BackColor = bgDark; 

            Panel pnlTop = new Panel() { Height = 120, Dock = DockStyle.Top, BackColor = bgDark };
            Label lblTitle = new Label() { Text = "▶ 농협 방송단 Bss-DATA SEVER 검색기", Font = new Font("Malgun Gothic", 18, FontStyle.Bold), ForeColor = Color.White, Location = new Point(20, 15), AutoSize = true };

            btnRefresh = new Button() { Text = "↻ 수동 스캔 (F5)", Location = new Point(1100, 15), Size = new Size(160, 40), BackColor = panelDark, ForeColor = textLight, FlatStyle = FlatStyle.Flat, Font = new Font("Malgun Gothic", 10, FontStyle.Bold), Cursor = Cursors.Hand };
            btnRefresh.FlatAppearance.BorderColor = borderDark;
            
            Panel pnlSearchInput = new Panel() { Location = new Point(20, 65), Size = new Size(1240, 45), BackColor = panelDark, BorderStyle = BorderStyle.FixedSingle };
            Label lblSearchIcon = new Label() { Text = "🔍", Font = new Font("Malgun Gothic", 14), ForeColor = accentBlue, Location = new Point(10, 8), AutoSize = true };
            
            txtSearch = new TextBox() { Location = new Point(50, 8), Width = 1000, Font = new Font("Malgun Gothic", 14), BorderStyle = BorderStyle.None, BackColor = panelDark, ForeColor = Color.White };
            lblTotalCount = new Label() { Text = "대기 중...", Location = new Point(1080, 12), AutoSize = true, Font = new Font("Malgun Gothic", 9, FontStyle.Bold), ForeColor = Color.LimeGreen, BackColor = Color.Transparent };

            pnlSearchInput.Controls.AddRange(new Control[] { lblSearchIcon, txtSearch, lblTotalCount });
            pnlTop.Controls.AddRange(new Control[] { lblTitle, btnRefresh, pnlSearchInput });

            this.KeyPreview = true;
            this.KeyDown += (s, e) => { if (e.KeyCode == Keys.F5) btnRefresh.PerformClick(); };

            StatusStrip statusStrip = new StatusStrip() { BackColor = panelDark, ForeColor = textMuted };
            statusStrip.Items.Add(new ToolStripStatusLabel() { Text = "🟢 실시간 동기화 감시망 동작 중 | 다중 키워드(,) 조합 검색 지원" });
            ToolStripStatusLabel space = new ToolStripStatusLabel() { Spring = true };
            statusStrip.Items.Add(space);
            lblSyncMessage = new ToolStripStatusLabel() { Text = "스캔 준비 상태", ForeColor = Color.White };
            statusStrip.Items.Add(lblSyncMessage);
            
            lblResourceMon = new ToolStripStatusLabel() { Text = " CPU: 측정 중... | 가용 RAM: 측정 중... ", ForeColor = Color.CornflowerBlue, Font = new Font("Malgun Gothic", 9, FontStyle.Bold) };
            statusStrip.Items.Add(new ToolStripSeparator());
            statusStrip.Items.Add(lblResourceMon);

            try {
                string pName = Process.GetCurrentProcess().ProcessName;
                cpuCounter = new PerformanceCounter("Process", "% Processor Time", pName);
                cpuCounter.NextValue();
                
                System.Windows.Forms.Timer resTimer = new System.Windows.Forms.Timer();
                resTimer.Interval = 1000;
                resTimer.Tick += (sysSender, sysEvent) => {
                    try { 
                        float appCpu = cpuCounter.NextValue() / Environment.ProcessorCount;
                        long appRam = Process.GetCurrentProcess().WorkingSet64 / 1048576; // MB
                        lblResourceMon.Text = string.Format(" App CPU: {0:0.0}% | App RAM: {1:0} MB ", appCpu, appRam); 
                    } catch {}
                };
                resTimer.Start();
            } catch {
                lblResourceMon.Text = " [모니터링 우회됨] ";
            }

            dgvResults = new DataGridView();
            dgvResults.Dock = DockStyle.Fill;
            dgvResults.BackgroundColor = bgDark;
            dgvResults.AllowUserToAddRows = false;
            dgvResults.ReadOnly = true;
            dgvResults.SelectionMode = DataGridViewSelectionMode.FullRowSelect;
            dgvResults.RowHeadersVisible = false;
            dgvResults.BorderStyle = BorderStyle.None;
            dgvResults.AutoSizeColumnsMode = DataGridViewAutoSizeColumnsMode.Fill;
            dgvResults.Font = new Font("Malgun Gothic", 11);
            dgvResults.RowTemplate.Height = 50; 
            
            dgvResults.EnableHeadersVisualStyles = false;
            dgvResults.ColumnHeadersDefaultCellStyle.BackColor = panelDark;
            dgvResults.ColumnHeadersDefaultCellStyle.Font = new Font("Malgun Gothic", 10, FontStyle.Bold);
            dgvResults.ColumnHeadersDefaultCellStyle.ForeColor = textMuted;
            dgvResults.ColumnHeadersDefaultCellStyle.Alignment = DataGridViewContentAlignment.MiddleCenter;
            dgvResults.ColumnHeadersHeight = 40;
            dgvResults.CellBorderStyle = DataGridViewCellBorderStyle.SingleHorizontal;
            dgvResults.GridColor = borderDark;
            dgvResults.DefaultCellStyle.BackColor = bgDark;
            dgvResults.DefaultCellStyle.ForeColor = textLight;
            dgvResults.DefaultCellStyle.SelectionBackColor = borderDark; 
            dgvResults.DefaultCellStyle.SelectionForeColor = Color.White;
            dgvResults.ShowCellToolTips = true; 
            
            dgvResults.VirtualMode = true;
            dgvResults.CellValueNeeded += DgvResults_CellValueNeeded;
            dgvResults.CellFormatting += DgvResults_CellFormatting;
            dgvResults.ColumnHeaderMouseClick += DgvResults_ColumnHeaderMouseClick;
            dgvResults.CellDoubleClick += DgvResults_CellDoubleClick;

            dgvResults.Columns.Add("No", "NO");
            dgvResults.Columns["No"].FillWeight = 4;
            dgvResults.Columns["No"].DefaultCellStyle.Alignment = DataGridViewContentAlignment.MiddleCenter;
            dgvResults.Columns["No"].DefaultCellStyle.ForeColor = textMuted;
            dgvResults.Columns.Add("Type", "포맷 ▲▼");
            dgvResults.Columns["Type"].Name = "Type";
            dgvResults.Columns["Type"].FillWeight = 8;
            dgvResults.Columns["Type"].DefaultCellStyle.Alignment = DataGridViewContentAlignment.MiddleCenter;
            dgvResults.Columns.Add("FileName", "자료명 ▲▼");
            dgvResults.Columns["FileName"].Name = "FileName";
            dgvResults.Columns["FileName"].FillWeight = 52;
            dgvResults.Columns.Add("Path", "세부 경로 ▲▼");
            dgvResults.Columns["Path"].Name = "Path";
            dgvResults.Columns["Path"].FillWeight = 16;
            dgvResults.Columns["Path"].DefaultCellStyle.ForeColor = textMuted;
            dgvResults.Columns.Add("Date", "수정 일시 ▲▼");
            dgvResults.Columns["Date"].Name = "Date";
            dgvResults.Columns["Date"].FillWeight = 13;
            dgvResults.Columns["Date"].DefaultCellStyle.Alignment = DataGridViewContentAlignment.MiddleCenter;
            dgvResults.Columns["Date"].DefaultCellStyle.ForeColor = textMuted;
            dgvResults.Columns.Add("Size", "용량 ▲▼");
            dgvResults.Columns["Size"].Name = "Size";
            dgvResults.Columns["Size"].FillWeight = 7;
            dgvResults.Columns["Size"].DefaultCellStyle.Alignment = DataGridViewContentAlignment.MiddleRight;
            dgvResults.Columns["Size"].DefaultCellStyle.ForeColor = textMuted;

            Panel pnlGridWrap = new Panel() { Dock = DockStyle.Fill };
            pnlGridWrap.Padding = new Padding(20, 0, 20, 10);
            pnlGridWrap.Controls.Add(dgvResults);

            this.Controls.Add(pnlGridWrap);
            this.Controls.Add(statusStrip);
            this.Controls.Add(pnlTop);
        }

        private void DgvResults_CellDoubleClick(object sender, DataGridViewCellEventArgs e)
        {
            ExecuteSelectedAction(FileActionType.Open);
        }

        private void DgvResults_ColumnHeaderMouseClick(object sender, DataGridViewCellMouseEventArgs e)
        {
            string colName = dgvResults.Columns[e.ColumnIndex].Name;
            if (_sortColumn == colName) _sortAscending = !_sortAscending; 
            else {
                _sortColumn = colName;
                if (colName == "Date" || colName == "Size") _sortAscending = false; 
                else _sortAscending = true; 
            }
            RefreshFilter(); 
        }

        private void DgvResults_CellValueNeeded(object sender, DataGridViewCellValueEventArgs e)
        {
            if (e.RowIndex < 0 || e.RowIndex >= _filteredList.Count) return;
            FileItem item = _filteredList[e.RowIndex];
            switch (e.ColumnIndex)
            {
                case 0: e.Value = (e.RowIndex + 1).ToString(); break;
                case 1: e.Value = string.IsNullOrEmpty(item.Extension) ? "FILE" : item.Extension.Replace(".", "").ToUpper(); break;
                case 2: e.Value = item.FileName; break;
                case 3: e.Value = item.DirectoryName; break;
                case 4: e.Value = item.DisplayDate; break;
                case 5: e.Value = item.DisplaySize; break;
            }
        }

        private void DgvResults_CellFormatting(object sender, DataGridViewCellFormattingEventArgs e)
        {
            if (e.ColumnIndex == 1 && e.RowIndex >= 0 && e.RowIndex < _filteredList.Count) 
            {
                string tag = _filteredList[e.RowIndex].TypeTag;
                if(tag == "VIDEO" || tag == "AUDIO") e.CellStyle.ForeColor = Color.FromArgb(59, 130, 246);
                else if(tag == "EXCEL") e.CellStyle.ForeColor = Color.FromArgb(16, 185, 129);
                else if(tag == "DOC") e.CellStyle.ForeColor = Color.FromArgb(14, 165, 233);
                else if(tag == "HWP") e.CellStyle.ForeColor = Color.FromArgb(0, 191, 255);
                else if(tag == "PPT") e.CellStyle.ForeColor = Color.FromArgb(239, 68, 68);
                else if(tag == "IMAGE") e.CellStyle.ForeColor = Color.FromArgb(249, 115, 22);
                else e.CellStyle.ForeColor = Color.Gray;
            }
        }
    }
    #endregion
}
