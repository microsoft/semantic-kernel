// Copyright (c) Microsoft. All rights reserved.

namespace HuggingFaceImageTextDemo;

partial class FormMain
{
    /// <summary>
    ///  Required designer variable.
    /// </summary>
    private System.ComponentModel.IContainer components = null;

    /// <summary>
    ///  Clean up any resources being used.
    /// </summary>
    /// <param name="disposing">true if managed resources should be disposed; otherwise, false.</param>
    protected override void Dispose(bool disposing)
    {
        if (disposing && (components is not null))
        {
            components.Dispose();
        }
        base.Dispose(disposing);
    }

    #region Windows Form Designer generated code

    /// <summary>
    ///  Required method for Designer support - do not modify
    ///  the contents of this method with the code editor.
    /// </summary>
    private void InitializeComponent()
    {
        this.flowLayoutPanel1 = new FlowLayoutPanel();
        this.textBox1 = new TextBox();
        this.lblImageDescription = new Label();
        this.folderBrowserDialog1 = new FolderBrowserDialog();
        this.lblImagesFolder = new Label();
        this.btRefresh = new Button();
        this.button1 = new Button();
        this.SuspendLayout();
        // 
        // flowLayoutPanel1
        // 
        this.flowLayoutPanel1.Anchor = AnchorStyles.Top | AnchorStyles.Bottom | AnchorStyles.Left | AnchorStyles.Right;
        this.flowLayoutPanel1.Location = new Point(12, 52);
        this.flowLayoutPanel1.Name = "flowLayoutPanel1";
        this.flowLayoutPanel1.Size = new Size(743, 514);
        this.flowLayoutPanel1.TabIndex = 0;
        // 
        // textBox1
        // 
        this.textBox1.Anchor = AnchorStyles.Top | AnchorStyles.Bottom | AnchorStyles.Right;
        this.textBox1.Font = new Font("Segoe UI", 14.25F, FontStyle.Regular, GraphicsUnit.Point, 0);
        this.textBox1.ForeColor = Color.DarkGreen;
        this.textBox1.Location = new Point(761, 145);
        this.textBox1.Multiline = true;
        this.textBox1.Name = "textBox1";
        this.textBox1.Size = new Size(306, 421);
        this.textBox1.TabIndex = 4;
        this.textBox1.Text = "Click in any of the images to generate an AI description";
        // 
        // lblImageDescription
        // 
        this.lblImageDescription.Anchor = AnchorStyles.Top | AnchorStyles.Right;
        this.lblImageDescription.AutoSize = true;
        this.lblImageDescription.Font = new Font("Segoe UI", 15.75F, FontStyle.Regular, GraphicsUnit.Point, 0);
        this.lblImageDescription.Location = new Point(756, 112);
        this.lblImageDescription.Name = "lblImageDescription";
        this.lblImageDescription.Size = new Size(220, 30);
        this.lblImageDescription.TabIndex = 5;
        this.lblImageDescription.Text = "Generated Description";
        this.lblImageDescription.TextAlign = ContentAlignment.MiddleCenter;
        // 
        // folderBrowserDialog1
        // 
        this.folderBrowserDialog1.Description = "Select a folder with images";
        this.folderBrowserDialog1.ShowNewFolderButton = false;
        this.folderBrowserDialog1.UseDescriptionForTitle = true;
        // 
        // lblImagesFolder
        // 
        this.lblImagesFolder.AutoSize = true;
        this.lblImagesFolder.Font = new Font("Segoe UI", 15.75F, FontStyle.Regular, GraphicsUnit.Point, 0);
        this.lblImagesFolder.Location = new Point(12, 14);
        this.lblImagesFolder.Name = "lblImagesFolder";
        this.lblImagesFolder.Size = new Size(250, 30);
        this.lblImagesFolder.TabIndex = 1;
        this.lblImagesFolder.Text = "Images folder: -- Select --";
        this.lblImagesFolder.TextAlign = ContentAlignment.MiddleCenter;
        // 
        // btRefresh
        // 
        this.btRefresh.Anchor = AnchorStyles.Top | AnchorStyles.Right;
        this.btRefresh.Font = new Font("Segoe UI", 11.25F, FontStyle.Regular, GraphicsUnit.Point, 0);
        this.btRefresh.Location = new Point(934, 12);
        this.btRefresh.Name = "btRefresh";
        this.btRefresh.Size = new Size(133, 27);
        this.btRefresh.TabIndex = 3;
        this.btRefresh.Text = "Refresh Images";
        this.btRefresh.UseVisualStyleBackColor = true;
        this.btRefresh.Click += this.btRefresh_Click;
        // 
        // button1
        // 
        this.button1.Anchor = AnchorStyles.Top | AnchorStyles.Right;
        this.button1.Font = new Font("Segoe UI", 11.25F, FontStyle.Regular, GraphicsUnit.Point, 0);
        this.button1.Location = new Point(795, 12);
        this.button1.Name = "button1";
        this.button1.Size = new Size(133, 27);
        this.button1.TabIndex = 2;
        this.button1.Text = "Change Folder";
        this.button1.UseVisualStyleBackColor = true;
        this.button1.Click += this.btChangeFolder_Click;
        // 
        // FormMain
        // 
        this.AutoScaleDimensions = new SizeF(7F, 15F);
        this.AutoScaleMode = AutoScaleMode.Font;
        this.ClientSize = new Size(1079, 578);
        this.Controls.Add(this.button1);
        this.Controls.Add(this.btRefresh);
        this.Controls.Add(this.lblImagesFolder);
        this.Controls.Add(this.lblImageDescription);
        this.Controls.Add(this.textBox1);
        this.Controls.Add(this.flowLayoutPanel1);
        this.Name = "FormMain";
        this.Text = "ImageToText Sample";
        this.Load += this.FormMain_Load;
        this.ResumeLayout(false);
        this.PerformLayout();
    }

    #endregion

    private FlowLayoutPanel flowLayoutPanel1;
    private TextBox textBox1;
    private Label lblImageDescription;
    private FolderBrowserDialog folderBrowserDialog1;
    private Label lblImagesFolder;
    private Button btRefresh;
    private Button button1;
}
