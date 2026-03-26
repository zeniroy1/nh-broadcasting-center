using System;
using System.Drawing;
using System.Drawing.Drawing2D;
using System.IO;

class C {
    static void Main() {
        string inPath = @"C:\Users\hamcoding\.gemini\antigravity\brain\120d1208-ef3a-499e-a230-f981084b6d09\nh_media_icon_navy_1774243860945.png";
        string outPath = @"C:\Users\hamcoding\Desktop\codding\new folder\녹음녹화 반출 자동화\app_icon_rounded.ico";
        
        int r = 35; 
        int s = 256;
        
        using (Bitmap raw = new Bitmap(inPath))
        using (Bitmap bmp = new Bitmap(s, s)) {
            using (Graphics g = Graphics.FromImage(bmp)) {
                g.SmoothingMode = SmoothingMode.AntiAlias;
                g.InterpolationMode = InterpolationMode.HighQualityBicubic;
                g.Clear(Color.Transparent);
                
                using (GraphicsPath path = new GraphicsPath()) {
                    path.AddArc(0, 0, r*2, r*2, 180, 90);
                    path.AddArc(s - r*2, 0, r*2, r*2, 270, 90);
                    path.AddArc(s - r*2, s - r*2, r*2, r*2, 0, 90);
                    path.AddArc(0, s - r*2, r*2, r*2, 90, 90);
                    path.CloseFigure();
                    
                    g.SetClip(path);
                    g.DrawImage(raw, 0, 0, s, s);
                }
            }
            
            using (FileStream fs = new FileStream(outPath, FileMode.Create)) {
                fs.Write(new byte[] { 0, 0, 1, 0, 1, 0, 0, 0, 0, 0, 1, 0, 32, 0, 0, 0, 0, 0, 22, 0, 0, 0 }, 0, 22);
                using (MemoryStream ms = new MemoryStream()) {
                    bmp.Save(ms, System.Drawing.Imaging.ImageFormat.Png);
                    int len = (int)ms.Length;
                    fs.Seek(14, SeekOrigin.Begin);
                    fs.Write(BitConverter.GetBytes(len), 0, 4);
                    fs.Seek(22, SeekOrigin.Begin);
                    ms.WriteTo(fs);
                }
            }
        }
    }
}
