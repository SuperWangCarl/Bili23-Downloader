import wx
import wx.py
import datetime
import subprocess
from threading import Thread

from .templates import *
from .about import AboutWindow
from .processing import ProcessingWindow
from .login import LoginWindow
from .user import UserWindow
from .settings import SettingWindow
from .download import DownloadWindow
from .debug import DebugWindow

from utils.config import Config
from utils.tools import *
from utils.video import VideoInfo, VideoParser
from utils.bangumi import BangumiInfo, BangumiParser
from utils.live import LiveInfo, LiveParser
from utils.audio import AudioInfo, AudioParser
from utils.cheese import CheeseInfo, CheeseParser
from utils.api import API

class MainWindow(Frame):
    def __init__(self, parent):
        Frame.__init__(self, parent, Config.app_name)

        self.init_UI()

        self.Bind_EVT()

        self.SetSize(self.FromDIP((750, 420)))

        self.CenterOnParent()

        self.init_utils()

    def init_utils(self):
        wx.CallAfter(self.init_userinfo)

        self.check_ffmpeg()
        self.check_login()

        if Config.check_update:
            Thread(target = self.check_update).start()

        self.video_parser = VideoParser(self.onError, self.onRedirect)
        self.bangumi_parser = BangumiParser(self.onError)
        self.live_parser = LiveParser(self.onError)
        self.audio_parser = AudioParser(self.onError)
        self.cheese_parser = CheeseParser(self.onError)

        wx.CallAfter(self.treelist.SetFocus)

        self.show_download_window = False

    def init_userinfo(self):
        if Config.user_login:
            face = wx.Image(get_face_pic(Config.user_face)).Scale(36, 36)

            self.face.Show()

            self.face.SetBitmap(wx.Bitmap(face, wx.BITMAP_SCREEN_DEPTH))
            self.uname_lab.SetLabel(Config.user_name)

            self.user_menuitem.SetItemLabel("用户中心(&E)")
        else:
            self.face.Hide()

            self.uname_lab.SetLabel("未登录")

            self.user_menuitem.SetItemLabel("登录(&L)")

        
        self.userinfo_hbox.Layout()

        self.vbox.Layout()
    
    def init_UI(self):
        self.infobar = InfoBar(self.panel, self.OnOpenBrowser)

        url_hbox = wx.BoxSizer(wx.HORIZONTAL)

        url_lab = wx.StaticText(self.panel, -1, "地址")
        self.url_box = wx.TextCtrl(self.panel, -1, style = wx.TE_PROCESS_ENTER)
        self.get_btn = wx.Button(self.panel, -1, "Get")

        url_hbox.Add(url_lab, 0, wx.ALL | wx.ALIGN_CENTER, 10)
        url_hbox.Add(self.url_box, 1, wx.EXPAND | wx.ALL & ~(wx.LEFT), 10)
        url_hbox.Add(self.get_btn, 0, wx.ALL & ~(wx.LEFT) | wx.ALIGN_CENTER, 10)

        quality_hbox = wx.BoxSizer(wx.HORIZONTAL)

        self.type_lab = wx.StaticText(self.panel, -1, "视频")
        quality_lab = wx.StaticText(self.panel, -1, "清晰度")
        self.quality_choice = wx.Choice(self.panel, -1)

        quality_hbox.Add(self.type_lab, 0, wx.LEFT | wx.RIGHT | wx.ALIGN_CENTER, 10)
        quality_hbox.AddStretchSpacer()
        quality_hbox.Add(quality_lab, 0, wx.LEFT | wx.RIGHT | wx.ALIGN_CENTER, 10)
        quality_hbox.Add(self.quality_choice, 0, wx.RIGHT | wx.ALIGN_CENTER, 10)

        self.treelist = TreeListCtrl(self.panel, self.onError)
        self.treelist.SetSize(self.FromDIP((800, 260)))

        bottom_hbox = wx.BoxSizer(wx.HORIZONTAL)

        self.download_mgr_btn = wx.Button(self.panel, -1, "下载管理", size = self.FromDIP((90, 30)))
        self.download_btn = wx.Button(self.panel, -1, "下载视频", size = self.FromDIP((90, 30)))
        self.download_btn.Enable(False)
        
        self.userinfo_hbox = wx.BoxSizer(wx.HORIZONTAL)

        self.face = wx.StaticBitmap(self.panel, -1)
        
        self.face.Cursor = wx.Cursor(wx.CURSOR_HAND)
        self.uname_lab = wx.StaticText(self.panel, -1, "用户名")
        self.uname_lab.Cursor = wx.Cursor(wx.CURSOR_HAND)

        self.userinfo_hbox.Add(self.face, 0, wx.ALL & ~(wx.TOP) & ~(wx.RIGHT), 10)
        self.userinfo_hbox.Add(self.uname_lab, 0, wx.ALL & ~(wx.TOP) | wx.ALIGN_CENTER, 10)

        bottom_hbox.Add(self.userinfo_hbox, 0, wx.EXPAND)
        bottom_hbox.AddStretchSpacer()
        bottom_hbox.Add(self.download_mgr_btn, 0, wx.ALL & ~(wx.TOP), 10)
        bottom_hbox.Add(self.download_btn, 0, wx.ALL & ~(wx.TOP) & ~(wx.LEFT), 10)

        self.vbox = wx.BoxSizer(wx.VERTICAL)

        self.vbox.Add(self.infobar, 1, wx.EXPAND)
        self.vbox.Add(url_hbox, 0, wx.EXPAND)
        self.vbox.Add(quality_hbox, 0, wx.EXPAND)
        self.vbox.Add(self.treelist, 1, wx.ALL | wx.EXPAND, 10)
        self.vbox.Add(bottom_hbox, 0, wx.EXPAND)

        self.panel.SetSizer(self.vbox)
        self.init_menubar()

        self.vbox.Fit(self)

    def init_menubar(self):
        menu_bar = wx.MenuBar()
        self.help_menu = wx.Menu()
        self.tool_menu = wx.Menu()
        
        menu_bar.Append(self.tool_menu, "工具(&T)")
        menu_bar.Append(self.help_menu, "帮助(&H)")

        self.user_id = wx.NewIdRef()
        user_title = "用户中心(&E)" if Config.user_login else "登录(&L)"
        self.user_menuitem = wx.MenuItem(self.tool_menu, self.user_id, user_title)
        self.tool_menu.Append(self.user_menuitem)
        
        self.console_id = wx.NewIdRef()
        self.tool_menu.Append(self.console_id, "控制台(&O)")

        self.tool_menu.AppendSeparator()
        
        self.settings_id = wx.NewIdRef()
        self.tool_menu.Append(self.settings_id, "设置(&S)")

        self.debug_id = wx.NewIdRef()
        if Config.debug:
            self.tool_menu.Append(self.debug_id, "调试(&D)")

        self.check_update_id = wx.NewIdRef()
        self.help_menu.Append(self.check_update_id, "检查更新(&U)")
        
        self.change_log_id = wx.NewIdRef()
        self.help_menu.Append(self.change_log_id, "更新日志(&P)")

        self.help_menu.AppendSeparator()

        self.help_id = wx.NewIdRef()
        self.help_menu.Append(self.help_id, "使用帮助(&C)")
        
        self.about_id = wx.NewIdRef()
        self.help_menu.Append(self.about_id, "关于(&A)")

        self.SetMenuBar(menu_bar)
    
    def Bind_EVT(self):
        self.Bind(wx.EVT_MENU, self.menu_EVT)

        self.url_box.Bind(wx.EVT_TEXT_ENTER, self.get_btn_EVT)
        
        self.url_box.Bind(wx.EVT_SET_FOCUS, self.onSetFoucus)
        self.url_box.Bind(wx.EVT_KILL_FOCUS, self.onKillFocus)

        self.get_btn.Bind(wx.EVT_BUTTON, self.get_btn_EVT)
        
        self.uname_lab.Bind(wx.EVT_LEFT_DOWN, self.userinfo_EVT)
        self.face.Bind(wx.EVT_LEFT_DOWN, self.userinfo_EVT)

        self.download_mgr_btn.Bind(wx.EVT_BUTTON, self.download_mgr_btn_EVT)
        self.download_btn.Bind(wx.EVT_BUTTON, self.download_btn_EVT)

    def menu_EVT(self, event):
        evt_id = event.GetId()

        if evt_id == self.check_update_id:
            wx.CallAfter(self.check_update, True)

        elif evt_id == self.change_log_id:
            self.dlgbox(get_changelog(), "更新日志", wx.ICON_INFORMATION)

        elif evt_id == self.help_id:
            import webbrowser

            webbrowser.open(API.App.website_api())
            
        elif evt_id == self.about_id:
            AboutWindow(self)

        elif evt_id == self.user_id:
            if Config.user_login:
                UserWindow(self).ShowWindowModal()
            else:
                LoginWindow(self).ShowWindowModal()

        elif evt_id == self.console_id:
            shell = wx.py.shell.ShellFrame(self, -1, "控制台")
        
            shell.CenterOnParent()
            shell.Show()

        elif evt_id == self.settings_id:
            SettingWindow(self).ShowWindowModal()

        elif evt_id == self.debug_id:
            DebugWindow(self).Show()
            
    def get_btn_EVT(self, event):
        url = self.url_box.GetValue()

        if url == "": return

        self.reset()

        self.processing_window = ProcessingWindow(self)

        Thread(target = self.get_thread, args = (url,)).start()

        self.processing_window.ShowWindowModal()

    def get_thread(self, url: str):
        wx.CallAfter(self.treelist.init_list)

        if find_str("b23.tv", url):
            url = process_shortlink(url)

        elif find_str("activity", url):
            url = process_activity_url(url)

        elif find_str("festival", url):
            url = process_festival_url(url)

        if find_str("BV|av", url):
            self.type = VideoInfo
            self.video_parser.parse_url(url)

            self.set_video_list()
            self.set_quality(VideoInfo)

        elif find_str("ep|ss|md", url) and "cheese" not in url:
            self.type = BangumiInfo
            self.bangumi_parser.parse_url(url)

            self.set_bangumi_list()
            self.set_quality(BangumiInfo)

        elif find_str("ep|ss", url) and "cheese" in url:
            self.type = CheeseInfo
            self.cheese_parser.parse_url(url)

            self.set_cheese_list()
            self.set_quality(CheeseInfo)

        elif find_str("live", url):
            self.type = LiveInfo
            self.live_parser.parse_url(url)

            self.set_live_list()

        elif find_str("au|am", url):
            self.type = AudioInfo
            self.audio_parser.parse_url(url)

            self.set_audio_list()
        
        else:
            self.onError(400)

        wx.CallAfter(self.get_finished)

    def reset(self):
        self.quality_choice.Clear()
        self.type_lab.SetLabel("视频")
        self.download_btn.Enable(False)

        VideoInfo.down_pages.clear()
        BangumiInfo.down_episodes.clear()

    def get_finished(self):
        if self.type == LiveInfo:
            self.quality_choice.Enable(False)
            self.download_btn.SetLabel("播放")

        elif self.type == AudioInfo:
            self.quality_choice.Enable(False)
            self.download_btn.SetLabel("下载音频")

        else:
            self.quality_choice.Enable(True)
            self.download_btn.SetLabel("下载视频")

        self.download_btn.Enable(True)

        self.processing_window.Hide()

        self.treelist.SetFocus()

    def set_video_list(self):
        if VideoInfo.type == "collection":
            count = len(VideoInfo.episodes) 
        else:
            count = len(VideoInfo.pages)

        wx.CallAfter(self.treelist.set_video_list)
        self.type_lab.SetLabel("视频 (共 %d 个)" % count)

    def set_bangumi_list(self):
        count = len(BangumiInfo.episodes)

        wx.CallAfter(self.treelist.set_bangumi_list)
        self.type_lab.SetLabel("{} (正片共 {} 集)".format(BangumiInfo.type, count))

        self.check_bangumi()
        
    def set_live_list(self):
        wx.CallAfter(self.treelist.set_live_list)
        self.type_lab.SetLabel("直播")

    def set_audio_list(self):
        wx.CallAfter(self.treelist.set_audio_list)
        self.type_lab.SetLabel("音乐 (共 {} 首)".format(AudioInfo.count))
    
    def set_cheese_list(self):
        count = len(CheeseInfo.episodes)

        wx.CallAfter(self.treelist.set_cheese_list)
        self.type_lab.SetLabel("课程 (共 {} 节)".format(count))

    def set_quality(self, type):
        self.quality_choice.Set(type.quality_desc)
        
        type.quality = Config.default_quality if Config.default_quality in type.quality_id else type.quality_id[0]
        self.quality_choice.Select(type.quality_id.index(type.quality))
    
    def download_btn_EVT(self, event):
        if self.type == LiveInfo:
            self.open_player()
            return

        if not self.treelist.get_allcheckeditem(self.type): return

        self.download_mgr_btn_EVT(0)

        if self.type != AudioInfo:
            quality_id = quality_wrap[self.quality_choice.GetStringSelection()]
        else:
            quality_id = None
            
        self.download_window.add_download_task(self.type, quality_id)

    def download_mgr_btn_EVT(self, event):
        if self.show_download_window:
            self.download_window.Show()
            self.download_window.SetFocus()

            if self.download_window.IsIconized():
                self.download_window.Iconize(False)
        else:
            self.download_window = DownloadWindow(self)
            self.download_window.Show()

            self.show_download_window = True
    
    def userinfo_EVT(self, event):
        if Config.user_login:
            UserWindow(self).ShowWindowModal()
        else:
            LoginWindow(self).ShowWindowModal()

    def open_player(self):
        if Config.player_path == "":
            wx.MessageDialog(self, "未找到播放器\n\n无法找到播放器，请设置播放器路径后再试", "错误", wx.ICON_WARNING).ShowModal()
        else:
            cmd = '{} "{}"'.format(Config.player_path, LiveInfo.playurl)
            subprocess.Popen(cmd, shell = True)

    def OnOpenBrowser(self, event):
        import webbrowser

        webbrowser.open(self.update_url)

        self.infobar.Dismiss()

        event.Skip()

    def check_bangumi(self):
        if BangumiInfo.payment:
            if not Config.user_login:
                self.infobar.ShowMessageInfo(300)
            elif Config.user_vip_status == 0:
                self.infobar.ShowMessageInfo(301)

    def check_update(self, menu = False):
        json = get_update_json()

        if json["error"]:
            if menu:
                self.dlgbox("检查更新失败\n\n目前无法检查更新，请稍候再试", "检查更新", wx.ICON_ERROR)
            else:
                self.infobar.ShowMessageInfo(405)
            return
    
        else:
            if int(json["version_code"]) > Config.app_version_code:
                self.update_url = json["url"]
                if menu:
                    dlg = wx.MessageDialog(self, "有新的更新可用\n\n{}".format(json["changelog"]), "检查更新", wx.ICON_INFORMATION | wx.YES_NO)
                    dlg.SetYesNoLabels("查看", "忽略")

                    if dlg.ShowModal() == wx.ID_YES:
                        import webbrowser

                        webbrowser.open(self.update_url)
                else:
                    wx.CallAfter(self.infobar.ShowMessageInfo, 100)
            else:
                if menu:
                    self.dlgbox("当前没有可用的更新", "检查更新", wx.ICON_INFORMATION)
        
    def check_ffmpeg(self):
        if not Config.ffmpeg_available:
            dlg = wx.MessageDialog(self, "未安装 ffmpeg\n\n检测到您尚未安装 ffmpeg，无法正常合成视频，是否现在安装？", "提示", wx.ICON_INFORMATION | wx.YES_NO)

            if dlg.ShowModal() == wx.ID_YES:
                import webbrowser

                webbrowser.open("https://scott.o5g.top/index.php/archives/120/")

    def check_login(self):
        if Config.user_expire == "":
            return

        expire = datetime.datetime.strptime(Config.user_expire, "%Y-%m-%d %H:%M:%S")
        
        now = datetime.datetime.now()

        if (expire - now).days <= 0:
            wx.MessageDialog(self, "登录过期\n\n登录状态过期，请重新登录。", "提示", wx.ICON_INFORMATION).ShowModal()

    def onSetFoucus(self, event):
        if self.url_box.GetValue() == "请输入 URL 链接":
            self.url_box.Clear()
            self.url_box.SetForegroundColour("black")

        event.Skip()
    
    def onKillFocus(self, event):
        if self.url_box.GetValue() == "":
            self.url_box.SetValue("请输入 URL 链接")
            self.url_box.SetForegroundColour(wx.Colour(117, 117, 117))
        
        event.Skip()

    def onError(self, code: int):
        wx.CallAfter(self.processing_window.Hide)

        self.infobar.ShowMessageInfo(code)

    def onRedirect(self, url: str):
        Thread(target = self.get_thread, args = (url,)).start()
        