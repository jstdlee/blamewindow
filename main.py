import tkinter as tk
from tkinter import ttk, colorchooser
import win32gui
import win32con
import win32api
import ctypes
from ctypes import windll, byref, Structure, c_uint32, c_int
from datetime import datetime as dt

# DWM attributes
DWMWA_BORDER_COLOR = 34
DWMWA_VISIBLE_FRAME_BORDER_THICKNESS = 37

class COLORREF(Structure):
    _fields_ = [("RGB", c_uint32)]

class WindowBorder:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Blame It - Total Blamed: 0")
        self.root.geometry("1200x800")  # Taller window
        self.root.iconbitmap('blame.ico')  # Set the custom icon
        
        # Track window positions and blink states
        self.after_ids = {}
        self.blink_after_ids = {}
        self.blink_states = {}
        self.current_colors = {}
        self.alert_texts = {}  # Store alert texts
        self.blamed_count = 0  # Track number of blamed windows
        self.colored_rows = {}  # Track colored rows
        
        frame = ttk.Frame(self.root, padding="10")
        frame.pack(fill=tk.BOTH, expand=True)
        
        # Window list with scrollbar
        tree_frame = ttk.Frame(frame)
        tree_frame.pack(fill=tk.BOTH, expand=True)
        
        # Create scrollbar frame
        scroll_frame = ttk.Frame(tree_frame)
        scroll_frame.pack(fill=tk.BOTH, expand=True)
        
        # Create vertical scrollbar
        v_scrollbar = ttk.Scrollbar(scroll_frame, orient="vertical")
        v_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Create horizontal scrollbar
        h_scrollbar = ttk.Scrollbar(tree_frame, orient="horizontal")
        h_scrollbar.pack(side=tk.BOTTOM, fill=tk.X)
        
        # Create the treeview with both scrollbars
        self.tree = ttk.Treeview(scroll_frame, columns=("handle", "class", "title"),
                                show="headings", selectmode="browse",
                                yscrollcommand=v_scrollbar.set,
                                xscrollcommand=h_scrollbar.set)
        
        # Configure the scrollbars
        v_scrollbar.configure(command=self.tree.yview)
        h_scrollbar.configure(command=self.tree.xview)
        
        # Configure the columns
        self.tree.heading("handle", text="Windows Handler ID")
        self.tree.heading("class", text="Class Type of Window")
        self.tree.heading("title", text="Title")
        
        # Set column widths with stretch
        self.tree.column("handle", width=120, stretch=False)
        self.tree.column("class", width=200, stretch=True)
        self.tree.column("title", width=880, stretch=True)
        
        # Pack the tree
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # Control frame
        ctrl_frame = ttk.Frame(frame)
        ctrl_frame.pack(fill=tk.X, pady=5)
        
        # Control buttons
        btn_frame = ttk.Frame(ctrl_frame)
        btn_frame.pack(side=tk.LEFT, padx=5)
        
        style = ttk.Style()
        style.configure("Green.TButton", 
                       foreground="white",
                       background="green",
                       padding=(10, 5))
        
        # Create custom button with green background
        blame_btn = tk.Button(btn_frame, 
                            text="Blame It",
                            command=self.set_border_color,
                            bg="green",
                            fg="white",
                            font=("Arial", 10, "bold"),
                            relief=tk.RAISED,
                            padx=10)
        blame_btn.pack(side=tk.LEFT, padx=5)
        
        reset_btn = tk.Button(btn_frame, 
                            text="Reset Blamed Window",
                            command=self.reset_window,
                            bg="#4169E1",  # Royal Blue color
                            fg="white",
                            font=("Arial", 10, "bold"),
                            relief=tk.RAISED,
                            padx=10)
        reset_btn.pack(side=tk.LEFT, padx=5)
        
        refresh_btn = tk.Button(btn_frame, 
                               text="Refresh Window List",
                               command=self.refresh_windows,
                               bg="#4169E1",  # Royal Blue color
                               fg="white",
                               font=("Arial", 10, "bold"),
                               relief=tk.RAISED,
                               padx=10)
        refresh_btn.pack(side=tk.LEFT, padx=5)
        
        # Settings frame
        settings_frame = ttk.LabelFrame(ctrl_frame, text="Settings")
        settings_frame.pack(side=tk.LEFT, padx=20, fill=tk.X, expand=True)
        
        # Text size
        size_frame = ttk.Frame(settings_frame)
        size_frame.pack(side=tk.LEFT, padx=10)
        ttk.Label(size_frame, text="Text Size:").pack(side=tk.LEFT)
        self.text_size = tk.StringVar(value="22")  # Default: 22
        size_spin = ttk.Spinbox(size_frame, from_=8, to=24, width=3,
                              textvariable=self.text_size)
        size_spin.pack(side=tk.LEFT, padx=5)
        self.text_size.trace_add('write', lambda *args: [self.update_alert_style(*args), self.update_status_message()])
        
        # Bold option
        self.bold_var = tk.BooleanVar(value=True)  # Default: Bold
        bold_check = ttk.Checkbutton(settings_frame, text="Bold",
                                   variable=self.bold_var)
        bold_check.pack(side=tk.LEFT, padx=10)
        self.bold_var.trace_add('write', lambda *args: [self.update_alert_style(*args), self.update_status_message()])
        
        # Transparency
        trans_frame = ttk.Frame(settings_frame)
        trans_frame.pack(side=tk.LEFT, padx=10)
        ttk.Label(trans_frame, text="Transparency:").pack(side=tk.LEFT)
        self.transparency = tk.StringVar(value="20")  # Default: 20%
        trans_spin = ttk.Spinbox(trans_frame, from_=0, to=90, increment=10, width=3,
                               textvariable=self.transparency)
        trans_spin.pack(side=tk.LEFT, padx=5)
        self.transparency.trace_add('write', lambda *args: [self.update_alert_style(*args), self.update_status_message()])
        
        # Blink frequency
        blink_frame = ttk.Frame(settings_frame)
        blink_frame.pack(side=tk.LEFT, padx=10)
        ttk.Label(blink_frame, text="Blink (Hz):").pack(side=tk.LEFT)
        self.blink_freq = tk.StringVar(value="3")
        freq_spin = ttk.Spinbox(blink_frame, from_=0.5, to=5, increment=0.5, width=3,
                              textvariable=self.blink_freq)
        freq_spin.pack(side=tk.LEFT, padx=5)
        self.blink_freq.trace_add('write', lambda *args: [self.update_blink_rate(*args), self.update_status_message()])
        
        # Position dropdown
        pos_frame = ttk.Frame(settings_frame)
        pos_frame.pack(side=tk.LEFT, padx=10)
        ttk.Label(pos_frame, text="Position:").pack(side=tk.LEFT)
        self.position_var = tk.StringVar(value="top-middle")
        pos_menu = ttk.OptionMenu(pos_frame, self.position_var,
                                "top-middle", "top-left", "top-middle", "top-right")
        pos_menu.pack(side=tk.LEFT, padx=5)
        self.position_var.trace_add('write', lambda *args: [self.update_alert_position(*args), self.update_status_message()])
        
        # Status
        self.status = tk.StringVar()
        self.status_label = ttk.Label(self.root, wraplength=1150)  # Allow text to wrap
        self.status_label.pack(side=tk.BOTTOM, fill=tk.X, padx=5, pady=5)
        
        # Dictionary to store alert windows
        self.alert_windows = {}
        
        self.refresh_windows()
    
    def update_alert_style(self, *args):
        for hwnd, alert_win in self.alert_windows.items():
            try:
                font_weight = "bold" if self.bold_var.get() else "normal"
                font_size = int(self.text_size.get())
                alpha = 1 - (float(self.transparency.get()) / 100)
                
                label = alert_win.winfo_children()[0]
                label.configure(font=('TkDefaultFont', font_size, font_weight))
                alert_win.attributes('-alpha', alpha)
                
                # Update position as size might have changed
                self.update_alert_position()
            except:
                pass
    
    def update_alert_position(self, *args):
        for hwnd, alert_win in self.alert_windows.items():
            try:
                if not win32gui.IsWindow(hwnd):
                    self.cleanup_window(hwnd)
                    continue
                
                # Check if target window is focused
                foreground_hwnd = win32gui.GetForegroundWindow()
                if foreground_hwnd != hwnd:
                    alert_win.lower()  # Put alert below other windows
                else:
                    alert_win.lift()  # Bring alert to top
                
                label = alert_win.winfo_children()[0]
                x, y, right, bottom = win32gui.GetWindowRect(hwnd)
                width = right - x
                
                alert_width = label.winfo_reqwidth()
                position = self.position_var.get()
                
                # Align with offset from window edges
                if position == "top-left":
                    new_x = x + 10  # 10 pixels from left edge
                elif position == "top-right":
                    new_x = right - alert_width - 10  # 10 pixels from right edge
                else:  # top-middle
                    new_x = x + (width - alert_width) // 2
                
                alert_height = label.winfo_reqheight()
                new_y = y - alert_height
                
                alert_win.geometry(f'{alert_width}x{alert_height}+{new_x}+{new_y}')
            except Exception:
                pass
    
    def update_blink_rate(self, *args):
        try:
            # Validate frequency input
            new_freq = float(self.blink_freq.get())
            # Restart blinking for all blamed windows with new frequency
            for hwnd in list(self.blink_states.keys()):
                if hwnd in self.blink_after_ids:
                    self.root.after_cancel(self.blink_after_ids[hwnd])
                self.start_blinking(hwnd)
        except ValueError:
            pass  # Invalid frequency input, ignore
        except Exception as e:
            print(f"Error in update_blink_rate: {e}")
    
    def refresh_windows(self):
        # Clear tree
        for item in self.tree.get_children():
            self.tree.delete(item)
        
        def callback(hwnd, _):
            if win32gui.IsWindowVisible(hwnd):
                title = win32gui.GetWindowText(hwnd)
                class_name = win32gui.GetClassName(hwnd)
                if title and class_name:  # Only add windows with both title and class
                    item = self.tree.insert("", "end", values=(hex(hwnd), class_name, title))
                    
                    # If this window is colored, reapply the color
                    if hwnd in self.colored_rows:
                        self.tree.item(item, tags=(self.colored_rows[hwnd],))
        
        win32gui.EnumWindows(callback, None)
    
    def rgb_to_colorref(self, r, g, b):
        # Windows COLORREF format is 0x00bbggrr
        return r | (g << 8) | (b << 16) | (0 << 24)
    
    def start_blinking(self, hwnd):
        try:
            def blink():
                try:
                    if hwnd in self.blink_states and win32gui.IsWindow(hwnd):
                        # Toggle the blink state
                        self.blink_states[hwnd] = not self.blink_states[hwnd]
                        
                        # Calculate the delay based on frequency (in Hz)
                        try:
                            freq = float(self.blink_freq.get())
                            if freq <= 0:  # Avoid division by zero
                                freq = 0.5
                            delay = int(1000 / (2 * freq))  # Convert to milliseconds (half period)
                        except ValueError:
                            delay = 500  # Default to 1Hz if invalid frequency
                        
                        if self.blink_states[hwnd]:
                            # Apply the original color
                            if hwnd in self.current_colors:
                                r, g, b = self.current_colors[hwnd]
                                color_ref = self.rgb_to_colorref(r, g, b)
                                windll.dwmapi.DwmSetWindowAttribute(
                                    hwnd,
                                    DWMWA_BORDER_COLOR,
                                    byref(c_uint32(color_ref)),
                                    ctypes.sizeof(c_uint32)
                                )
                        else:
                            # Set border to transparent/black
                            color_ref = self.rgb_to_colorref(0, 0, 0)
                            windll.dwmapi.DwmSetWindowAttribute(
                                hwnd,
                                DWMWA_BORDER_COLOR,
                                byref(c_uint32(color_ref)),
                                ctypes.sizeof(c_uint32)
                            )
                        
                        # Schedule next blink with current frequency
                        if hwnd in self.blink_states:  # Check if still blinking
                            self.blink_after_ids[hwnd] = self.root.after(delay, blink)
                except Exception as e:
                    print(f"Error in blink function: {e}")
                    if hwnd in self.blink_states:
                        del self.blink_states[hwnd]
            
            # Cancel any existing blink cycle
            if hwnd in self.blink_after_ids:
                self.root.after_cancel(self.blink_after_ids[hwnd])
            
            # Initialize blink state and start immediately
            self.blink_states[hwnd] = True
            blink()  # Start the blink cycle immediately
            
        except Exception as e:
            print(f"Error in start_blinking: {e}")
    
    def set_border_color(self):
        selection = self.tree.selection()
        if not selection:
            self.status.set("Select a window first")
            return
        
        hwnd = int(self.tree.item(selection[0])['values'][0], 16)
        window_title = self.tree.item(selection[0])['values'][2]
        
        # Get color from user first
        color = colorchooser.askcolor(title="Choose Border Color")
        if not color[0]:
            return
        
        # Create and position text input dialog
        alert_dialog = tk.Toplevel(self.root)
        alert_dialog.title("Enter Alert Text")
        alert_dialog.geometry("300x100")
        
        # Center on screen
        screen_width = alert_dialog.winfo_screenwidth()
        screen_height = alert_dialog.winfo_screenheight()
        x = (screen_width - 300) // 2
        y = (screen_height - 100) // 2
        alert_dialog.geometry(f"300x100+{x}+{y}")
        
        alert_dialog.transient(self.root)
        alert_dialog.grab_set()
        
        alert_entry = ttk.Entry(alert_dialog, width=30)
        alert_entry.pack(pady=5)
        
        # Pre-fill with existing text if any
        if hwnd in self.alert_texts:
            alert_entry.insert(0, self.alert_texts[hwnd])
            alert_entry.select_range(0, tk.END)
        
        def on_ok(event=None):
            alert_text = alert_entry.get()
            self.alert_texts[hwnd] = alert_text  # Store the text
            alert_dialog.destroy()
            self.apply_color_and_alert(hwnd, color[0], alert_text, window_title)
        
        alert_dialog.bind('<Return>', on_ok)
        ttk.Button(alert_dialog, text="Set", command=on_ok).pack(pady=5)
        
        # Focus and select all text
        alert_entry.focus_set()
        
    def apply_color_and_alert(self, hwnd, color_rgb, alert_text, window_title):
        try:
            if hwnd not in self.alert_windows:
                self.blamed_count += 1
                self.root.title(f"Blame It - Total Blamed: {self.blamed_count}")
            
            # Store current color for blinking
            r, g, b = map(int, color_rgb)
            self.current_colors[hwnd] = (r, g, b)
            self.blink_states[hwnd] = True
            
            # Color the row in treeview
            for item in self.tree.get_children():
                if int(self.tree.item(item)['values'][0], 16) == hwnd:
                    # Create a unique tag for this row
                    tag_name = f'color_{hwnd}'
                    self.colored_rows[hwnd] = tag_name
                    
                    # Configure tag with window color (slightly lighter for better visibility)
                    lighter_color = f'#{min(r + 40, 255):02x}{min(g + 40, 255):02x}{min(b + 40, 255):02x}'
                    self.tree.tag_configure(tag_name, background=lighter_color)
                    
                    # Apply tag to row
                    self.tree.item(item, tags=(tag_name,))
                    break
            
            # Create detailed status message with line breaks for readability
            text_size = self.text_size.get()
            bold = "Yes" if self.bold_var.get() else "No"
            blink = self.blink_freq.get()
            trans = self.transparency.get()
            pos = self.position_var.get()
            
            status_msg = (
                f"Logged: {dt.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
                f"Window: {window_title}\n"
                f"Text: {alert_text}\n"
                f"Settings: Size={text_size}pt, Bold={bold}, "
                f"Blink={blink}Hz, Transparency={trans}%, "
                f"Position={pos}"
            )
            self.status_label.configure(text=status_msg)
            
            # Save original styles
            self.original_style = win32gui.GetWindowLong(hwnd, win32con.GWL_STYLE)
            self.original_ex_style = win32gui.GetWindowLong(hwnd, win32con.GWL_EXSTYLE)
            
            # Add border styles
            new_style = self.original_style | win32con.WS_THICKFRAME
            new_ex_style = self.original_ex_style | win32con.WS_EX_WINDOWEDGE
            
            win32gui.SetWindowLong(hwnd, win32con.GWL_STYLE, new_style)
            win32gui.SetWindowLong(hwnd, win32con.GWL_EXSTYLE, new_ex_style)
            
            # Set border color using DWM
            color_ref = COLORREF(self.rgb_to_colorref(r, g, b))
            
            # Create alert window
            if hwnd in self.alert_windows:
                self.alert_windows[hwnd].destroy()
                if hwnd in self.after_ids:
                    self.root.after_cancel(self.after_ids[hwnd])
                if hwnd in self.blink_after_ids:
                    self.root.after_cancel(self.blink_after_ids[hwnd])
            
            self.create_alert_window(hwnd, alert_text)
            
            dwmapi = windll.dwmapi
            
            # Set the border color
            dwmapi.DwmSetWindowAttribute(
                hwnd,
                DWMWA_BORDER_COLOR,
                byref(color_ref),
                ctypes.sizeof(COLORREF)
            )
            
            # Update window
            win32gui.SetWindowPos(
                hwnd, None, 0, 0, 0, 0,
                win32con.SWP_NOMOVE | 
                win32con.SWP_NOSIZE | 
                win32con.SWP_NOZORDER | 
                win32con.SWP_FRAMECHANGED
            )
            
            win32gui.RedrawWindow(
                hwnd, None, None,
                win32con.RDW_FRAME | 
                win32con.RDW_INVALIDATE | 
                win32con.RDW_UPDATENOW
            )
            
            # Start blinking immediately after applying color
            self.start_blinking(hwnd)
                        
        except Exception as e:
            self.status_label.configure(text=f"Error: {str(e)}")
    
    def create_alert_window(self, hwnd, text):
        if hwnd in self.alert_windows:
            self.alert_windows[hwnd].destroy()
        
        alert_win = tk.Toplevel(self.root)
        alert_win.overrideredirect(True)
        alert_win.attributes('-topmost', True)
        
        # Calculate reversed color for background
        r, g, b = self.current_colors[hwnd]
        reversed_color = f'#{255-r:02x}{255-g:02x}{255-b:02x}'
        
        # Create label with reversed background color and original text color
        label = tk.Label(alert_win, text=text, justify=tk.CENTER)
        label.pack(expand=True, fill=tk.BOTH)
        
        # Apply current style settings with original color for text
        self.apply_alert_style(label, reversed_color, f'#{r:02x}{g:02x}{b:02x}')
        
        self.alert_windows[hwnd] = alert_win
        
        # Start position tracking
        self.track_window_position(hwnd, alert_win)
        
    def track_window_position(self, hwnd, alert_win):
        def update_position():
            try:
                if hwnd in self.alert_windows and win32gui.IsWindow(hwnd):
                    # Keep alert window always on top
                    alert_win.lift()
                    alert_win.attributes('-topmost', True)
                    
                    # Get target window position
                    x, y, right, bottom = win32gui.GetWindowRect(hwnd)
                    width = right - x
                    
                    # Get alert dimensions
                    label = alert_win.winfo_children()[0]
                    alert_width = label.winfo_reqwidth()
                    alert_height = label.winfo_reqheight()
                    
                    # Calculate position based on selection
                    position = self.position_var.get()
                    if position == "top-left":
                        new_x = x + 10  # 10 pixels from left edge
                    elif position == "top-right":
                        new_x = right - alert_width - 10  # 10 pixels from right edge
                    else:  # top-middle
                        new_x = x + (width - alert_width) // 2
                    
                    new_y = y - alert_height
                    
                    # Update position
                    alert_win.geometry(f'{alert_width}x{alert_height}+{new_x}+{new_y}')
                    
                    # Schedule next update
                    self.after_ids[hwnd] = self.root.after(16, update_position)  # ~60fps update rate
                else:
                    self.cleanup_window(hwnd)
            except Exception:
                self.cleanup_window(hwnd)
        
        # Start tracking
        update_position()
    
    def apply_alert_style(self, label, bg_color, text_color):
        try:
            # Get current settings
            size = int(self.text_size.get())
            bold = "bold" if self.bold_var.get() else "normal"
            trans = int(self.transparency.get())
            
            # Configure font and colors - use original color for text
            label.configure(
                font=("Arial", size, bold),
                bg=bg_color,  # Reversed color for background
                fg=text_color  # Original color for text
            )
            
            # Set transparency
            opacity = (100 - trans) / 100
            label.winfo_toplevel().attributes('-alpha', opacity)
        except Exception as e:
            self.status_label.configure(text=f"Error applying style: {str(e)}")
    
    def get_contrasting_text_color(self, bg_color):
        # Convert hex color to RGB
        bg_rgb = tuple(int(bg_color[i:i+2], 16) for i in (1, 3, 5))
        
        # Calculate luminance
        luminance = (0.299 * bg_rgb[0] + 0.587 * bg_rgb[1] + 0.114 * bg_rgb[2]) / 255
        
        # Return black or white based on background brightness
        return '#000000' if luminance > 0.5 else '#ffffff'
    
    def cleanup_window(self, hwnd):
        if hwnd in self.alert_windows:
            self.alert_windows[hwnd].destroy()
            del self.alert_windows[hwnd]
        if hwnd in self.after_ids:
            self.root.after_cancel(self.after_ids[hwnd])
            del self.after_ids[hwnd]
        if hwnd in self.blink_after_ids:
            self.root.after_cancel(self.blink_after_ids[hwnd])
            del self.blink_after_ids[hwnd]
        if hwnd in self.blink_states:
            del self.blink_states[hwnd]
    
    def reset_window(self):
        selection = self.tree.selection()
        if not selection:
            self.status_label.configure(text="Select a window first")
            return
        
        hwnd = int(self.tree.item(selection[0])['values'][0], 16)
        
        try:
            if hwnd in self.alert_windows:
                self.blamed_count -= 1
                self.root.title(f"Blame It - Total Blamed: {self.blamed_count}")
            
            # Remove row color
            if hwnd in self.colored_rows:
                for item in self.tree.get_children():
                    if int(self.tree.item(item)['values'][0], 16) == hwnd:
                        self.tree.item(item, tags=())
                del self.colored_rows[hwnd]
            
            self.cleanup_window(hwnd)
            if hwnd in self.alert_texts:
                del self.alert_texts[hwnd]
            
            # Reset border color
            color_ref = COLORREF(0xFFFFFFFF)
            dwmapi = windll.dwmapi
            dwmapi.DwmSetWindowAttribute(
                hwnd,
                DWMWA_BORDER_COLOR,
                byref(color_ref),
                ctypes.sizeof(COLORREF)
            )
            
            # Reset border thickness
            thickness = c_int(1)
            dwmapi.DwmSetWindowAttribute(
                hwnd,
                DWMWA_VISIBLE_FRAME_BORDER_THICKNESS,
                byref(thickness),
                ctypes.sizeof(c_int)
            )
            
            # Restore original styles
            if hasattr(self, 'original_style'):
                win32gui.SetWindowLong(hwnd, win32con.GWL_STYLE, self.original_style)
            if hasattr(self, 'original_ex_style'):
                win32gui.SetWindowLong(hwnd, win32con.GWL_EXSTYLE, self.original_ex_style)
            
            # Update window
            win32gui.SetWindowPos(
                hwnd, None, 0, 0, 0, 0,
                win32con.SWP_NOMOVE | 
                win32con.SWP_NOSIZE | 
                win32con.SWP_NOZORDER | 
                win32con.SWP_FRAMECHANGED
            )
            
            win32gui.RedrawWindow(
                hwnd, None, None,
                win32con.RDW_FRAME | 
                win32con.RDW_INVALIDATE | 
                win32con.RDW_UPDATENOW
            )
            
            self.status_label.configure(text="Window reset")
            
        except Exception as e:
            self.status_label.configure(text=f"Error: {str(e)}")

    def update_status_message(self):
        selection = self.tree.selection()
        if selection:
            hwnd = int(self.tree.item(selection[0])['values'][0], 16)
            if hwnd in self.alert_texts:  # Only update if window is blamed
                window_title = self.tree.item(selection[0])['values'][2]
                text_size = self.text_size.get()
                bold = "Yes" if self.bold_var.get() else "No"
                blink = self.blink_freq.get()
                trans = self.transparency.get()
                pos = self.position_var.get()
                
                status_msg = (
                    f"Window: {window_title}\n"
                    f"Text: {self.alert_texts[hwnd]}\n"
                    f"Settings: Size={text_size}pt, Bold={bold}, "
                    f"Blink={blink}Hz, Transparency={trans}%, "
                    f"Position={pos}"
                )
                self.status_label.configure(text=status_msg)

    def run(self):
        # Start auto-refresh
        def auto_refresh():
            self.refresh_windows()
            self.root.after(10000, auto_refresh)  # Every 10 seconds
        
        auto_refresh()  # Start the auto-refresh cycle
        self.root.mainloop()

def main():
    app = WindowBorder()
    app.run()

if __name__ == "__main__":
    main()
    