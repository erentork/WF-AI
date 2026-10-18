"""Builds the native Windows application WF-AI.exe with embedded icon and Task Manager identity.

How it works:
1. Generates assets/wf-ai.ico (multi-size high-DPI Cephalon diamond icon).
2. Compiles WF-AI.exe using the built-in Windows .NET C# compiler (csc.exe) with:
   - Embedded icon (assets/wf-ai.ico)
   - AssemblyTitle / FileDescription = "WF-AI" (shown in Task Manager "Processes" tab)
   - Dynamic discovery of Python base path from .venv/pyvenv.cfg
   - In-process hosting of Python DLL (python3XX.dll via LoadLibrary + Py_Main) so there is
     NO separate python.exe / pythonw.exe process at all! The only running process is WF-AI.exe.
"""
import os
import subprocess
from pathlib import Path

from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parent.parent
ASSETS = ROOT / "assets"
ICO_PATH = ASSETS / "wf-ai.ico"
ROOT_EXE = ROOT / "WF-AI.exe"


def generate_ico() -> Path:
    ASSETS.mkdir(parents=True, exist_ok=True)
    size = 256
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)

    # Outer dark cyber disc with cyan glow border
    d.ellipse((12, 12, size - 12, size - 12), fill=(8, 13, 24, 245), outline=(34, 211, 238, 255), width=8)
    # Inner subtle ring
    d.ellipse((34, 34, size - 34, size - 34), fill=None, outline=(168, 85, 247, 190), width=4)

    # Cephalon outer diamond
    cx, cy = size // 2, size // 2
    r_out = 78
    d.polygon(
        [(cx, cy - r_out), (cx + r_out, cy), (cx, cy + r_out), (cx - r_out, cy)],
        fill=(14, 116, 144, 180),
        outline=(34, 211, 238, 255),
    )
    # Inner bright core diamond
    r_in = 40
    d.polygon(
        [(cx, cy - r_in), (cx + r_in, cy), (cx, cy + r_in), (cx - r_in, cy)],
        fill=(165, 243, 252, 255),
    )

    img.save(
        ICO_PATH,
        format="ICO",
        sizes=[(256, 256), (128, 128), (64, 64), (48, 48), (32, 32), (16, 16)],
    )
    return ICO_PATH


