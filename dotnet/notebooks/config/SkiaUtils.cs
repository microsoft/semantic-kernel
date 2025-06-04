// Copyright (c) Microsoft. All rights reserved.

using SkiaSharp;
using System.Net.Http;

// ReSharper disable InconsistentNaming
public static class SkiaUtils
{
    // Function used to display images in the notebook
    public static async Task ShowImage(string url, int width, int height)
    {
        SKImageInfo info = new SKImageInfo(width, height);
        SKSurface surface = SKSurface.Create(info);
        SKCanvas canvas = surface.Canvas;
        canvas.Clear(SKColors.White);
        var httpClient = new HttpClient();
        using (Stream stream = await httpClient.GetStreamAsync(url))
        using (MemoryStream memStream = new MemoryStream())
        {
            await stream.CopyToAsync(memStream);
            memStream.Seek(0, SeekOrigin.Begin);
            SKBitmap webBitmap = SKBitmap.Decode(memStream);
            canvas.DrawBitmap(webBitmap, 0, 0, null);
            surface.Draw(canvas, 0, 0, null);
        };
        surface.Snapshot().Display();
    }
}
