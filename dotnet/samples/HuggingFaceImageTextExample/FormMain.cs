using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.ImageToText;
using System.Drawing.Imaging;

namespace HuggingFaceImageTextDemo;

#pragma warning disable SKEXP0001 // Type is for evaluation purposes only and is subject to change or removal in future updates.
#pragma warning disable SKEXP0020 // Type is for evaluation purposes only and is subject to change or removal in future updates.

/// <summary>
/// Main form of the application.
/// </summary>
public partial class FormMain : Form
{
    private readonly Kernel _kernel;
    private readonly IImageToTextService _imageToTextService;

    /// <summary>
    /// Initializes a new instance of the <see cref="FormMain"/> class.
    /// </summary>
    public FormMain()
    {
        this.InitializeComponent();
        this._kernel = Kernel.CreateBuilder()
                        .AddHuggingFaceImageToText("Salesforce/blip-image-captioning-base")
                        .Build();

        this._imageToTextService = this._kernel.GetRequiredService<IImageToTextService>();
    }

    private void FormMain_Load(object sender, EventArgs e)
    {
        this.ChangeFolder();
    }
    private void ChangeFolder()
    {
        if (this.folderBrowserDialog1.ShowDialog() == DialogResult.OK)
        {
            this.lblImagesFolder.Text = $"Images folder: {this.folderBrowserDialog1.SelectedPath}";
        }

        if (string.IsNullOrEmpty(this.folderBrowserDialog1.SelectedPath))
        {
            MessageBox.Show("A folder needs to be selected.");

            this.ChangeFolder();
        }
        else
        {
            this.RefreshImages();
        }
    }

    private void RefreshImages()
    {
        var imageDirectory = this.folderBrowserDialog1.SelectedPath;

        var extensions = new List<string> { "*.jpg", "*.jpeg", "*.png", "*.gif", "*.bmp", "*.tiff", "*.ico", "*.svg" };
        var myImagePaths = new List<string>();
        foreach (var extension in extensions)
        {
            myImagePaths.AddRange(Directory.GetFiles(imageDirectory, extension, SearchOption.AllDirectories));
        }

        this.flowLayoutPanel1.Controls.Clear();
        foreach (var imagePath in myImagePaths)
        {
            PictureBox pictureBox = new();
            using var fs = new FileStream(imagePath, FileMode.Open, FileAccess.Read);
            pictureBox.Image = new Bitmap(Image.FromStream(fs));
            pictureBox.SizeMode = PictureBoxSizeMode.Zoom;
            pictureBox.Height = 300;
            pictureBox.Width = 300;
            pictureBox.Click += this.PictureBoxOnClickAsync;
            pictureBox.Tag = imagePath;
            this.flowLayoutPanel1.Controls.Add(pictureBox);
        }
    }

#pragma warning disable VSTHRD100 // Avoid async void methods
    private async void PictureBoxOnClickAsync(object? sender, EventArgs e)
    {
        this.textBox1.Text = "Processing...";
        var pictureBox = ((PictureBox)sender!);
        ImageContent imageContent = CreateImageContentFromPictureBox(pictureBox);
        string text;
        try
        {
            text = (await this._imageToTextService.GetTextContentAsync(imageContent).ConfigureAwait(false)).Text!;
        }
        catch (Exception ex)
        {
            text = ex.Message;
        }

        this.UpdateImageDescription(text);
    }
#pragma warning restore VSTHRD100 // Avoid async void methods

    private void UpdateImageDescription(string description)
    {
        // Ensure the following UI update is executed on the UI thread
        if (this.textBox1.InvokeRequired)
        {
            this.textBox1.Invoke(() =>
            {
                this.textBox1.Text = description;
            });
        }
        else
        {
            this.textBox1.Text = description;
        }
    }

    private static ImageContent CreateImageContentFromPictureBox(PictureBox pictureBox)
        => new(ConvertImageToReadOnlyMemory(pictureBox.Image))
        {
            MimeType = GetMimeType(pictureBox.Tag?.ToString()!)
        };

    private static ReadOnlyMemory<byte> ConvertImageToReadOnlyMemory(Image image)
    {
        using var memoryStream = new MemoryStream();
        // Save the image to the MemoryStream, using PNG format for example
        image.Save(memoryStream, ImageFormat.Jpeg);

        // Optionally, reset the position of the MemoryStream to the beginning
        memoryStream.Position = 0;

        // Convert the MemoryStream's buffer to ReadOnlyMemory<byte>
        // Note: ToArray creates a copy of the buffer; if you're concerned about performance or memory usage,
        // you might look into more efficient methods depending on your use case.
        return new ReadOnlyMemory<byte>(memoryStream.ToArray());
    }

    private void btRefresh_Click(object sender, EventArgs e)
    {
        this.RefreshImages();
    }

    private static string GetMimeType(string fileName)
    {
        return Path.GetExtension(fileName) switch
        {
            ".jpg" or ".jpeg" => "image/jpeg",
            ".png" => "image/png",
            ".gif" => "image/gif",
            ".bmp" => "image/bmp",
            ".tiff" => "image/tiff",
            ".ico" => "image/x-icon",
            ".svg" => "image/svg+xml",
            _ => "application/octet-stream"
        };
    }

    private void btChangeFolder_Click(object sender, EventArgs e)
    {
        this.ChangeFolder();
    }
}