CSHARP_SOURCE = r"""
using System;
using System.Diagnostics;
using System.IO;
using System.Reflection;
using System.Runtime.InteropServices;

[assembly: AssemblyTitle("WF-AI")]
[assembly: AssemblyDescription("WF-AI")]
[assembly: AssemblyProduct("WF-AI — Warframe AI Overlay Assistant")]
[assembly: AssemblyCompany("Tenno Cephalon")]
[assembly: AssemblyVersion("1.0.0.0")]
[assembly: AssemblyFileVersion("1.0.0.0")]

class Program {
    [DllImport("shell32.dll", CharSet = CharSet.Unicode)]
    static extern int SetCurrentProcessExplicitAppUserModelID(string AppID);

    [DllImport("kernel32.dll", CharSet = CharSet.Unicode, SetLastError = true)]
    static extern IntPtr LoadLibraryW(string lpFileName);

    [DllImport("kernel32.dll", CharSet = CharSet.Unicode, SetLastError = true)]
    static extern bool SetDllDirectoryW(string lpPathName);

    [DllImport("kernel32.dll", CharSet = CharSet.Ansi, SetLastError = true)]
    static extern IntPtr GetProcAddress(IntPtr hModule, string procName);

    [UnmanagedFunctionPointer(CallingConvention.Cdecl)]
    delegate int Py_MainDelegate(
        int argc,
        [MarshalAs(UnmanagedType.LPArray, ArraySubType = UnmanagedType.LPWStr)] string[] argv
    );

    static string FindPythonBaseDir(string root) {
        string cfg = Path.Combine(root, ".venv", "pyvenv.cfg");
        if (!File.Exists(cfg)) return null;
        foreach (string line in File.ReadAllLines(cfg)) {
            int eq = line.IndexOf('=');
            if (eq > 0) {
                string key = line.Substring(0, eq).Trim().ToLowerInvariant();
                if (key == "home") {
                    return line.Substring(eq + 1).Trim();
                }
            }
        }
        return null;
    }

    static string FindPythonDll(string baseDir) {
        if (string.IsNullOrEmpty(baseDir) || !Directory.Exists(baseDir)) return null;
        string best = null;
        foreach (string f in Directory.GetFiles(baseDir, "python3*.dll")) {
            string name = Path.GetFileName(f).ToLowerInvariant();
            if (name != "python3.dll") {
                if (best == null || f.Length > best.Length) best = f;
            }
        }
        return best;
    }

    static int Main(string[] args) {
        try { SetCurrentProcessExplicitAppUserModelID("Tenno.WFAI.Overlay.1"); } catch {}

        string root = AppDomain.CurrentDomain.BaseDirectory;
        Directory.SetCurrentDirectory(root);

        string venvSite = Path.Combine(root, ".venv", "Lib", "site-packages");
        string installedFlag = Path.Combine(root, ".venv", ".installed");
        string mainPy = Path.Combine(root, "src", "main.py");
        string pyBaseDir = FindPythonBaseDir(root);
        string pyDllPath = FindPythonDll(pyBaseDir);

        if (!Directory.Exists(venvSite) || !File.Exists(installedFlag) || string.IsNullOrEmpty(pyDllPath)) {
            string bat = Path.Combine(root, "setup_and_run.bat");
            if (File.Exists(bat)) {
                Process.Start(new ProcessStartInfo {
                    FileName = bat,
                    WorkingDirectory = root,
                    UseShellExecute = true
                });
                return 0;
            }
            return 1;
        }

        Environment.SetEnvironmentVariable("PYTHONHOME", pyBaseDir);
        Environment.SetEnvironmentVariable("VIRTUAL_ENV", Path.Combine(root, ".venv"));
        string pyPath = Path.Combine(root, "src") + ";" + venvSite + ";" +
                        Path.Combine(pyBaseDir, "DLLs") + ";" + Path.Combine(pyBaseDir, "Lib");
        Environment.SetEnvironmentVariable("PYTHONPATH", pyPath);
        Environment.SetEnvironmentVariable("PATH",
            Path.Combine(root, ".venv", "Scripts") + ";" + pyBaseDir + ";" +
            Environment.GetEnvironmentVariable("PATH"));

        SetDllDirectoryW(pyBaseDir);
        IntPtr hPy = LoadLibraryW(pyDllPath);
        if (hPy == IntPtr.Zero) return 2;

        IntPtr pPyMain = GetProcAddress(hPy, "Py_Main");
        if (pPyMain == IntPtr.Zero) return 3;

        var pyMain = (Py_MainDelegate)Marshal.GetDelegateForFunctionPointer(pPyMain, typeof(Py_MainDelegate));
        string[] pyArgv;
        if (args != null && args.Length > 0) {
            pyArgv = new string[args.Length + 1];
            pyArgv[0] = Path.Combine(root, "WF-AI.exe");
            Array.Copy(args, 0, pyArgv, 1, args.Length);
        } else {
            pyArgv = new string[] { Path.Combine(root, "WF-AI.exe"), mainPy };
        }
        return pyMain(pyArgv.Length, pyArgv);
    }
}
"""


def compile_root_launcher() -> Path:
    csc_candidates = [
        r"C:\Windows\Microsoft.NET\Framework64\v4.0.30319\csc.exe",
        r"C:\Windows\Microsoft.NET\Framework\v4.0.30319\csc.exe",
    ]
    csc = next((p for p in csc_candidates if os.path.exists(p)), None)
    if not csc:
        raise RuntimeError("csc.exe bulunamadı")

    cs_file = ASSETS / "launcher.cs"
    cs_file.write_text(CSHARP_SOURCE.strip(), encoding="utf-8")
    try:
        cmd = [
            csc,
            "/nologo",
            "/target:winexe",
            "/platform:x64",
            "/optimize+",
            f"/out:{ROOT_EXE}",
            f"/win32icon:{ICO_PATH}",
            str(cs_file),
        ]
        subprocess.run(cmd, check=True, capture_output=True, text=True)
    finally:
        if cs_file.exists():
            cs_file.unlink()
    return ROOT_EXE


def main():
    ico = generate_ico()
    exe = compile_root_launcher()
    print(f"Built {exe.name} and {ico.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
