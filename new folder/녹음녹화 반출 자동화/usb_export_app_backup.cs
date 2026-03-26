using System;
using System.IO;
using System.Linq;
using System.Windows.Forms;
using System.Drawing;
using System.Collections.Generic;
using System.Threading.Tasks;

namespace NHMediaExportTool
{
    /// <summary>
    /// 향후 네트워크 경로 변경이나 타이틀 수정 등 환경 설정 값들을 중앙에서 관리하는 설정 클래스입니다.
    /// </summary>
    static class AppConfig
    {
        public const string AppName = "농협 방송실 녹음녹화파일 반출 도구 v1.1";
        public const string TargetNetworkPath = @"\\BSS-DATA\자료폴더\07. 녹음녹화파일";
        public const string LogFileName = "반출대장_자동기록.txt";
    }

    class MainForm : Form
    {
        #region UI 구성 요소 선언 (Fields)
        private TextBox txtSearch;
        private Button btnRefresh;
        private ListBox lstFolders;
        private ListBox lstFiles;
        private ComboBox cboUsb;
        private TextBox txtUsbFolder;
        private Button btnBrowseFolder;
        private Button btnExport;
        private ProgressBar pbProgress;
        private Label lblStatus;
        #endregion

        // 데이터 캐싱 및 현재 작업 경로
        private string currentNetPath = AppConfig.TargetNetworkPath;
        private List<string> folderCache = new List<string>();

        public MainForm()
        {
            InitializeUI();
            InitializeEventHandlers();
        }

        #region 초기화 및 UI 설정 (Initialization)
        
        /// <summary>
        /// 폼 및 모든 UI 컨트롤의 위치/크기/속성을 배치합니다.
        /// 미래의 UI 업데이트 시 이 메서드 안에서만 수정하면 레이아웃 충돌 방지가 가능합니다.
        /// </summary>
        private void InitializeUI()
        {
            this.Text = AppConfig.AppName;
            this.Size = new Size(800, 520);
            this.StartPosition = FormStartPosition.CenterScreen;
            this.Font = new Font("Malgun Gothic", 10);
            this.FormBorderStyle = FormBorderStyle.FixedDialog;
            this.MaximizeBox = false;
            
            Label lblSearch = new Label() { Text = "🔍 실시간 검색어 입력 (이전/폐기 자료 자동 포함):", Location = new Point(20, 20), AutoSize = true, Font = new Font("Malgun Gothic", 10, FontStyle.Bold) };
            txtSearch = new TextBox() { Location = new Point(20, 45), Width = 640, Font = new Font("Malgun Gothic", 12) };
            btnRefresh = new Button() { Text = "🔄 목록 갱신", Location = new Point(670, 44), Size = new Size(95, 29), Font = new Font("Malgun Gothic", 9, FontStyle.Bold), Cursor = Cursors.Hand };
            
            Label lblRes = new Label() { Text = "📂 검색 결과 선택 (폴더):", Location = new Point(20, 85), AutoSize = true, Font = new Font("Malgun Gothic", 10, FontStyle.Bold) };
            lstFolders = new ListBox() { Location = new Point(20, 110), Size = new Size(360, 150), Font = new Font("Malgun Gothic", 11), HorizontalScrollbar = true };
            
            Label lblFiles = new Label() { Text = "📄 폴더 내 파일 (더블클릭 시 바로 재생/실행):", Location = new Point(400, 85), AutoSize = true, Font = new Font("Malgun Gothic", 10, FontStyle.Bold), ForeColor = Color.DarkRed };
            lstFiles = new ListBox() { Location = new Point(400, 110), Size = new Size(365, 150), Font = new Font("Malgun Gothic", 11), HorizontalScrollbar = true };
            
            Label lblUsb = new Label() { Text = "💾 대상 USB:", Location = new Point(20, 280), AutoSize = true, Font = new Font("Malgun Gothic", 10, FontStyle.Bold) };
            cboUsb = new ComboBox() { Location = new Point(125, 277), Width = 255, DropDownStyle = ComboBoxStyle.DropDownList };
            
            Label lblFolder = new Label() { Text = "USB 내 저장 폴더:", Location = new Point(400, 280), AutoSize = true, Font = new Font("Malgun Gothic", 10, FontStyle.Bold) };
            txtUsbFolder = new TextBox() { Location = new Point(540, 277), Width = 150, Font = new Font("Malgun Gothic", 10) };
            btnBrowseFolder = new Button() { Text = "찾아보기", Location = new Point(695, 275), Size = new Size(70, 26), Font = new Font("Malgun Gothic", 9), Cursor = Cursors.Hand };
            
            btnExport = new Button() { Text = "USB로 내보내기 (복사 시작)", Location = new Point(20, 320), Size = new Size(745, 50), BackColor = Color.DodgerBlue, ForeColor = Color.White, Font = new Font("Malgun Gothic", 12, FontStyle.Bold), Cursor = Cursors.Hand };
            
            pbProgress = new ProgressBar() { Location = new Point(20, 385), Size = new Size(745, 25) };
            lblStatus = new Label() { Text = "대기 중...", Location = new Point(20, 420), Size = new Size(745, 40), ForeColor = Color.DimGray };
            
            this.Controls.AddRange(new Control[] { 
                lblSearch, txtSearch, btnRefresh, 
                lblRes, lstFolders, lblFiles, lstFiles, 
                lblUsb, cboUsb, lblFolder, txtUsbFolder, btnBrowseFolder, 
                btnExport, pbProgress, lblStatus 
            });
        }

