# Downloads Janitor

A free Mac tool that sorts your messy Downloads folder into organized subfolders. One click.

## What it does

When you run Downloads Janitor, it looks at every file in your Downloads folder and moves it into a tidy subfolder based on what kind of file it is. It sorts your files into 13 categories, like Photos, Videos, PDFs, Music, and more. Every move is recorded, so if you don't like the result you can undo the whole thing with a single click. Nothing is ever deleted or overwritten.

![Demo](demo.gif)

## Quick start

1. Download this project. Click the green **Code** button near the top of this page, then choose **Download ZIP**.
2. Unzip the folder (double-click the downloaded file).
3. Double-click **INSTALL.command** inside the folder.
4. Follow the on-screen instructions.
5. Double-click **~/Downloads-Janitor-Sort.command** whenever your Downloads folder needs cleaning.

That's it. You never have to touch Terminal or type any commands.

## The 13 categories

| Category | File types |
|---|---|
| Photos | .jpg, .jpeg, .png, .gif, .heic, .webp, .bmp, .tiff, .svg, .raw, .dng, .cr2 |
| Videos | .mp4, .mov, .avi, .mkv, .webm, .flv, .wmv, .m4v |
| PDFs | .pdf |
| Documents | .docx, .doc, .pages, .txt, .rtf, .odt, .md, .gp |
| Spreadsheets | .xlsx, .xls, .xlsm, .csv, .ods, .numbers |
| Presentations | .pptx, .ppt, .key, .odp |
| Applications | .exe, .msi, .dmg, .pkg, .deb, .rpm, .appimage, .iso, .img |
| Zips | .zip, .rar, .7z, .tar, .gz, .tgz, .bz2 |
| Music | .mp3, .wav, .flac, .m4a, .aac, .ogg, .wma, .midi, .mid |
| Design Files | .psd, .ai, .sketch, .fig, .xd, .indd |
| Fonts | .ttf, .otf, .woff, .woff2 |
| Code | .py, .js, .ts, .html, .css, .json, .xml, .yaml, .yml, .toml, .sh, .sql, .jsx, .tsx |
| Ebooks | .epub, .mobi, .azw3 |

## Customization

You can change what goes where by editing the **config.json** file in the project folder. Open it with any text editor. You can add new file types to a category, remove ones you don't want, or create a whole new category of your own.

For example, to add .webp to Photos, open config.json and add ".webp" to the Photos list.

## Undo

Made a mess or changed your mind? Double-click **~/Downloads-Janitor-Undo.command** and it will put everything back where it was. Undo reverses only the most recent sort, and it never overwrites a file that's already in the way, so it's always safe to try.

## Requirements

- macOS (any recent version)
- Python 3. Most Macs already have it. If not, you can download it for free from [python.org](https://www.python.org/downloads/).

## Privacy

Downloads Janitor runs entirely on your Mac. No data is collected, no files are uploaded, no internet connection is needed. Your files stay yours.

## Support the project

If this tool saved you time, consider supporting the project:

[UPI QR code here]

[Buy Me a Coffee link here]

## License

MIT License — free to use, modify, and share.

## Credits

Built by Daksh (https://instagram.com/whydakshh)
