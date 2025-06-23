<div align="center"> <img src="SubFontManager/icon/icon@256.png">

# Sub Font Manager

[![license](https://img.shields.io/github/license/anncwb/vue-vben-admin.svg)](LICENSE)

[English](./README.en.md) | **简体中文**
</div>

## 这是什么

Sub Font Manager 用于编辑.ASS或.SSA字幕文件中的字体设置，它可以让你几乎无代价地将字体和字幕整合到一起。

具体来说，Sub Font Manager 可以将字幕中所有使用过的字体汇总，
并将字体按照字幕所覆盖的字符集进行子集化并嵌入到字幕文件中。

## 为什么需要它

> SubStation Alpha (.SSA) 和 Advanced SubStation Alpha (.ASS) 是当下最流行的视频特效字幕格式，
> 可以实现丰富的样式和动画效果，极大的丰富了视频字幕的表现能力。

SSA/ASS 字幕的效果往往需要多种字体的支持，这些字体需要预先安装在操作系统内，播放器才可以读取和渲染，
这对于大部分用户来说过于繁琐，简直是为了盘醋还得包顿饺子。

**难道没有更简单的特效字体解决方案了吗？**

### 其实，字幕和字体可以合并为一个文件

不但可以，而且是被字幕和播放器都支持的做法。
SSA/ASS 格式原生就支持内嵌文件，其最主要的用途就是内嵌字体文件，
不过，SSA/ASS 规定二进制文件需使用 UUEncoding 编码为文本后嵌入，对于非西方语系的语言来说，字体文件本来就大，
文本化嵌入不但低效而且会大大增加字幕文件的体积。

### 好在，还有**字体子集化**技术可以解决这个问题

> 子集化，就是将字体所覆盖的字符集取子集，删去其他字符，从而减小字体文件的体积。

在字幕文件中，许多特效字体仅仅只使用了几个字，其覆盖的字库绝大部分都是无用的，存在巨大的空间浪费，
通过子集化方法可以将字库中无用的字符删除，从而大大减小字体文件的体积。

### 但是，还有问题

子集化操作并不简单，现成的工具不多，GUI 工具都很难用，命令行工具倒是有，例如 fonttools ，但门槛高，
除了要掌握命令规则外，子集字符还得自己收集。
如果你不是很会使用的话，子集化的同时还会删除字体名表，导致字体引用失败。

> 名表，是字体各种引用名字在各种语言下的名称，例如“微软雅黑”的英文名字叫“Microsoft Yahei”，
> 这两个名字都可以引用到它，但如果任何一个名字被删掉了，就没法引用到了。

此外，子集化后的字体文件只包含了少数字符，如果字幕中又增加了新字符，
子集化的字体是无法显示的，所以它会给字幕的后期编辑带来障碍。

这一系列问题实在是太麻烦了，直接导致子集化和字体内嵌技术几乎无人使用。

### 所以我开发了这个工具

**Sub Font Manager** 可以大大简化字体内嵌的流程，它将以上繁琐的过程全部自动化：

- 汇总出字幕中所有使用过的字体（包括 Style 中的设置和行内覆盖的设置）；
- 在同目录和系统中自动匹配字体源文件；
- 收集字体在字幕中覆盖的字符集；
- 将字体子集化并在名表中保留字幕中的引用名字；
- 将字体编码为文本并写入到字幕文件中。

在 Sub Font Manager 中，你只需通过简单的勾选就可以一键实现字体的子集化和嵌入操作，大大简化内嵌字体的流程。

因为流程的简化，你甚至可以在字体内嵌后放心的再次修改字幕，因为重新内嵌只需一键即可完成。

对于字幕制作者，你可以大大简化发布的文件包，用几乎一样大小的字幕文件在用户端无障碍重现字幕特效。

对于普通观影者，你无需再为了字幕中的几个特效文字而安装一系列字库，字幕会自带字体，而且只带它需要的那几个字，
这种字幕甚至在机顶盒和播放机中也可以重现特效。

所以，**Sub Font Manager 可以让字体和字幕无负担的绑定在一起，让字幕制作者精心设计的特效在用户端完美重现。**

## 如何使用

Sub Font Manager 的使用非常简单，嵌入字体的步骤如下：

1. 从“输入文件”框中打开字幕文件，或者将字幕文件拖入窗口中，可以看到字幕中使用的字体和分别覆盖的字符数；
2. 勾选希望内嵌的字体（推荐同时勾选“子集化”）；
3. 点击应用；

<img src="https://github.com/user-attachments/assets/70a710e6-c4a6-42fb-bd49-3ca9f697c044" />
<br /><br />

4. 完成！字幕自动重载入，可以看到勾选的字体已经变成内嵌字体。

<img src="https://github.com/user-attachments/assets/02967ed4-728a-41fd-9d7d-9cb3aab19f08" />

## 使用须知

### 效率

字体内嵌毕竟是一种低效且会增大总数据量的方案（大约增加33%），当嵌入的文件过大时，字幕文件会显著增大，
过大的字幕文件对播放和编辑性能都有影响。所以它只适合对覆盖少量字符的字体进行内嵌，尤其适合于片名等特效字体，
不建议将覆盖大量对白的字体内嵌。除非字体源文件特别小（如一些英文字体），否则建议始终使用“子集化”功能。

### 兼容性

主流视频播放器中，只要能支持 ASS/SSA 特效字幕的，大多对内嵌字体兼容良好，其中包括但不限于：

- PotPlayer
- VLC
- IINA (MPV)
- Kodi
- Infuse

不过也有例外，如 Movist（截至 v2.11.5）。

部分字幕编辑器对字幕附件兼容不好，它们可能会忽略附件并在保存时删掉它们。
不过，[Aegisub](https://aegisub.org/) 一直对附件支持良好，推荐使用。


## 系统支持

- **Windows**
- **macOS**


## 语言支持

- **English**
- **简体中文**

可由用户翻译来支持更多语言


## 开发信息

### 语言：

- **Python**
- **C++** (Windows DLL)

### Python 依赖

```
pip3 install fonttools, tkinterdnd2, charset-normalizer, cython, pyinstaller
```

感谢 [**fonttools**](https://github.com/fonttools/fonttools) 库。

### C++ 依赖（仅Windows需要）

- **Microsoft Visual Studio**

### 运行

项目由一个 Python 主项目 SubFontManager 和一个 Windows C++ 子项目 fontmatch_dll 组成，
其中 fontmatch_dll 负责提供一个 fontmatch.dll 文件，用于在 Windows 系统中匹配字体。
Mac 下不需要该 DLL 项目，macOS 自带的接口就可以实现字体匹配。

1. 安装 Python 以及相关[依赖库](#Python-依赖)，Windows 系统还需安装 Visual Studio。

2. 初次运行需要先编译组件，Windows 需要先编译 DLL 项目：
```
powershell -ExecutionPolicy Bypass -File .\fontmatch_dll\build.ps1
```

3. 编译 Cython 代码。进入项目根目录，在准备好的 Python 环境中执行：
```
python ./SubFontManager/sub/uu_cy/setup.py
```

4. 运行：
```
python ./SubFontManager/main.py
```

### 构建

项目支持 macOS 和 Windows 系统，统一构建脚本 build_all.py 会根据系统自动编译需要的部分。

1. 安装 Python 以及相关[依赖库](#Python-依赖)，Windows 系统还需安装 Visual Studio。

2. 在准备好的 Python 环境中执行项目根目录下的脚本文件：
```
python ./build_all.py
```

Enjoy!

## 联系我

Email: jensen-yg@163.com