        /// <summary>
        /// 이벤트 핸들러를 연결합니다.
        /// </summary>
        private void InitializeEventHandlers()
        {
            this.Load += MainForm_Load;
            txtSearch.TextChanged += (s, e) => FilterResults();
            btnRefresh.Click += (s, e) => AutoRefreshUI();
            lstFolders.SelectedIndexChanged += LstFolders_SelectedIndexChanged;
            lstFiles.DoubleClick += LstFiles_DoubleClick;
            btnBrowseFolder.Click += BtnBrowseFolder_Click;
            btnExport.Click += BtnExport_Click;
        }

        private async void MainForm_Load(object sender, EventArgs e)
        {
            lblStatus.Text = "네트워크 드라이브 목록을 불러오는 중입니다...";
            await FetchFoldersAsync();
            RefreshUSBList();
            FilterResults();
            lblStatus.Text = "대기 중... 검색어를 입력하고 폴더를 선택하세요.";

            // 실시간 파일 변경 감지 시작
            StartDirectoryMonitoring();
        }

        private void StartDirectoryMonitoring()
        {
            try
            {
                if (!Directory.Exists(currentNetPath)) return;
                
                FileSystemWatcher watcher = new FileSystemWatcher()
                {
                    Path = currentNetPath,
                    NotifyFilter = NotifyFilters.DirectoryName,
                    EnableRaisingEvents = true
                };

                watcher.Created += (s, e) => this.Invoke((MethodInvoker)AutoRefreshUI);
                watcher.Renamed += (s, e) => this.Invoke((MethodInvoker)AutoRefreshUI);
                watcher.Deleted += (s, e) => this.Invoke((MethodInvoker)AutoRefreshUI);
            }
            catch
            {
                // 권한 부족 등의 이유로 모니터링 실패 시 무시하고 수동 새로고침만 사용
            }
        }
        #endregion

        #region 데이터 로드 및 갱신 로직 (Data & Updates)
        
        async void AutoRefreshUI()
        {
            SetControlEnabledState(false);
            lblStatus.Text = "🔔 네트워크 파일 갱신 중...";
            lblStatus.ForeColor = Color.Black;
            pbProgress.Value = 0;
            
            await Task.Delay(200); // UI 안정화용 대기
            await FetchFoldersAsync();
            FilterResults();
            
            lblStatus.Text = "✅ 실시간 자동 동기화 완료!";
            lblStatus.ForeColor = Color.Green;
            pbProgress.Value = 100;
            
            SetControlEnabledState(true);
            
            await Task.Delay(3000); 
            if (lblStatus.Text.Contains("동기화 완료"))
            {
                lblStatus.Text = "대기 중... 검색어를 입력하고 폴더를 선택하세요.";
                lblStatus.ForeColor = Color.DimGray;
                pbProgress.Value = 0;
            }
        }
        
