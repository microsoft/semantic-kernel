# Tesseract OCR Support

This API supports the ability to upload image file formats such as png, jpg and tiff via the [Tesseract](https://www.nuget.org/packages/Tesseract) nuget package.  
You will need to obtain one or more [tessdata language data files](https://github.com/tesseract-ocr/tessdata) such as `eng.traineddata` and add them to your `./data` directory or the location specified in the `Tesseract.FilePath` location in `./appsettings.json`.

If you do not add any `.traineddata` files, you will receive a runtime exception when attempting to upload one of these image formats.