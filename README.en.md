<div align="center"> <img src="SubFontManager/icon/icon@256.png">

# Sub Font Manager

[![license](https://img.shields.io/github/license/anncwb/vue-vben-admin.svg)](LICENSE)

**English** | [中文](./README.md)
</div>

## What is this?

Sub Font Manager is a tool for editing font settings in .ASS or .SSA subtitle files.
It allows you to integrate fonts and subtitles with virtually no cost.

Specifically, Sub Font Manager collects all fonts used in the subtitles and allows
you to subset those fonts based on the characters occurred in the subtitles,
then embed them directly into the subtitle file.


## Why do you need this?

> SubStation Alpha (.SSA) and Advanced SubStation Alpha (.ASS) are among the most
> popular subtitle formats for video effects, offering rich styling and animation
> capabilities that greatly enhance the visual expressiveness of subtitles.

SSA/ASS subtitles often require multiple fonts to render properly.
These fonts need to be pre-installed in the operating system in order for the
player to read and display them correctly. For most users, this process is
too complicated.

**Isn't there a simpler solution for stylized subtitle fonts?**

### In fact, subtitles and fonts can be combined into a single file.

Not only is it possible — it's actually a supported approach by both subtitle formats
and media players.

The SSA/ASS format natively supports embedded files, with its most common use being
font embedding. However, it uses UUEncoding to encode binary files into text form.
For non-Western languages, font files are typically large to begin with,
so embedding them as text is not only inefficient but also significantly
increases the size of the subtitle file.

### Fortunately, **Font Subsetting** technology solves this problem.

> Font subsetting means extracting only the subset of characters needed from a font,
> removing the rest to reduce file size.

In many subtitle files, special-effect fonts are used for very few characters,
while the majority of the font’s character set goes unused. This leads to wasted space.
Font subsetting removes unused characters, dramatically reducing file size.

### But, there are still problems.

Font subsetting isn't a simple task. Tools are limited, most GUI-based ones are
difficult to use, and while command-line tools like fonttools exist, they come with
a steep learning curve. You need to not only learn the command syntax, but also manually
collect the characters to include.

If you're not familiar with the tools, font subsetting may also remove the name table,
which can cause font references to fail.

> The name table stores font names used across various languages and systems.
> For example, the Chinese name “微软雅黑” corresponds to the English “Microsoft Yahei.”
> Both names can reference the same font — but if either one is removed, the font
> can no longer be recognized under that name.

Additionally, a subsetted font file contains only a limited set of characters.
If new characters are added to the subtitles later, the subsetted font won't be able
to display them.
This creates obstacles for further subtitle editing.

These complications have effectively discouraged most users from ever attempting
font subsetting and embedding.

### That’s why I built this tool.

**Sub Font Manager** automates this complex process and significantly simplifies
font embedding by:

- Aggregating all fonts used in the subtitles (including both style and inline overrides)
- Automatically matching font source files from the same folder or system
- Collecting the exact set of characters used in the subtitles
- Subsetting the fonts and retaining the original reference names in the name table
- Encoding the fonts as text and embedding them into the subtitle file

With Sub Font Manager, you can embed and subset fonts with just a few clicks, no technical
expertise required.

Because the workflow is so streamlined, you can even modify your subtitles after
embedding fonts and easily re-embed everything with a single click.

For subtitle creators, this means drastically simplifying your distribution package.
You can share a subtitle file that's nearly the same size as the original,
while still offering full visual fidelity on the user's end.

For general viewers, you no longer have to install entire font libraries just to watch
subtitles with fancy effects. The subtitle file carries only the characters it needs,
and will display correctly—even on set-top boxes and media players.

**Sub Font Manager** lets fonts and subtitles be bundled seamlessly, ensuring the
designer’s intended effects are perfectly reproduced on the viewer’s end.

## How to use

Using Sub Font Manager is very straightforward. The steps to embed fonts are as follows:

1. Open the subtitle file from the "Input File" box, or drag the subtitle file into the window.
You will see the fonts used in the subtitles along with the number of characters covered by each font.
2. Check the fonts you want to embed (it’s recommended to also check "Subsetting").
3. Click "Apply".

<img src="https://github.com/user-attachments/assets/70a710e6-c4a6-42fb-bd49-3ca9f697c044" />
<br /><br />

4. Done! The subtitles will be reloaded automatically, and you’ll see that the selected fonts
are now embedded fonts.

<img src="https://github.com/user-attachments/assets/02967ed4-728a-41fd-9d7d-9cb3aab19f08" />

## Notes on Usage

### Efficiency

Font embedding is inherently inefficient and increases the overall data size
(typically increases by about 33%). When large font files are embedded,
the subtitle file size can increase significantly, which may impact playback and
editing performance.

Therefore, embedding is best suited for fonts used to display a small number of
characters, particularly for titles or logo effects. It is not recommended to embed fonts
used for large amounts of dialogue.

Unless your font file is already very small (e.g., certain English fonts),
it is highly recommended to always use the subsetting feature.

### Compatibility

Most mainstream video players that support ASS/SSA effects also support embedded fonts well.
Tested players include:

- PotPlayer
- VLC
- IINA (MPV)
- Kodi
- Infuse

There are also exceptions, like Movist (as of v2.11.5).

Some subtitle editors have poor support for attachments and may ignore or remove
embedded files upon saving.

However, [Aegisub](https://aegisub.org/) has long provided reliable support for
subtitle attachments and is highly recommended.

## System Support

- **Windows**
- **macOS**

## Language Support

- **English**
- **Simplified Chinese**

Additional languages can be supported through user-contributed translations.

## Development Information

### Language

- **Python**
- **C++** (Windows DLL)

### Python Dependencies

```
pip3 install fonttools, tkinterdnd2, charset-normalizer, cython, pyinstaller
```

Thanks to [fonttools](https://github.com/fonttools/fonttools).

### C++ Dependencies (Only on Windows)

- **Microsoft Visual Studio**

### Run

The project consists of a main Python component named sfm and a Windows C++ subproject named
fontmatch_dll. The fontmatch_dll component is responsible for generating the fontmatch.dll file,
which is used for font matching on Windows system.
On macOS, this DLL is not needed, as the built-in system APIs are sufficient for font matching.

1. Install Python and required [dependencies](#Python-Dependencies).
On Windows, Visual Studio is also required.

2. Before the first run, compile the necessary components.
On Windows, you must compile the DLL project first:
```
powershell -ExecutionPolicy Bypass -File .\fontmatch_dll\build.ps1
```

3. Compile the Cython code.
Navigate to the project root directory and, in your prepared Python environment, run:
```
python ./SubFontManager/sub/uu_cy/setup.py
```

4. Run:
```
python ./SubFontManager/main.py
```

### Build

The project supports both macOS and Windows systems.
The unified build script build_all.py will automatically compile the necessary components
depending on the operating system.

1. Install Python and required [dependencies](#Python-Dependencies).
On Windows, Visual Studio is also required.

2. In your prepared Python environment, run the script from the root directory of the project:
```
python ./build_all.py
```

Enjoy!

## Contact

Email: jensen-yg@163.com
