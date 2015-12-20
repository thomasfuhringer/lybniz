# -*- coding: UTF-8 -*-
# Lybniz on IronPython, Thomas Führinger, 2006-10-29
# released under the terms of the revised BSD license

# To run, type:
# "C:\Program Files\IronPython\ipy.exe" lybniz.py


import math
import clr
clr.AddReferenceByPartialName("System.Windows.Forms")
clr.AddReferenceByPartialName("System.Drawing")
import System.Windows.Forms
import System.Drawing
import System.IO
#import System.Resources
#import System.Reflection
import System.Drawing.Image
import Microsoft.Win32

Icon = System.Drawing.Icon("Resources/Lybniz.ico")

class MainForm(System.Windows.Forms.Form):
    def __init__(self):
        self.Text = "Lybniz"
        self.Name = "mainForm"
        self.Icon = Icon
        self.IsMdiContainer = True
        self.FormClosing += self.SaveSize
        self.Load += self.SetSize
        #resources = System.Resources.ResourceManager("Lybniz", System.Reflection.Assembly.GetExecutingAssembly())
        #print resources.GetObject("executeToolStripButton.Image")
        self.childWindows = 0

        self.menuStrip = System.Windows.Forms.MenuStrip()
        self.fileToolStripMenuItem = System.Windows.Forms.ToolStripMenuItem()
        self.graphToolStripMenuItem = System.Windows.Forms.ToolStripMenuItem()
        self.windowToolStripMenuItem = System.Windows.Forms.ToolStripMenuItem()
        self.helpToolStripMenuItem = System.Windows.Forms.ToolStripMenuItem()
        self.newToolStripMenuItem = System.Windows.Forms.ToolStripMenuItem()
        self.closeToolStripMenuItem = System.Windows.Forms.ToolStripMenuItem()
        self.exitToolStripMenuItem = System.Windows.Forms.ToolStripMenuItem()
        self.plotToolStripMenuItem = System.Windows.Forms.ToolStripMenuItem()
        self.aboutToolStripMenuItem = System.Windows.Forms.ToolStripMenuItem()
        self.toolStrip = System.Windows.Forms.ToolStrip()
        self.executeToolStripButton = System.Windows.Forms.ToolStripButton()
        self.statusStrip = System.Windows.Forms.StatusStrip()
        self.toolStripStatusLabel = System.Windows.Forms.ToolStripStatusLabel()
        self.menuStrip.SuspendLayout()
        self.toolStrip.SuspendLayout()
        self.SuspendLayout()
        
        # mainMenu
        self.menuStrip.Name = "menuStrip"
        self.menuStrip.Items.AddRange((
            self.fileToolStripMenuItem, 
            self.graphToolStripMenuItem, 
            self.windowToolStripMenuItem, 
            self.helpToolStripMenuItem))
        
        # fileToolStripMenuItem
        self.fileToolStripMenuItem.Text = "&File"
        self.fileToolStripMenuItem.DropDownItems.AddRange((
            self.newToolStripMenuItem, 
            self.closeToolStripMenuItem, 
            System.Windows.Forms.ToolStripSeparator(),
            self.exitToolStripMenuItem))
        
        # newToolStripMenuItem
        self.newToolStripMenuItem.Text = "&New"
        self.newToolStripMenuItem.Click += self.DocNew
        self.newToolStripMenuItem.ShortcutKeys = System.Windows.Forms.Keys.Control | System.Windows.Forms.Keys.N
        
        # closeToolStripMenuItem
        self.closeToolStripMenuItem.Text = "&Close"
        self.closeToolStripMenuItem.Click += self.DocClose
        
        # exitToolStripMenuItem
        self.exitToolStripMenuItem.Text = "E&xit"
        self.exitToolStripMenuItem.Click += self.AppExit
        
        # graphToolStripMenuItem
        self.graphToolStripMenuItem.Text = "&Graph"
        self.graphToolStripMenuItem.DropDownItems.Add(self.plotToolStripMenuItem)
        
        # plotToolStripMenuItem
        self.plotToolStripMenuItem.Text = "P&lot"
        self.plotToolStripMenuItem.ShortcutKeys = System.Windows.Forms.Keys.Control | System.Windows.Forms.Keys.G
        self.plotToolStripMenuItem.Click += self.Plot
        
        # windowToolStripMenuItem
        self.windowToolStripMenuItem.Text = "&Window"
        self.menuStrip.MdiWindowListItem = self.windowToolStripMenuItem
        #self.graphToolStripMenuItem.DropDownItems.AddRange((self.closeMenuItem, self.exitMenuItem))
        
        # closeToolStripMenuItem
        self.closeToolStripMenuItem.Text = "&Close"
        self.closeToolStripMenuItem.Click += self.DocClose
        
        # helpToolStripMenuItem
        self.helpToolStripMenuItem.Name = "helpMenuItem"
        self.helpToolStripMenuItem.Text = "&Help"
        self.helpToolStripMenuItem.DropDownItems.Add(self.aboutToolStripMenuItem)
        
        # aboutToolStripMenuItem
        self.aboutToolStripMenuItem.Text = "&About"
        self.aboutToolStripMenuItem.Click += self.About
        
        # toolStrip
        self.toolStrip.Items.Add(self.executeToolStripButton)
        
        # statusStrip
        self.statusStrip.Items.Add(self.toolStripStatusLabel)
        #self.toolStripStatusLabel.Text = "Status"

        # executeToolStripButton
        self.executeToolStripButton.Name = "executeToolStripButtonName"
        self.executeToolStripButton.DisplayStyle = System.Windows.Forms.ToolStripItemDisplayStyle.Image
        #self.executeToolStripButton.Image = resources.GetObject("executeToolStripButton.Image")
        self.executeToolStripButton.Image = System.Drawing.Image.FromFile("Resources/Run.ico")
        self.executeToolStripButton.ImageTransparentColor = System.Drawing.Color.Magenta
        self.executeToolStripButton.Click += self.Plot
        
        self.Controls.Add(self.statusStrip)
        self.Controls.Add(self.toolStrip)
        self.Controls.Add(self.menuStrip)
        #self.MainMenuStrip = self.menuStrip
        self.menuStrip.ResumeLayout(False)
        self.menuStrip.PerformLayout()
        self.toolStrip.ResumeLayout(False)
        self.toolStrip.PerformLayout()
        self.ResumeLayout(False)
        self.PerformLayout()
        
        self.DocNew(None, None)
        
    def SaveSize(self, f, a):
        key = Microsoft.Win32.Registry.CurrentUser.CreateSubKey("Software\Lybniz\Main")
        key.SetValue("Height", self.Height)
        key.SetValue("Width", self.Width)
        key.SetValue("Left", self.Left)
        key.SetValue("Top", self.Top)

    def SetSize(self, f, a):
        key = Microsoft.Win32.Registry.CurrentUser.OpenSubKey("Software\Lybniz\Main")
        if key is not None:
            self.Height = key.GetValue("Height")
            self.Width = key.GetValue("Width")
            self.Left = key.GetValue("Left")
            self.Top = key.GetValue("Top")

    def Plot(self, f, a):
        if self.ActiveMdiChild is not None:
            self.ActiveMdiChild.Plot()

    def DocNew(self, source, a):
        self.childWindows += 1
        childForm = GraphForm(self, self.childWindows)
        childForm.Show()

    def DocClose(self, source, a):
        if self.ActiveMdiChild is not None:
            self.ActiveMdiChild.Close()

    def AppExit(self, source, a):
        self.Close()

    def About(self, source, a):
        #MessageBox("Lybniz by Thomas Führinger")
        System.Windows.Forms.MessageBox.Show(u"Lybniz on IronPython\nVersion 0.9\n2006 by Thomas Führinger", "About Lybniz", System.Windows.Forms.MessageBoxButtons.OK)