        async Task FetchFoldersAsync()
        {
            await Task.Run(() =>
            {
                try
                {
                    if (!Directory.Exists(currentNetPath)) return;
                    folderCache.Clear();
                    
                    // 최상위 폴더 수집 (#으로 시작하지 않는 일반 자료)
                    var rootDirs = Directory.GetDirectories(currentNetPath).Where(d => !Path.GetFileName(d).StartsWith("#"));
                    foreach(var d in rootDirs) folderCache.Add(Path.GetFileName(d));
                    
                    // #지난자료 하위 탐색
                    string pastPath = Path.Combine(currentNetPath, "#지난자료");
                    if (Directory.Exists(pastPath)) TraverseSafe(pastPath, "#지난자료");
                    
                    // ##폐기파일 하위 탐색
                    string delPath = Path.Combine(currentNetPath, "##폐기파일");
                    if (Directory.Exists(delPath)) TraverseSafe(delPath, "##폐기파일");
                }
                catch { }
            });
        }

        /// <summary>
        /// 권한 에러를 회피하며 안전하게 재귀적으로 하위 폴더를 스캔합니다.
        /// </summary>
        private void TraverseSafe(string path, string prefix)
        {
            try
            {
                foreach (var dir in Directory.GetDirectories(path))
                {
                    string name = Path.GetFileName(dir);
                    string newPrefix = string.Format("{0}\\{1}", prefix, name);
                    folderCache.Add(newPrefix);
                    TraverseSafe(dir, newPrefix); 
                }
            }
            catch { }
        }

        private void FilterResults()
        {
            lstFolders.Items.Clear();
            string keyword = txtSearch.Text.ToLower();
            
            var matches = folderCache.Where(f => f.ToLower().Contains(keyword)).ToList();
            if (matches.Count == 0 && folderCache.Count == 0)
                matches.Add("네트워크(BSS-DATA) 연결 실패 (파일을 찾을 수 없습니다)");
                
            foreach (var m in matches) lstFolders.Items.Add(m);
            if (lstFolders.Items.Count > 0) lstFolders.SelectedIndex = 0;
        }

