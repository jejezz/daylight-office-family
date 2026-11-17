param(
  [Parameter(Mandatory)] [string[]]$Exe,
  [Parameter(Mandatory)] [string]$Ico,
  [long]$OnlyGroup = 0
)
Add-Type -TypeDefinition @'
using System; using System.Collections.Generic; using System.IO; using System.Runtime.InteropServices;
public static class PeIcon {
  delegate bool EnumNameProc(IntPtr h, IntPtr type, IntPtr name, IntPtr l);
  delegate bool EnumLangProc(IntPtr h, IntPtr type, IntPtr name, ushort lang, IntPtr l);
  [DllImport("kernel32.dll", SetLastError=true, CharSet=CharSet.Unicode)] static extern IntPtr LoadLibraryEx(string f, IntPtr h, uint fl);
  [DllImport("kernel32.dll")] static extern bool FreeLibrary(IntPtr h);
  [DllImport("kernel32.dll", SetLastError=true)] static extern bool EnumResourceNames(IntPtr h, IntPtr type, EnumNameProc p, IntPtr l);
  [DllImport("kernel32.dll", SetLastError=true)] static extern bool EnumResourceLanguages(IntPtr h, IntPtr type, IntPtr name, EnumLangProc p, IntPtr l);
  [DllImport("kernel32.dll", SetLastError=true)] static extern IntPtr BeginUpdateResource(string f, bool del);
  [DllImport("kernel32.dll", SetLastError=true)] static extern bool UpdateResource(IntPtr h, IntPtr type, IntPtr name, ushort lang, byte[] data, uint cb);
  [DllImport("kernel32.dll", SetLastError=true)] static extern bool EndUpdateResource(IntPtr h, bool discard);

  public static List<string> Replace(string exe, string icoPath, long only) {
    var log = new List<string>();
    var groups = new List<KeyValuePair<long, ushort>>();
    IntPtr lib = LoadLibraryEx(exe, IntPtr.Zero, 2); // LOAD_LIBRARY_AS_DATAFILE
    if (lib == IntPtr.Zero) { log.Add("LoadLibraryEx failed " + Marshal.GetLastWin32Error()); return log; }
    var names = new List<long>();
    EnumResourceNames(lib, (IntPtr)14, (h, t, n, l) => { names.Add((long)n); return true; }, IntPtr.Zero);
    foreach (var n in names) {
      if (n >= 65536) { log.Add("skip string-named group " + n); continue; }
      if (only != 0 && n != only) continue;
      EnumResourceLanguages(lib, (IntPtr)14, (IntPtr)n, (h, t, nm, lang, l) => { groups.Add(new KeyValuePair<long, ushort>(n, lang)); return true; }, IntPtr.Zero);
    }
    FreeLibrary(lib);
    log.Add("icon groups: " + groups.Count);
    if (groups.Count == 0) return log;

    byte[] ico = File.ReadAllBytes(icoPath);
    int cnt = BitConverter.ToUInt16(ico, 4);
    var imgs = new List<byte[]>(); var dirs = new List<byte[]>();
    for (int i = 0; i < cnt; i++) {
      int e = 6 + 16 * i;
      int size = BitConverter.ToInt32(ico, e + 8), off = BitConverter.ToInt32(ico, e + 12);
      var img = new byte[size]; Array.Copy(ico, off, img, 0, size); imgs.Add(img);
      var d = new byte[12]; Array.Copy(ico, e, d, 0, 8);          // width,height,colors,reserved,planes,bitcount
      Array.Copy(BitConverter.GetBytes(size), 0, d, 8, 4); dirs.Add(d);
    }
    IntPtr up = BeginUpdateResource(exe, false);
    if (up == IntPtr.Zero) { log.Add("BeginUpdateResource failed " + Marshal.GetLastWin32Error()); return log; }
    int gi = 0;
    foreach (var g in groups) {
      var grp = new List<byte>();
      grp.AddRange(BitConverter.GetBytes((ushort)0)); grp.AddRange(BitConverter.GetBytes((ushort)1)); grp.AddRange(BitConverter.GetBytes((ushort)cnt));
      for (int i = 0; i < cnt; i++) {
        ushort id = (ushort)(3000 + gi * 100 + i);
        if (!UpdateResource(up, (IntPtr)3, (IntPtr)id, g.Value, imgs[i], (uint)imgs[i].Length)) log.Add("RT_ICON fail " + Marshal.GetLastWin32Error());
        grp.AddRange(dirs[i]); grp.AddRange(BitConverter.GetBytes(id));
      }
      var gb = grp.ToArray();
      if (!UpdateResource(up, (IntPtr)14, (IntPtr)g.Key, g.Value, gb, (uint)gb.Length)) log.Add("RT_GROUP_ICON fail " + Marshal.GetLastWin32Error());
      log.Add("group " + g.Key + " lang " + g.Value + " replaced with " + cnt + " images");
      gi++;
    }
    log.Add(EndUpdateResource(up, false) ? "saved" : "EndUpdateResource failed " + Marshal.GetLastWin32Error());
    return log;
  }
}
'@
foreach($e in $Exe){ "== $e"; [PeIcon]::Replace($e,$Ico,$OnlyGroup) | ForEach-Object { "  $_" } }