class GraphData(object):
    def __init__(self):

        self.ConnectPoints = True

        self.xMinText = "-5.0"
        self.xMaxText = "5.0"
        self.xScaleText = "1.0"

        self.yMinText = "-5.0"
        self.yMaxText = "5.0"
        self.yScaleText = "1.0"
        
        self.xMin = -5.0
        self.xMax = 5.0
        self.xScale = 1.0

        self.yMin = -5.0
        self.yMax = 5.0
        self.yScale = 1.0

        self.y1 = ""
        self.y2 = ""
        self.y3 = ""


class GraphForm(System.Windows.Forms.Form):
    def __init__(self, Parent, childWindows):
        self.MdiParent = Parent
        self.Text = "Graph" + str(childWindows)
        self.Icon = Icon
        self.Size = System.Drawing.Size(520, 400)

        self.g = GraphData()

        self.SuspendLayout();
        self.y1Label = System.Windows.Forms.Label()
        self.y1Label.ForeColor = System.Drawing.Color.Blue
        self.y1Label.Location = System.Drawing.Point(6, 11)
        self.y1Label.Text = "y1 ="
        self.y1Label.AutoSize = True
        self.y1TextBox = System.Windows.Forms.TextBox()
        self.y1TextBox.Location = System.Drawing.Point(36, 8)
        self.y1TextBox.Anchor = System.Windows.Forms.AnchorStyles.Top | System.Windows.Forms.AnchorStyles.Left | System.Windows.Forms.AnchorStyles.Right
        self.y1TextBox.Width = 200
        self.y1TextBox.DataBindings.Add("Text", self.g, "y1")
        
        self.y2Label = System.Windows.Forms.Label()
        self.y2Label.ForeColor = System.Drawing.Color.Red
        self.y2Label.Location = System.Drawing.Point(6, 37)
        self.y2Label.Text = "y2 ="
        self.y2Label.AutoSize = True
        self.y2TextBox = System.Windows.Forms.TextBox()
        self.y2TextBox.Location = System.Drawing.Point(36, 34)
        self.y2TextBox.Anchor = System.Windows.Forms.AnchorStyles.Top | System.Windows.Forms.AnchorStyles.Left | System.Windows.Forms.AnchorStyles.Right
        self.y2TextBox.Width = 200
        self.y2TextBox.DataBindings.Add("Text", self.g, "y2")
        
        self.y3Label = System.Windows.Forms.Label()
        self.y3Label.ForeColor = System.Drawing.Color.Green
        self.y3Label.Location = System.Drawing.Point(6, 63)
        self.y3Label.Text = "y3 ="
        self.y3Label.AutoSize = True
        self.y3TextBox = System.Windows.Forms.TextBox()
        self.y3TextBox.Location = System.Drawing.Point(36, 60)
        self.y3TextBox.Anchor = System.Windows.Forms.AnchorStyles.Top | System.Windows.Forms.AnchorStyles.Left | System.Windows.Forms.AnchorStyles.Right
        self.y3TextBox.Width = 200
        self.y3TextBox.DataBindings.Add("Text", self.g, "y3")
        
        self.xMinLabel = System.Windows.Forms.Label()
        self.xMinLabel.Location = System.Drawing.Point(266, 11)
        self.xMinLabel.Anchor = System.Windows.Forms.AnchorStyles.Top | System.Windows.Forms.AnchorStyles.Right
        self.xMinLabel.Text = "xMin"
        self.xMinLabel.AutoSize = True
        self.xMinTextBox = System.Windows.Forms.TextBox()
        self.xMinTextBox.Location = System.Drawing.Point(306, 8)
        self.xMinTextBox.Anchor = System.Windows.Forms.AnchorStyles.Top | System.Windows.Forms.AnchorStyles.Right
        self.xMinTextBox.Width = 72
        self.xMinTextBox.DataBindings.Add("Text", self.g, "xMinText")
        
        self.xMaxLabel = System.Windows.Forms.Label()
        self.xMaxLabel.Location = System.Drawing.Point(266, 37)
        self.xMaxLabel.Anchor = System.Windows.Forms.AnchorStyles.Top | System.Windows.Forms.AnchorStyles.Right
        self.xMaxLabel.Text = "xMax"
        self.xMaxLabel.AutoSize = True
        self.xMaxTextBox = System.Windows.Forms.TextBox()
        self.xMaxTextBox.Location = System.Drawing.Point(306, 34)
        self.xMaxTextBox.Anchor = System.Windows.Forms.AnchorStyles.Top | System.Windows.Forms.AnchorStyles.Right
        self.xMaxTextBox.Width = 72
        self.xMaxTextBox.DataBindings.Add("Text", self.g, "xMaxText")
        
        self.xScaleLabel = System.Windows.Forms.Label()
        self.xScaleLabel.Location = System.Drawing.Point(266, 63)
        self.xScaleLabel.Anchor = System.Windows.Forms.AnchorStyles.Top | System.Windows.Forms.AnchorStyles.Right
        self.xScaleLabel.Text = "xScale"
        self.xScaleLabel.AutoSize = True
        self.xScaleTextBox = System.Windows.Forms.TextBox()
        self.xScaleTextBox.Location = System.Drawing.Point(306, 60)
        self.xScaleTextBox.Anchor = System.Windows.Forms.AnchorStyles.Top | System.Windows.Forms.AnchorStyles.Right
        self.xScaleTextBox.Width = 72
        self.xScaleTextBox.DataBindings.Add("Text", self.g, "xScaleText")
        
        self.yMinLabel = System.Windows.Forms.Label()
        self.yMinLabel.Location = System.Drawing.Point(394, 11)
        self.yMinLabel.Anchor = System.Windows.Forms.AnchorStyles.Top | System.Windows.Forms.AnchorStyles.Right
        self.yMinLabel.Text = "yMin"
        self.yMinLabel.AutoSize = True
        self.yMinTextBox = System.Windows.Forms.TextBox()
        self.yMinTextBox.Location = System.Drawing.Point(434, 8)
        self.yMinTextBox.Anchor = System.Windows.Forms.AnchorStyles.Top | System.Windows.Forms.AnchorStyles.Right
        self.yMinTextBox.Width = 72
        self.yMinTextBox.DataBindings.Add("Text", self.g, "yMinText")
        
        self.yMaxLabel = System.Windows.Forms.Label()
        self.yMaxLabel.Location = System.Drawing.Point(394, 37)
        self.yMaxLabel.Anchor = System.Windows.Forms.AnchorStyles.Top | System.Windows.Forms.AnchorStyles.Right
        self.yMaxLabel.Text = "yMax"
        self.yMaxLabel.AutoSize = True
        self.yMaxTextBox = System.Windows.Forms.TextBox()
        self.yMaxTextBox.Location = System.Drawing.Point(434, 34)
        self.yMaxTextBox.Anchor = System.Windows.Forms.AnchorStyles.Top | System.Windows.Forms.AnchorStyles.Right
        self.yMaxTextBox.Width = 72
        self.yMaxTextBox.DataBindings.Add("Text", self.g, "yMaxText")
        
        self.yScaleLabel = System.Windows.Forms.Label()
        self.yScaleLabel.Location = System.Drawing.Point(394, 63)
        self.yScaleLabel.Anchor = System.Windows.Forms.AnchorStyles.Top | System.Windows.Forms.AnchorStyles.Right
        self.yScaleLabel.Text = "yScale"
        self.yScaleLabel.AutoSize = True
        self.yScaleTextBox = System.Windows.Forms.TextBox()
        self.yScaleTextBox.Location = System.Drawing.Point(434, 60)
        self.yScaleTextBox.Anchor = System.Windows.Forms.AnchorStyles.Top | System.Windows.Forms.AnchorStyles.Right
        self.yScaleTextBox.Width = 72   
        self.yScaleTextBox.DataBindings.Add("Text", self.g, "yScaleText")         
        
        self.Controls.Add(self.y1Label)
        self.Controls.Add(self.y1TextBox)
        self.Controls.Add(self.y2Label)
        self.Controls.Add(self.y2TextBox)
        self.Controls.Add(self.y3Label)
        self.Controls.Add(self.y3TextBox)
        self.Controls.Add(self.xMinLabel)
        self.Controls.Add(self.xMinTextBox)
        self.Controls.Add(self.xMaxLabel)
        self.Controls.Add(self.xMaxTextBox)
        self.Controls.Add(self.xScaleLabel)
        self.Controls.Add(self.xScaleTextBox)
        self.Controls.Add(self.yMinLabel)
        self.Controls.Add(self.yMinTextBox)
        self.Controls.Add(self.yMaxLabel)
        self.Controls.Add(self.yMaxTextBox)
        self.Controls.Add(self.yScaleLabel)
        self.Controls.Add(self.yScaleTextBox)
        
        self.graphLabel = System.Windows.Forms.Label()
        self.graphLabel.SetBounds(6, 90, 498, 268)
        self.graphLabel.Anchor = System.Windows.Forms.AnchorStyles.Top | System.Windows.Forms.AnchorStyles.Bottom | System.Windows.Forms.AnchorStyles.Left | System.Windows.Forms.AnchorStyles.Right
        self.graphLabel.BackColor = System.Drawing.SystemColors.Window
        self.graphLabel.BorderStyle = System.Windows.Forms.BorderStyle.Fixed3D
        self.graphLabel.Paint += self.GraphLabel_Paint
        self.Controls.Add(self.graphLabel)
        
        if self.Text == "Graph1":
            self.g.y1 = "x**3 - 2 * x"
            #self.xMinTextBox.Text = "-2 * math.pi"
            #self.xMaxTextBox.Text = "2 * math.pi"
            #self.xScaleTextBox.Text = "math.pi/2"
            #self.yMinTextBox.Text = "-3.0"
            #self.yMaxTextBox.Text = "3.0"
            #self.yScaleTextBox.Text = "1"
        
        self.ResumeLayout(False)
        self.PerformLayout()
                
    def GraphLabel_Paint(self, source, a):    
        # this code needs to be rewritten using matrix transformation
        
        xFactor = self.graphLabel.ClientSize.Width / (self.g.xMax - self.g.xMin)
        yFactor = self.graphLabel.ClientSize.Height / (self.g.yMax - self.g.yMin) * -1

        gx = a.Graphics
        gx.TranslateTransform(self.g.xMin * xFactor * -1, self.g.yMax * yFactor * -1)
        pen = System.Drawing.Pen(System.Drawing.Color.Black, 1)
        
        # draw cross
        gx.DrawLine(pen, System.Drawing.Point(self.g.xMin * xFactor, 0), System.Drawing.Point(self.g.xMax * xFactor, 0))
        gx.DrawLine(pen, System.Drawing.Point(0, self.g.yMin * yFactor), System.Drawing.Point(0, self.g.yMax * yFactor))

        # draw scaling x
        os = -1 * self.g.xMin % self.g.xScale
        for i in xrange((self.g.xMax - self.g.xMin) / self.g.xScale + 1):
            gx.DrawLine(pen, System.Drawing.Point((os + i * self.g.xScale + self.g.xMin) * xFactor, -5), System.Drawing.Point((os + i * self.g.xScale + self.g.xMin) * xFactor, +5))
        # draw scaling y
        os = -1 * self.g.yMin % self.g.yScale
        for i in xrange((self.g.yMax - self.g.yMin) / self.g.yScale + 1):
            gx.DrawLine(pen, System.Drawing.Point(-5, (os + i * self.g.yScale + self.g.yMin) * yFactor), System.Drawing.Point(+5, (os + i * self.g.yScale + self.g.yMin) * yFactor))

        # plot        
        self.PrevY = [None, None, None]
        for i in xrange(self.graphLabel.ClientSize.Width):
            xC = self.g.xMin * xFactor + i
            x = xC / xFactor
            for e in ((self.g.y1, 0, System.Drawing.Color.Blue), (self.g.y2, 1, System.Drawing.Color.Red), (self.g.y3, 2, System.Drawing.Color.Green)):
                try:
                    y = eval(e[0])
                    yC = y * yFactor
                    
                    if y < self.g.yMin or y > self.g.yMax:
                        raise ValueError
                    
                    pen = System.Drawing.Pen(e[2], 1)
                    if self.g.ConnectPoints and self.PrevY[e[1]] is not None:
                        gx.DrawLine(pen, System.Drawing.Point(xC, self.PrevY[e[1]]), System.Drawing.Point(xC + 1, yC))
                    else:
                        gx.DrawLine(pen, System.Drawing.Point(xC + 1, yC), System.Drawing.Point(xC+1, yC+1))
                    self.PrevY[e[1]] = yC
                except:
                    #import sys
                    #print "Error at %f: %s" % (x, sys.exc_value)
                    self.PrevY[e[1]] = None

    def Plot(self):

        self.g.xMin = eval(self.g.xMinText)
        self.g.xMax = eval(self.g.xMaxText)
        self.g.xScale = eval(self.g.xScaleText)

        self.g.yMin = eval(self.g.yMinText)
        self.g.yMax = eval(self.g.yMaxText)
        self.g.yScale = eval(self.g.yScaleText)
        
        self.graphLabel.Refresh()


System.Windows.Forms.Application.EnableVisualStyles()
System.Windows.Forms.Application.Run(MainForm())