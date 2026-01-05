# Noto Sans fonts for PDF Unicode support

This folder is intentionally empty. To enable Unicode font support for PDF exports, place the Noto Sans TTF files here:

- `NotoSans-Regular.ttf` (regular) — required
- `NotoSans-Bold.ttf` (optional)
- `NotoSans-Italic.ttf` (optional)

You can download the fonts from Google Fonts (Noto Sans): [https://fonts.google.com/specimen/Noto+Sans](https://fonts.google.com/specimen/Noto+Sans)

Once the regular font file is present the application will automatically register the Noto family and use it for PDF generation, enabling support for wide ranges of Unicode characters. Tests that require Unicode fonts will be skipped automatically when the font is not present.
