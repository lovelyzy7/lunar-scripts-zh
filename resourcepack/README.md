# resourcepack/ — resource_dump-android-zh.7z 构建器

`build_resource_pack.py` = 2026-10-28 JP 最终打包所用流程的脚本化（copy → stage → patch list.bin → bump → `7z u` → verify）。

```powershell
$py build_resource_pack.py `
  --original E:\NieRReincarnation\resources\resource_dump_android.7z `
  --out      E:\NieRReincarnation\zh-l10n\work\release-jp\resource_dump-android-zh.7z `
  --text-ja  E:\NieRReincarnation\lunar-tear\server\assets\revisions\0\assetbundle\text\ja `
  --bin-e    E:\NieRReincarnation\zh-l10n\work\mt-run\final2\bin_zh_final2.bin.e `
  --help-ja  <原版 help/ja 树（回滚态）> `
  --patch-tool E:\NieRReincarnation\lunar-base\scripts\assetbundles\patch_listbin.py `
  --seven-zip  <7-Zip 22+ 7z.exe> --revision 829 --work-dir <staging> --apply
```

包内布局（= 服务器资源树，bunker 导入只解 `revisions/0`，`release/` 为配套 bin.e）：
```
revisions/0/assetbundle/text/ja/**          汉化整树
revisions/0/assetbundle/ui/help/ja/**       help（本轮=原版 310 回滚态）
revisions/0/list.bin                        原版基 + text/ja 条目刷新 + revision bump
revisions/0/info.json / resources/**        原样
release/20240404193219.bin.e                汉化主数据
```

**硬性要求**：
* 原版 dump **只读**——先整文件 copy 成工作副本（sha256 核对）再 `7z u`；
* **7-Zip 22+**（32 位 7-Zip 9.x 对 14.9GB solid 包 `u` 会 `Unknown Error`，实测）；
* list.bin 必须与包内文件自洽（entries 的 size/md5 = 实际文件；否则 octo CDN 下载即拒）；
* 交付校验 = `7z l -slt` 条目 CRC32/size ↔ 源文件逐一比对 + sha256 表（见 `work\release-jp\RELEASE-JP.md`）。