        private void RefreshUSBList()
        {
            cboUsb.Items.Clear();
            // C 드라이브를 제외한 이동식/고정식 디스크 검색
            var validDrives = DriveInfo.GetDrives().Where(d => d.IsReady && d.Name.ToUpper() != @"C:\");
            foreach (var drive in validDrives)
            {
                if (drive.DriveType == DriveType.Removable || drive.DriveType == DriveType.Fixed)
                {
                    cboUsb.Items.Add(string.Format("{0} ({1})", drive.Name, drive.VolumeLabel));
                }
            }
            if (cboUsb.Items.Count > 0) cboUsb.SelectedIndex = 0;
            else cboUsb.Items.Add("⚠️ USB(또는 외장하드)를 연결해 주세요.");
        }
        
        protected override void WndProc(ref Message m)
        {
            base.WndProc(ref m);
            const int WM_DEVICECHANGE = 0x0219;
            if (m.Msg == WM_DEVICECHANGE) RefreshUSBList(); // USB 삽입/제거 시 장치 자동 갱신
        }
        #endregion

        #region UI 이벤트 핸들링 (Event Handlers)
        
        private void LstFolders_SelectedIndexChanged(object sender, EventArgs e)
        {
            lstFiles.Items.Clear();
            if (lstFolders.SelectedItem == null) return;
            
            string rawTarget = lstFolders.SelectedItem.ToString();
            if (rawTarget.Contains("연결 실패")) return;
            
            string srcPath = Path.Combine(currentNetPath, rawTarget);
            if (!Directory.Exists(srcPath))
            {
                lstFiles.Items.Add("(폴더를 찾을 수 없음)");
                return;
            }

            try
            {
                var files = Directory.GetFiles(srcPath, "*.*", SearchOption.AllDirectories);
                foreach(var f in files)
                {
                    lstFiles.Items.Add(f.Substring(srcPath.Length + 1));
                }
                if (files.Length == 0) lstFiles.Items.Add("(파일 없음)");
            }
            catch
            {
                lstFiles.Items.Add("(접근 권한 없음 또는 에러)");
            }
        }

        private void LstFiles_DoubleClick(object sender, EventArgs e)
        {
            if (lstFiles.SelectedItem == null) return;
            
            string selFile = lstFiles.SelectedItem.ToString();
            if (selFile.StartsWith("(")) return;
            if (lstFolders.SelectedItem == null) return;
            
            string rawTarget = lstFolders.SelectedItem.ToString();
            string fullPath = Path.Combine(currentNetPath, rawTarget, selFile);
            
            if (File.Exists(fullPath))
            {
                try
                {
                    System.Diagnostics.Process.Start(new System.Diagnostics.ProcessStartInfo()
                    {
                        FileName = fullPath,
                        UseShellExecute = true // OS 기본 연결 프로그램으로 실행
                    });
                }
                catch (Exception ex)
                {
                    MessageBox.Show("파일을 실행할 수 없습니다.\n" + ex.Message, "오류", MessageBoxButtons.OK, MessageBoxIcon.Error);
                }
            }
        }

        private void BtnBrowseFolder_Click(object sender, EventArgs e)
        {
            if (cboUsb.SelectedItem == null)
            {
                MessageBox.Show("먼저 대상 USB를 선택해 주세요.", "알림", MessageBoxButtons.OK, MessageBoxIcon.Information);
                return;
            }
            
            string usbLine = cboUsb.SelectedItem.ToString();
            if (!usbLine.Contains(":\\")) return;
            
            string usbDrive = usbLine.Substring(0, 3);
            
            using (FolderBrowserDialog fbd = new FolderBrowserDialog())
            {
                fbd.Description = "USB 내에서 저장할 폴더를 선택하세요.";
                fbd.SelectedPath = usbDrive;
                if (fbd.ShowDialog() == DialogResult.OK)
                {
                    string selectedPath = fbd.SelectedPath;
                    // 선택된 경로가 USB 내부에 있는지 유효성 검증
                    if (selectedPath.StartsWith(usbDrive, StringComparison.OrdinalIgnoreCase))
                    {
                        string subPath = selectedPath.Substring(usbDrive.Length);
                        if (subPath.StartsWith("\\")) subPath = subPath.Substring(1);
                        txtUsbFolder.Text = subPath;
                    }
                    else
                    {
                        MessageBox.Show("반드시 선택한 USB 드라이브 내부의 폴더를 지정해야 합니다.", "알림", MessageBoxButtons.OK, MessageBoxIcon.Warning);
                    }
                }
            }
        }
        #endregion

        #region 반출 실행 로직 (Export Execution)
        
        private async void BtnExport_Click(object sender, EventArgs e)
        {
            if (lstFolders.SelectedItem == null)
            {
                MessageBox.Show("목록에서 내보낼 폴더를 선택해주세요.", "알림", MessageBoxButtons.OK, MessageBoxIcon.Information);
                return;
            }
            
            string rawTarget = lstFolders.SelectedItem.ToString();
            if (rawTarget.Contains("연결 실패")) return;
            
            // "지난자료\폴더명" 등에서 순수 폴더 이름 분리
            string cleanTarget = rawTarget;
            if (cleanTarget.Contains("\\"))
            {
                string[] parts = cleanTarget.Split('\\');
                cleanTarget = parts[parts.Length - 1];
            }
            
            // 목적지 경로 구성
            string usbLine = cboUsb.Text;
            if (!usbLine.Contains(":\\"))
            {
                RefreshUSBList();
                usbLine = cboUsb.Text;
                if (!usbLine.Contains(":\\"))
                {
                    MessageBox.Show("USB 드라이브를 찾을 수 없습니다. 삽입 여부를 확인하세요.", "오류", MessageBoxButtons.OK, MessageBoxIcon.Error); 
                    return; 
                }
            }
            
            string usbDrive = usbLine.Substring(0, 3);
            string srcPath = Path.Combine(currentNetPath, rawTarget);
            
            string subFolder = txtUsbFolder.Text.Trim();
            if (subFolder.StartsWith("\\") || subFolder.StartsWith("/"))
                subFolder = subFolder.Substring(1);
                
            string destPath = Path.Combine(usbDrive, subFolder, cleanTarget);

            if (!Directory.Exists(srcPath))
            {
                MessageBox.Show("원본 폴더를 찾을 수 없습니다: " + srcPath, "오류", MessageBoxButtons.OK, MessageBoxIcon.Error);
                return;
            }

            if (Directory.Exists(destPath))
            {
                var res = MessageBox.Show(string.Format("[알림] 이미 USB안에 동일한 이름의 '{0}' 폴더가 존재합니다.\n\n기존 폴더를 무시하고 덮어쓰시겠습니까?", cleanTarget), "중복 폴더 복사 알림", MessageBoxButtons.YesNo, MessageBoxIcon.Warning);
                if (res == DialogResult.No)
                {
                    lblStatus.Text = "취소되었습니다.";
                    return;
                }
            }

            // 복사 중 UI 비활성화
            SetControlEnabledState(false);
            pbProgress.Value = 0;
            pbProgress.Style = ProgressBarStyle.Blocks;
            lblStatus.Text = string.Format("{0} 복사 준비 중...", cleanTarget);
            lblStatus.ForeColor = Color.Black;
            
            // 실제 파일 복사 IO 워커
            await RunCopyProcessAsync(srcPath, destPath, cleanTarget);
            
            // 복사 완료 후 UI 활성화
            SetControlEnabledState(true);
        }

        private async Task RunCopyProcessAsync(string srcPath, string destPath, string cleanTarget)
        {
            await Task.Run(() =>
            {
                try
                {
                    if (Directory.Exists(destPath)) Directory.Delete(destPath, true);
                    Directory.CreateDirectory(destPath);
                    
                    var files = Directory.GetFiles(srcPath, "*.*", SearchOption.AllDirectories);
                    long totalBytes = files.Sum(f => new FileInfo(f).Length);
                    long copiedBytes = 0;
                    
                    if (totalBytes == 0) totalBytes = 1;
                    if (files.Length == 0) this.Invoke((MethodInvoker)delegate { pbProgress.Value = 100; });

                    foreach (string file in files)
                    {
                        string relPath = file.Substring(srcPath.Length + 1);
                        string destFile = Path.Combine(destPath, relPath);
                        Directory.CreateDirectory(Path.GetDirectoryName(destFile));
                        
                        this.Invoke((MethodInvoker)delegate { lblStatus.Text = string.Format("현재 복사 중: {0}", Path.GetFileName(file)); });
                        
                        using (var fs = new FileStream(file, FileMode.Open, FileAccess.Read))
                        using (var fd = new FileStream(destFile, FileMode.Create, FileAccess.Write))
                        {
                            byte[] buffer = new byte[2 * 1024 * 1024]; // 2MB 버퍼링 최적화
                            int read;
                            while ((read = fs.Read(buffer, 0, buffer.Length)) > 0)
                            {
                                fd.Write(buffer, 0, read);
                                copiedBytes += read;
                                int pct = (int)((copiedBytes * 100) / totalBytes);
                                this.Invoke((MethodInvoker)delegate { pbProgress.Value = pct; });
                            }
                        }
                    }
                    
                    // 내역을 로그 파일로 기록
                    AppendExportLog(cleanTarget);

                    this.Invoke((MethodInvoker)delegate { 
                        lblStatus.Text = "✔️ 복사 및 로그 기록 완료! USB 안전 제거 가능"; 
                        lblStatus.ForeColor = Color.Green;
                        pbProgress.Value = 100;
                    });
                }
                catch (Exception ex)
                {
                    this.Invoke((MethodInvoker)delegate { 
                        MessageBox.Show("복사 중 에러: " + ex.Message, "IO 심각한 오류", MessageBoxButtons.OK, MessageBoxIcon.Error); 
                        lblStatus.Text = "복사 중 에러 발생!"; 
                    });
                }
            });
        }

        private void AppendExportLog(string folderName)
        {
            try
            {
                string logFile = Path.Combine(currentNetPath, AppConfig.LogFileName);
                string logEntry = string.Format("[{0}] 반출 항목: {1}\r\n", DateTime.Now.ToString("yyyy-MM-dd HH:mm:ss"), folderName);
                File.AppendAllText(logFile, logEntry);
            }
            catch { /* 로깅 실패 시 프로그램 중단 금지 */ }
        }

        /// <summary>
        /// 처리 중 사용자 입력을 차단하거나 해제하기 위한 상태 토글 헬퍼입니다.
        /// </summary>
        private void SetControlEnabledState(bool state)
        {
            btnExport.Enabled = state;
            cboUsb.Enabled = state;
            txtUsbFolder.Enabled = state;
            btnBrowseFolder.Enabled = state;
            txtSearch.Enabled = state;
            btnRefresh.Enabled = state;
            lstFolders.Enabled = state;
            lstFiles.Enabled = state;
        }
        #endregion
    }
}

static class Program
{
    [STAThread]
    static void Main()
    {
        Application.EnableVisualStyles();
        Application.SetCompatibleTextRenderingDefault(false);
        Application.Run(new NHMediaExportTool.MainForm());
    }
}
