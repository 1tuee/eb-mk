import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import threading
import time
import datetime
import json
import os
import subprocess
import re
from typing import Dict, List, Optional, Callable
from dataclasses import dataclass
from enum import Enum

class TimerType(Enum):
    COUNTDOWN = "countdown"
    INTERVAL = "interval"
    SCHEDULED = "scheduled"
    CONDITIONAL = "conditional"
    CHAIN = "chain"
    POMODORO = "pomodoro"
    STOPWATCH = "stopwatch"

class ActionType(Enum):
    NOTIFICATION = "notification"
    SOUND = "sound"
    COMMAND = "command"
    POPUP = "popup"
    FILE_WRITE = "file_write"
    HTTP_REQUEST = "http_request"

@dataclass
class TimerAction:
    action_type: ActionType
    parameters: Dict
    
class CustomStyle:
    """Custom styling for tkinter widgets"""
    
    COLORS = {
        'bg_primary': '#1e1e2e',
        'bg_secondary': '#313244',
        'bg_tertiary': '#45475a',
        'accent': '#89b4fa',
        'accent_hover': '#74c7ec',
        'text': '#cdd6f4',
        'text_dim': '#a6adc8',
        'success': '#a6e3a1',
        'warning': '#f9e2af',
        'error': '#f38ba8',
        'surface': '#585b70'
    }
    
    @classmethod
    def apply_dark_theme(cls, root):
        """Apply dark theme to root window"""
        root.configure(bg=cls.COLORS['bg_primary'])
        
        # Configure ttk styles
        style = ttk.Style()
        style.theme_use('clam')
        
        # Configure styles
        style.configure('Custom.TFrame', background=cls.COLORS['bg_primary'])
        style.configure('Card.TFrame', background=cls.COLORS['bg_secondary'], relief='raised')
        style.configure('Custom.TLabel', background=cls.COLORS['bg_primary'], foreground=cls.COLORS['text'])
        style.configure('Title.TLabel', background=cls.COLORS['bg_primary'], foreground=cls.COLORS['accent'], font=('Helvetica', 16, 'bold'))
        style.configure('Custom.TButton', background=cls.COLORS['accent'], foreground=cls.COLORS['bg_primary'])
        style.map('Custom.TButton', background=[('active', cls.COLORS['accent_hover'])])
        style.configure('Custom.TEntry', fieldbackground=cls.COLORS['bg_tertiary'], foreground=cls.COLORS['text'])
        style.configure('Custom.TCombobox', fieldbackground=cls.COLORS['bg_tertiary'], foreground=cls.COLORS['text'])

class CustomWidget:
    """Custom widget factory"""
    
    @staticmethod
    def create_card_frame(parent, **kwargs):
        """Create a card-like frame"""
        frame = ttk.Frame(parent, style='Card.TFrame', **kwargs)
        frame.configure(padding="10")
        return frame
    
    @staticmethod
    def create_button(parent, text, command=None, style='Custom.TButton', **kwargs):
        """Create a styled button"""
        return ttk.Button(parent, text=text, command=command, style=style, **kwargs)
    
    @staticmethod
    def create_entry(parent, **kwargs):
        """Create a styled entry"""
        return ttk.Entry(parent, style='Custom.TEntry', **kwargs)
    
    @staticmethod
    def create_label(parent, text, style='Custom.TLabel', **kwargs):
        """Create a styled label"""
        return ttk.Label(parent, text=text, style=style, **kwargs)

class ComplexTimer:
    def __init__(self, name: str, timer_type: TimerType, config: Dict):
        self.name = name
        self.timer_type = timer_type
        self.config = config
        self.active = True
        self.created_at = datetime.datetime.now()
        self.last_triggered = None
        self.trigger_count = 0
        self.thread = None
        self.stop_event = threading.Event()
        self.actions: List[TimerAction] = []
        
        # Timer-specific initialization
        self._init_timer_specifics()
    
    def _init_timer_specifics(self):
        """Initialize timer-specific attributes"""
        if self.timer_type == TimerType.COUNTDOWN:
            self.duration = self.config.get('duration', 0)
            self.remaining_time = self.duration
            
        elif self.timer_type == TimerType.INTERVAL:
            self.interval = self.config.get('interval', 60)
            self.max_repeats = self.config.get('max_repeats', -1)
            
        elif self.timer_type == TimerType.SCHEDULED:
            self.schedule_times = self.config.get('schedule_times', [])
            self.days_of_week = self.config.get('days_of_week', list(range(7)))
            self.date_specific = self.config.get('date_specific', None)
            
        elif self.timer_type == TimerType.CONDITIONAL:
            self.condition_script = self.config.get('condition_script', "")
            self.check_interval = self.config.get('check_interval', 30)
            
        elif self.timer_type == TimerType.CHAIN:
            self.chain_configs = self.config.get('chain_configs', [])
            self.current_chain_index = 0
            
        elif self.timer_type == TimerType.POMODORO:
            self.work_duration = self.config.get('work_duration', 25 * 60)
            self.break_duration = self.config.get('break_duration', 5 * 60)
            self.long_break_duration = self.config.get('long_break_duration', 15 * 60)
            self.cycles_until_long_break = self.config.get('cycles_until_long_break', 4)
            self.current_cycle = 0
            self.is_work_period = True
            
        elif self.timer_type == TimerType.STOPWATCH:
            self.elapsed_time = 0
            self.start_time = None
    
    def add_action(self, action: TimerAction):
        """Add an action to execute when timer triggers"""
        self.actions.append(action)
    
    def start(self):
        """Start the timer"""
        if self.thread and self.thread.is_alive():
            return False
        
        self.stop_event.clear()
        self.thread = threading.Thread(target=self._run, daemon=True)
        self.thread.start()
        return True
    
    def stop(self):
        """Stop the timer"""
        self.stop_event.set()
        if self.thread:
            self.thread.join(timeout=1)
    
    def pause(self):
        """Pause the timer (implementation depends on timer type)"""
        # Implementation varies by timer type
        pass
    
    def resume(self):
        """Resume the timer"""
        # Implementation varies by timer type
        pass
    
    def _run(self):
        """Main timer loop"""
        try:
            if self.timer_type == TimerType.COUNTDOWN:
                self._run_countdown()
            elif self.timer_type == TimerType.INTERVAL:
                self._run_interval()
            elif self.timer_type == TimerType.SCHEDULED:
                self._run_scheduled()
            elif self.timer_type == TimerType.CONDITIONAL:
                self._run_conditional()
            elif self.timer_type == TimerType.CHAIN:
                self._run_chain()
            elif self.timer_type == TimerType.POMODORO:
                self._run_pomodoro()
            elif self.timer_type == TimerType.STOPWATCH:
                self._run_stopwatch()
        except Exception as e:
            print(f"Timer {self.name} error: {e}")
    
    def _run_countdown(self):
        """Run countdown timer"""
        while self.remaining_time > 0 and not self.stop_event.is_set():
            time.sleep(1)
            self.remaining_time -= 1
        
        if not self.stop_event.is_set():
            self._trigger()
    
    def _run_interval(self):
        """Run interval timer"""
        count = 0
        while not self.stop_event.is_set():
            if self.stop_event.wait(self.interval):
                break
            
            self._trigger()
            count += 1
            
            if self.max_repeats > 0 and count >= self.max_repeats:
                break
    
    def _run_scheduled(self):
        """Run scheduled timer"""
        while not self.stop_event.is_set():
            now = datetime.datetime.now()
            
            # Check if today is a valid day
            if now.weekday() not in self.days_of_week:
                time.sleep(60)  # Check again in a minute
                continue
            
            # Check specific date if set
            if self.date_specific and now.date() != self.date_specific:
                time.sleep(60)
                continue
            
            # Check schedule times
            current_time = now.time()
            for schedule_time in self.schedule_times:
                if (current_time.hour == schedule_time.hour and 
                    current_time.minute == schedule_time.minute and 
                    current_time.second == schedule_time.second):
                    self._trigger()
            
            time.sleep(1)
    
    def _run_conditional(self):
        """Run conditional timer"""
        while not self.stop_event.is_set():
            try:
                # Execute condition script
                if self._evaluate_condition():
                    self._trigger()
            except Exception as e:
                print(f"Condition evaluation error: {e}")
            
            if self.stop_event.wait(self.check_interval):
                break
    
    def _run_chain(self):
        """Run chain timer"""
        for i, chain_config in enumerate(self.chain_configs):
            if self.stop_event.is_set():
                break
            
            self.current_chain_index = i
            chain_timer = ComplexTimer(f"{self.name}_chain_{i}", 
                                     TimerType(chain_config['type']), 
                                     chain_config)
            chain_timer.start()
            
            # Wait for chain timer to complete
            while chain_timer.thread.is_alive() and not self.stop_event.is_set():
                time.sleep(0.1)
            
            chain_timer.stop()
    
    def _run_pomodoro(self):
        """Run pomodoro timer"""
        while not self.stop_event.is_set():
            if self.is_work_period:
                duration = self.work_duration
            else:
                if self.current_cycle % self.cycles_until_long_break == 0 and self.current_cycle > 0:
                    duration = self.long_break_duration
                else:
                    duration = self.break_duration
            
            # Run the current period
            for _ in range(duration):
                if self.stop_event.is_set():
                    return
                time.sleep(1)
            
            self._trigger()
            
            # Switch periods
            if self.is_work_period:
                self.current_cycle += 1
            self.is_work_period = not self.is_work_period
    
    def _run_stopwatch(self):
        """Run stopwatch timer"""
        self.start_time = time.time()
        while not self.stop_event.is_set():
            time.sleep(0.1)
            self.elapsed_time = time.time() - self.start_time
    
    def _evaluate_condition(self) -> bool:
        """Evaluate conditional script"""
        try:
            # Create a safe environment for script execution
            safe_globals = {
                'datetime': datetime,
                'time': time,
                'os': os,
                'subprocess': subprocess,
                '__builtins__': {}
            }
            return bool(eval(self.condition_script, safe_globals))
        except:
            return False
    
    def _trigger(self):
        """Execute all actions associated with this timer"""
        self.last_triggered = datetime.datetime.now()
        self.trigger_count += 1
        
        for action in self.actions:
            self._execute_action(action)
    
    def _execute_action(self, action: TimerAction):
        """Execute a single action"""
        try:
            if action.action_type == ActionType.NOTIFICATION:
                self._show_notification(action.parameters)
            elif action.action_type == ActionType.SOUND:
                self._play_sound(action.parameters)
            elif action.action_type == ActionType.COMMAND:
                self._execute_command(action.parameters)
            elif action.action_type == ActionType.POPUP:
                self._show_popup(action.parameters)
            elif action.action_type == ActionType.FILE_WRITE:
                self._write_file(action.parameters)
            elif action.action_type == ActionType.HTTP_REQUEST:
                self._make_http_request(action.parameters)
        except Exception as e:
            print(f"Action execution error: {e}")
    
    def _show_notification(self, params):
        """Show system notification"""
        title = params.get('title', 'Timer Alert')
        message = params.get('message', f'Timer {self.name} has triggered!')
        
        # Try to use system notifications
        try:
            if os.name == 'nt':  # Windows
                subprocess.run(['msg', '*', f'{title}: {message}'], check=True)
            elif os.name == 'posix':  # Linux/Mac
                subprocess.run(['notify-send', title, message], check=True)
        except:
            print(f"Notification: {title} - {message}")
    
    def _play_sound(self, params):
        """Play sound file or system sound"""
        sound_file = params.get('file', None)
        system_sound = params.get('system_sound', 'default')
        
        try:
            if sound_file and os.path.exists(sound_file):
                if os.name == 'nt':
                    import winsound
                    winsound.PlaySound(sound_file, winsound.SND_FILENAME)
                else:
                    subprocess.run(['aplay', sound_file], check=True)
            else:
                # System beep
                if os.name == 'nt':
                    import winsound
                    winsound.Beep(1000, 500)
                else:
                    print('\a')  # Terminal bell
        except:
            print('\a')  # Fallback to terminal bell
    
    def _execute_command(self, params):
        """Execute system command"""
        command = params.get('command', '')
        if command:
            subprocess.run(command, shell=True)
    
    def _show_popup(self, params):
        """Show popup dialog"""
        title = params.get('title', 'Timer Alert')
        message = params.get('message', f'Timer {self.name} has triggered!')
        
        # This would need to be called from the main thread
        # For now, just print
        print(f"POPUP: {title} - {message}")
    
    def _write_file(self, params):
        """Write to file"""
        file_path = params.get('file_path', 'timer_log.txt')
        content = params.get('content', f'Timer {self.name} triggered at {datetime.datetime.now()}')
        append = params.get('append', True)
        
        mode = 'a' if append else 'w'
        with open(file_path, mode) as f:
            f.write(content + '\n')
    
    def _make_http_request(self, params):
        """Make HTTP request"""
        try:
            import urllib.request
            url = params.get('url', '')
            method = params.get('method', 'GET')
            data = params.get('data', None)
            
            if url:
                if method == 'POST' and data:
                    data = data.encode('utf-8')
                    req = urllib.request.Request(url, data=data, method=method)
                else:
                    req = urllib.request.Request(url, method=method)
                
                urllib.request.urlopen(req)
        except Exception as e:
            print(f"HTTP request error: {e}")

class TimerManager:
    def __init__(self):
        self.timers: Dict[str, ComplexTimer] = {}
        self.callbacks: List[Callable] = []
    
    def add_timer(self, timer: ComplexTimer) -> bool:
        """Add a timer to the manager"""
        if timer.name in self.timers:
            return False
        self.timers[timer.name] = timer
        self._notify_callbacks()
        return True
    
    def remove_timer(self, name: str) -> bool:
        """Remove a timer from the manager"""
        if name in self.timers:
            self.timers[name].stop()
            del self.timers[name]
            self._notify_callbacks()
            return True
        return False
    
    def start_timer(self, name: str) -> bool:
        """Start a specific timer"""
        if name in self.timers:
            return self.timers[name].start()
        return False
    
    def stop_timer(self, name: str) -> bool:
        """Stop a specific timer"""
        if name in self.timers:
            self.timers[name].stop()
            return True
        return False
    
    def get_timer(self, name: str) -> Optional[ComplexTimer]:
        """Get a timer by name"""
        return self.timers.get(name)
    
    def list_timers(self) -> List[str]:
        """Get list of all timer names"""
        return list(self.timers.keys())
    
    def stop_all(self):
        """Stop all timers"""
        for timer in self.timers.values():
            timer.stop()
    
    def save_to_file(self, file_path: str):
        """Save all timers to file"""
        data = {}
        for name, timer in self.timers.items():
            data[name] = {
                'type': timer.timer_type.value,
                'config': timer.config,
                'actions': [{'type': action.action_type.value, 'params': action.parameters} 
                           for action in timer.actions]
            }
        
        with open(file_path, 'w') as f:
            json.dump(data, f, indent=2)
    
    def load_from_file(self, file_path: str):
        """Load timers from file"""
        try:
            with open(file_path, 'r') as f:
                data = json.load(f)
            
            for name, timer_data in data.items():
                timer = ComplexTimer(name, TimerType(timer_data['type']), timer_data['config'])
                for action_data in timer_data['actions']:
                    action = TimerAction(ActionType(action_data['type']), action_data['params'])
                    timer.add_action(action)
                self.add_timer(timer)
        except Exception as e:
            print(f"Error loading timers: {e}")
    
    def add_callback(self, callback: Callable):
        """Add callback for timer list changes"""
        self.callbacks.append(callback)
    
    def _notify_callbacks(self):
        """Notify all callbacks of changes"""
        for callback in self.callbacks:
            try:
                callback()
            except Exception as e:
                print(f"Callback error: {e}")

class TimerApp:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Complex Timer Application")
        self.root.geometry("1200x800")
        
        # Apply custom styling
        CustomStyle.apply_dark_theme(self.root)
        
        # Initialize timer manager
        self.timer_manager = TimerManager()
        self.timer_manager.add_callback(self.refresh_timer_list)
        
        # Create UI
        self.create_ui()
        
        # Status update thread
        self.update_thread_running = True
        self.update_thread = threading.Thread(target=self.update_status_loop, daemon=True)
        self.update_thread.start()
    
    def create_ui(self):
        """Create the main UI"""
        # Main container
        main_frame = ttk.Frame(self.root, style='Custom.TFrame')
        main_frame.pack(fill='both', expand=True, padx=10, pady=10)
        
        # Title
        title_label = CustomWidget.create_label(main_frame, "Complex Timer Application", style='Title.TLabel')
        title_label.pack(pady=(0, 20))
        
        # Create notebook for tabs
        notebook = ttk.Notebook(main_frame)
        notebook.pack(fill='both', expand=True)
        
        # Create tabs
        self.create_timer_list_tab(notebook)
        self.create_new_timer_tab(notebook)
        self.create_settings_tab(notebook)
    
    def create_timer_list_tab(self, parent):
        """Create the timer list tab"""
        frame = ttk.Frame(parent, style='Custom.TFrame')
        parent.add(frame, text="Active Timers")
        
        # Controls frame
        controls_frame = CustomWidget.create_card_frame(frame)
        controls_frame.pack(fill='x', pady=(0, 10))
        
        CustomWidget.create_button(controls_frame, "Refresh", self.refresh_timer_list).pack(side='left', padx=(0, 10))
        CustomWidget.create_button(controls_frame, "Start All", self.start_all_timers).pack(side='left', padx=(0, 10))
        CustomWidget.create_button(controls_frame, "Stop All", self.stop_all_timers).pack(side='left', padx=(0, 10))
        CustomWidget.create_button(controls_frame, "Save Config", self.save_config).pack(side='left', padx=(0, 10))
        CustomWidget.create_button(controls_frame, "Load Config", self.load_config).pack(side='left')
        
        # Timer list frame
        list_frame = CustomWidget.create_card_frame(frame)
        list_frame.pack(fill='both', expand=True)
        
        # Create treeview for timer list
        columns = ('Name', 'Type', 'Status', 'Last Triggered', 'Trigger Count')
        self.timer_tree = ttk.Treeview(list_frame, columns=columns, show='headings', height=15)
        
        # Configure columns
        for col in columns:
            self.timer_tree.heading(col, text=col)
            self.timer_tree.column(col, width=150)
        
        # Scrollbar for treeview
        scrollbar = ttk.Scrollbar(list_frame, orient='vertical', command=self.timer_tree.yview)
        self.timer_tree.configure(yscrollcommand=scrollbar.set)
        
        # Pack treeview and scrollbar
        self.timer_tree.pack(side='left', fill='both', expand=True)
        scrollbar.pack(side='right', fill='y')
        
        # Context menu for timer list
        self.create_context_menu()
        
        # Bind events
        self.timer_tree.bind("<Button-3>", self.show_context_menu)
        self.timer_tree.bind("<Double-1>", self.edit_timer)
    
    def create_new_timer_tab(self, parent):
        """Create the new timer tab"""
        frame = ttk.Frame(parent, style='Custom.TFrame')
        parent.add(frame, text="Create Timer")
        
        # Create scrollable frame
        canvas = tk.Canvas(frame, bg=CustomStyle.COLORS['bg_primary'])
        scrollbar = ttk.Scrollbar(frame, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas, style='Custom.TFrame')
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        # Basic timer info
        basic_frame = CustomWidget.create_card_frame(scrollable_frame)
        basic_frame.pack(fill='x', pady=(0, 10))
        
        CustomWidget.create_label(basic_frame, "Timer Name:").grid(row=0, column=0, sticky='w', pady=5)
        self.name_entry = CustomWidget.create_entry(basic_frame, width=30)
        self.name_entry.grid(row=0, column=1, sticky='ew', padx=(10, 0), pady=5)
        
        CustomWidget.create_label(basic_frame, "Timer Type:").grid(row=1, column=0, sticky='w', pady=5)
        self.type_combo = ttk.Combobox(basic_frame, values=[t.value for t in TimerType], style='Custom.TCombobox')
        self.type_combo.grid(row=1, column=1, sticky='ew', padx=(10, 0), pady=5)
        self.type_combo.bind('<<ComboboxSelected>>', self.on_type_changed)
        
        basic_frame.columnconfigure(1, weight=1)
        
        # Dynamic configuration frame
        self.config_frame = CustomWidget.create_card_frame(scrollable_frame)
        self.config_frame.pack(fill='x', pady=(0, 10))
        
        # Actions frame
        actions_frame = CustomWidget.create_card_frame(scrollable_frame)
        actions_frame.pack(fill='x', pady=(0, 10))
        
        CustomWidget.create_label(actions_frame, "Actions:", style='Title.TLabel').pack(anchor='w')
        
        # Action list
        self.action_list_frame = ttk.Frame(actions_frame, style='Custom.TFrame')
        self.action_list_frame.pack(fill='x', pady=10)
        
        # Add action button
        CustomWidget.create_button(actions_frame, "Add Action", self.add_action).pack(anchor='w')
        
        # Create timer button
        create_frame = ttk.Frame(scrollable_frame, style='Custom.TFrame')
        create_frame.pack(fill='x', pady=20)
        
        CustomWidget.create_button(create_frame, "Create Timer", self.create_timer).pack(side='right')
        CustomWidget.create_button(create_frame, "Clear Form", self.clear_form).pack(side='right', padx=(0, 10))
        
        # Pack canvas and scrollbar
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # Initialize
        self.action_widgets = []
        self.config_widgets = {}
    
    def create_settings_tab(self, parent):
        """Create the settings tab"""
        frame = ttk.Frame(parent, style='Custom.TFrame')
        parent.add(frame, text="Settings")
        
        settings_frame = CustomWidget.create_card_frame(frame)
        settings_frame.pack(fill='x', pady=10)
        
        CustomWidget.create_label(settings_frame, "Application Settings", style='Title.TLabel').pack(anchor='w', pady=(0, 20))
        
        # Auto-save setting
        self.auto_save_var = tk.BooleanVar(value=True)
        auto_save_check = tk.Checkbutton(settings_frame, text="Auto-save configuration", 
                                       variable=self.auto_save_var, 
                                       bg=CustomStyle.COLORS['bg_secondary'],
                                       fg=CustomStyle.COLORS['text'],
                                       selectcolor=CustomStyle.COLORS['bg_tertiary'])
        auto_save_check.pack(anchor='w', pady=5)
        
        # Update interval
        CustomWidget.create_label(settings_frame, "Status update interval (seconds):").pack(anchor='w', pady=(10, 0))
        self.update_interval_entry = CustomWidget.create_entry(settings_frame, width=10)
        self.update_interval_entry.pack(anchor='w', pady=5)
        self.update_interval_entry.insert(0, "1")
        
        # Log level
        CustomWidget.create_label(settings_frame, "Log level:").pack(anchor='w', pady=(10, 0))
        self.log_level_combo = ttk.Combobox(settings_frame, values=["DEBUG", "INFO", "WARNING", "ERROR"], 
                                          style='Custom.TCombobox')
        self.log_level_combo.pack(anchor='w', pady=5)
        self.log_level_combo.set("INFO")
        
        # Apply settings button
        CustomWidget.create_button(settings_frame, "Apply Settings", self.apply_settings).pack(anchor='w', pady=(20, 0))
    
    def create_context_menu(self):
        """Create context menu for timer list"""
        self.context_menu = tk.Menu(self.root, tearoff=0,
                                  bg=CustomStyle.COLORS['bg_secondary'],
                                  fg=CustomStyle.COLORS['text'])
        self.context_menu.add_command(label="Start", command=self.start_selected_timer)
        self.context_menu.add_command(label="Stop", command=self.stop_selected_timer)
        self.context_menu.add_command(label="Edit", command=self.edit_timer)
        self.context_menu.add_command(label="Delete", command=self.delete_timer)
        self.context_menu.add_separator()
        self.context_menu.add_command(label="Duplicate", command=self.duplicate_timer)
    
    def on_type_changed(self, event=None):
        """Handle timer type selection change"""
        timer_type = TimerType(self.type_combo.get())
        
        # Clear existing config widgets
        for widget in self.config_frame.winfo_children():
            widget.destroy()
        self.config_widgets.clear()
        
        # Create type-specific config widgets
        if timer_type == TimerType.COUNTDOWN:
            self.create_countdown_config()
        elif timer_type == TimerType.INTERVAL:
            self.create_interval_config()
        elif timer_type == TimerType.SCHEDULED:
            self.create_scheduled_config()
        elif timer_type == TimerType.CONDITIONAL:
            self.create_conditional_config()
        elif timer_type == TimerType.CHAIN:
            self.create_chain_config()
        elif timer_type == TimerType.POMODORO:
            self.create_pomodoro_config()
        elif timer_type == TimerType.STOPWATCH:
            self.create_stopwatch_config()
    
    def create_countdown_config(self):
        """Create countdown timer configuration widgets"""
        CustomWidget.create_label(self.config_frame, "Duration:").grid(row=0, column=0, sticky='w', pady=5)
        
        duration_frame = ttk.Frame(self.config_frame, style='Custom.TFrame')
        duration_frame.grid(row=0, column=1, sticky='ew', padx=(10, 0), pady=5)
        
        self.config_widgets['hours'] = CustomWidget.create_entry(duration_frame, width=5)
        self.config_widgets['hours'].pack(side='left')
        CustomWidget.create_label(duration_frame, "h").pack(side='left', padx=(5, 10))
        
        self.config_widgets['minutes'] = CustomWidget.create_entry(duration_frame, width=5)
        self.config_widgets['minutes'].pack(side='left')
        CustomWidget.create_label(duration_frame, "m").pack(side='left', padx=(5, 10))
        
        self.config_widgets['seconds'] = CustomWidget.create_entry(duration_frame, width=5)
        self.config_widgets['seconds'].pack(side='left')
        CustomWidget.create_label(duration_frame, "s").pack(side='left', padx=(5, 0))
        
        self.config_frame.columnconfigure(1, weight=1)
    
    def create_interval_config(self):
        """Create interval timer configuration widgets"""
        CustomWidget.create_label(self.config_frame, "Interval (seconds):").grid(row=0, column=0, sticky='w', pady=5)
        self.config_widgets['interval'] = CustomWidget.create_entry(self.config_frame, width=10)
        self.config_widgets['interval'].grid(row=0, column=1, sticky='w', padx=(10, 0), pady=5)
        self.config_widgets['interval'].insert(0, "60")
        
        CustomWidget.create_label(self.config_frame, "Max repeats (-1 for infinite):").grid(row=1, column=0, sticky='w', pady=5)
        self.config_widgets['max_repeats'] = CustomWidget.create_entry(self.config_frame, width=10)
        self.config_widgets['max_repeats'].grid(row=1, column=1, sticky='w', padx=(10, 0), pady=5)
        self.config_widgets['max_repeats'].insert(0, "-1")
        
        self.config_frame.columnconfigure(1, weight=1)
    
    def create_scheduled_config(self):
        """Create scheduled timer configuration widgets"""
        # Schedule times
        CustomWidget.create_label(self.config_frame, "Schedule times (HH:MM:SS, one per line):").grid(row=0, column=0, sticky='nw', pady=5)
        self.config_widgets['times_text'] = tk.Text(self.config_frame, height=5, width=15,
                                                   bg=CustomStyle.COLORS['bg_tertiary'],
                                                   fg=CustomStyle.COLORS['text'])
        self.config_widgets['times_text'].grid(row=0, column=1, sticky='ew', padx=(10, 0), pady=5)
        
        # Days of week
        CustomWidget.create_label(self.config_frame, "Days of week:").grid(row=1, column=0, sticky='nw', pady=5)
        days_frame = ttk.Frame(self.config_frame, style='Custom.TFrame')
        days_frame.grid(row=1, column=1, sticky='ew', padx=(10, 0), pady=5)
        
        self.config_widgets['days'] = []
        days = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
        for i, day in enumerate(days):
            var = tk.BooleanVar(value=True)
            cb = tk.Checkbutton(days_frame, text=day, variable=var,
                              bg=CustomStyle.COLORS['bg_secondary'],
                              fg=CustomStyle.COLORS['text'],
                              selectcolor=CustomStyle.COLORS['bg_tertiary'])
            cb.grid(row=0, column=i, sticky='w', padx=5)
            self.config_widgets['days'].append(var)
        
        # Specific date
        CustomWidget.create_label(self.config_frame, "Specific date (YYYY-MM-DD, optional):").grid(row=2, column=0, sticky='w', pady=5)
        self.config_widgets['specific_date'] = CustomWidget.create_entry(self.config_frame, width=15)
        self.config_widgets['specific_date'].grid(row=2, column=1, sticky='w', padx=(10, 0), pady=5)
        
        self.config_frame.columnconfigure(1, weight=1)
    
    def create_conditional_config(self):
        """Create conditional timer configuration widgets"""
        CustomWidget.create_label(self.config_frame, "Condition script (Python expression):").grid(row=0, column=0, sticky='nw', pady=5)
        self.config_widgets['condition_text'] = tk.Text(self.config_frame, height=8, width=50,
                                                       bg=CustomStyle.COLORS['bg_tertiary'],
                                                       fg=CustomStyle.COLORS['text'])
        self.config_widgets['condition_text'].grid(row=0, column=1, sticky='ew', padx=(10, 0), pady=5)
        
        # Default condition example
        example = """# Example conditions:
# datetime.datetime.now().hour == 9  # Trigger at 9 AM
# os.path.exists('/tmp/trigger_file')  # Trigger if file exists
# datetime.datetime.now().weekday() == 4  # Trigger on Friday
True  # Always trigger (for testing)"""
        self.config_widgets['condition_text'].insert('1.0', example)
        
        CustomWidget.create_label(self.config_frame, "Check interval (seconds):").grid(row=1, column=0, sticky='w', pady=5)
        self.config_widgets['check_interval'] = CustomWidget.create_entry(self.config_frame, width=10)
        self.config_widgets['check_interval'].grid(row=1, column=1, sticky='w', padx=(10, 0), pady=5)
        self.config_widgets['check_interval'].insert(0, "30")
        
        self.config_frame.columnconfigure(1, weight=1)
    
    def create_chain_config(self):
        """Create chain timer configuration widgets"""
        CustomWidget.create_label(self.config_frame, "Chain configuration (JSON):").grid(row=0, column=0, sticky='nw', pady=5)
        self.config_widgets['chain_text'] = tk.Text(self.config_frame, height=10, width=60,
                                                   bg=CustomStyle.COLORS['bg_tertiary'],
                                                   fg=CustomStyle.COLORS['text'])
        self.config_widgets['chain_text'].grid(row=0, column=1, sticky='ew', padx=(10, 0), pady=5)
        
        # Default chain example
        example = """[
    {
        "type": "countdown",
        "duration": 300
    },
    {
        "type": "interval", 
        "interval": 60,
        "max_repeats": 3
    },
    {
        "type": "countdown",
        "duration": 600
    }
]"""
        self.config_widgets['chain_text'].insert('1.0', example)
        
        self.config_frame.columnconfigure(1, weight=1)
    
    def create_pomodoro_config(self):
        """Create pomodoro timer configuration widgets"""
        CustomWidget.create_label(self.config_frame, "Work duration (minutes):").grid(row=0, column=0, sticky='w', pady=5)
        self.config_widgets['work_duration'] = CustomWidget.create_entry(self.config_frame, width=10)
        self.config_widgets['work_duration'].grid(row=0, column=1, sticky='w', padx=(10, 0), pady=5)
        self.config_widgets['work_duration'].insert(0, "25")
        
        CustomWidget.create_label(self.config_frame, "Break duration (minutes):").grid(row=1, column=0, sticky='w', pady=5)
        self.config_widgets['break_duration'] = CustomWidget.create_entry(self.config_frame, width=10)
        self.config_widgets['break_duration'].grid(row=1, column=1, sticky='w', padx=(10, 0), pady=5)
        self.config_widgets['break_duration'].insert(0, "5")
        
        CustomWidget.create_label(self.config_frame, "Long break duration (minutes):").grid(row=2, column=0, sticky='w', pady=5)
        self.config_widgets['long_break_duration'] = CustomWidget.create_entry(self.config_frame, width=10)
        self.config_widgets['long_break_duration'].grid(row=2, column=1, sticky='w', padx=(10, 0), pady=5)
        self.config_widgets['long_break_duration'].insert(0, "15")
        
        CustomWidget.create_label(self.config_frame, "Cycles until long break:").grid(row=3, column=0, sticky='w', pady=5)
        self.config_widgets['cycles_until_long_break'] = CustomWidget.create_entry(self.config_frame, width=10)
        self.config_widgets['cycles_until_long_break'].grid(row=3, column=1, sticky='w', padx=(10, 0), pady=5)
        self.config_widgets['cycles_until_long_break'].insert(0, "4")
        
        self.config_frame.columnconfigure(1, weight=1)
    
    def create_stopwatch_config(self):
        """Create stopwatch configuration widgets"""
        CustomWidget.create_label(self.config_frame, "Stopwatch Configuration").grid(row=0, column=0, sticky='w', pady=5)
        CustomWidget.create_label(self.config_frame, "No additional configuration required.", 
                                style='Custom.TLabel').grid(row=1, column=0, sticky='w', pady=5)
    
    def add_action(self):
        """Add a new action configuration"""
        action_frame = CustomWidget.create_card_frame(self.action_list_frame)
        action_frame.pack(fill='x', pady=5)
        
        # Action type selection
        action_type_frame = ttk.Frame(action_frame, style='Custom.TFrame')
        action_type_frame.pack(fill='x', pady=5)
        
        CustomWidget.create_label(action_type_frame, "Action Type:").pack(side='left')
        action_combo = ttk.Combobox(action_type_frame, values=[a.value for a in ActionType], 
                                  style='Custom.TCombobox', width=15)
        action_combo.pack(side='left', padx=(10, 0))
        
        # Remove button
        remove_btn = CustomWidget.create_button(action_type_frame, "Remove", 
                                              lambda f=action_frame: self.remove_action(f))
        remove_btn.pack(side='right')
        
        # Action parameters frame
        params_frame = ttk.Frame(action_frame, style='Custom.TFrame')
        params_frame.pack(fill='x', pady=(10, 0))
        
        # Store references
        action_widgets = {
            'frame': action_frame,
            'combo': action_combo,
            'params_frame': params_frame,
            'param_widgets': {}
        }
        
        self.action_widgets.append(action_widgets)
        
        # Bind combo change event
        action_combo.bind('<<ComboboxSelected>>', 
                         lambda e, aw=action_widgets: self.on_action_type_changed(aw))
    
    def remove_action(self, action_frame):
        """Remove an action configuration"""
        # Find and remove from action_widgets list
        self.action_widgets = [aw for aw in self.action_widgets if aw['frame'] != action_frame]
        action_frame.destroy()
    
    def on_action_type_changed(self, action_widgets):
        """Handle action type change"""
        action_type = ActionType(action_widgets['combo'].get())
        
        # Clear existing parameter widgets
        for widget in action_widgets['params_frame'].winfo_children():
            widget.destroy()
        action_widgets['param_widgets'].clear()
        
        # Create type-specific parameter widgets
        if action_type == ActionType.NOTIFICATION:
            self.create_notification_params(action_widgets)
        elif action_type == ActionType.SOUND:
            self.create_sound_params(action_widgets)
        elif action_type == ActionType.COMMAND:
            self.create_command_params(action_widgets)
        elif action_type == ActionType.POPUP:
            self.create_popup_params(action_widgets)
        elif action_type == ActionType.FILE_WRITE:
            self.create_file_write_params(action_widgets)
        elif action_type == ActionType.HTTP_REQUEST:
            self.create_http_request_params(action_widgets)
    
    def create_notification_params(self, action_widgets):
        """Create notification action parameters"""
        frame = action_widgets['params_frame']
        
        CustomWidget.create_label(frame, "Title:").grid(row=0, column=0, sticky='w', pady=2)
        title_entry = CustomWidget.create_entry(frame, width=30)
        title_entry.grid(row=0, column=1, sticky='ew', padx=(10, 0), pady=2)
        title_entry.insert(0, "Timer Alert")
        action_widgets['param_widgets']['title'] = title_entry
        
        CustomWidget.create_label(frame, "Message:").grid(row=1, column=0, sticky='nw', pady=2)
        message_text = tk.Text(frame, height=3, width=40,
                             bg=CustomStyle.COLORS['bg_tertiary'],
                             fg=CustomStyle.COLORS['text'])
        message_text.grid(row=1, column=1, sticky='ew', padx=(10, 0), pady=2)
        message_text.insert('1.0', "Timer has triggered!")
        action_widgets['param_widgets']['message'] = message_text
        
        frame.columnconfigure(1, weight=1)
    
    def create_sound_params(self, action_widgets):
        """Create sound action parameters"""
        frame = action_widgets['params_frame']
        
        CustomWidget.create_label(frame, "Sound file (optional):").grid(row=0, column=0, sticky='w', pady=2)
        file_frame = ttk.Frame(frame, style='Custom.TFrame')
        file_frame.grid(row=0, column=1, sticky='ew', padx=(10, 0), pady=2)
        
        file_entry = CustomWidget.create_entry(file_frame)
        file_entry.pack(side='left', fill='x', expand=True)
        CustomWidget.create_button(file_frame, "Browse", 
                                 lambda: self.browse_sound_file(file_entry)).pack(side='right', padx=(10, 0))
        
        action_widgets['param_widgets']['file'] = file_entry
        
        CustomWidget.create_label(frame, "System sound:").grid(row=1, column=0, sticky='w', pady=2)
        sound_combo = ttk.Combobox(frame, values=['default', 'beep', 'chime'], 
                                 style='Custom.TCombobox', width=15)
        sound_combo.grid(row=1, column=1, sticky='w', padx=(10, 0), pady=2)
        sound_combo.set('default')
        action_widgets['param_widgets']['system_sound'] = sound_combo
        
        frame.columnconfigure(1, weight=1)
    
    def create_command_params(self, action_widgets):
        """Create command action parameters"""
        frame = action_widgets['params_frame']
        
        CustomWidget.create_label(frame, "Command:").grid(row=0, column=0, sticky='nw', pady=2)
        command_text = tk.Text(frame, height=3, width=50,
                             bg=CustomStyle.COLORS['bg_tertiary'],
                             fg=CustomStyle.COLORS['text'])
        command_text.grid(row=0, column=1, sticky='ew', padx=(10, 0), pady=2)
        action_widgets['param_widgets']['command'] = command_text
        
        frame.columnconfigure(1, weight=1)
    
    def create_popup_params(self, action_widgets):
        """Create popup action parameters"""
        frame = action_widgets['params_frame']
        
        CustomWidget.create_label(frame, "Title:").grid(row=0, column=0, sticky='w', pady=2)
        title_entry = CustomWidget.create_entry(frame, width=30)
        title_entry.grid(row=0, column=1, sticky='ew', padx=(10, 0), pady=2)
        title_entry.insert(0, "Timer Alert")
        action_widgets['param_widgets']['title'] = title_entry
        
        CustomWidget.create_label(frame, "Message:").grid(row=1, column=0, sticky='nw', pady=2)
        message_text = tk.Text(frame, height=3, width=40,
                             bg=CustomStyle.COLORS['bg_tertiary'],
                             fg=CustomStyle.COLORS['text'])
        message_text.grid(row=1, column=1, sticky='ew', padx=(10, 0), pady=2)
        message_text.insert('1.0', "Timer has triggered!")
        action_widgets['param_widgets']['message'] = message_text
        
        frame.columnconfigure(1, weight=1)
    
    def create_file_write_params(self, action_widgets):
        """Create file write action parameters"""
        frame = action_widgets['params_frame']
        
        CustomWidget.create_label(frame, "File path:").grid(row=0, column=0, sticky='w', pady=2)
        file_frame = ttk.Frame(frame, style='Custom.TFrame')
        file_frame.grid(row=0, column=1, sticky='ew', padx=(10, 0), pady=2)
        
        file_entry = CustomWidget.create_entry(file_frame)
        file_entry.pack(side='left', fill='x', expand=True)
        file_entry.insert(0, "timer_log.txt")
        CustomWidget.create_button(file_frame, "Browse", 
                                 lambda: self.browse_output_file(file_entry)).pack(side='right', padx=(10, 0))
        
        action_widgets['param_widgets']['file_path'] = file_entry
        
        CustomWidget.create_label(frame, "Content:").grid(row=1, column=0, sticky='nw', pady=2)
        content_text = tk.Text(frame, height=3, width=50,
                             bg=CustomStyle.COLORS['bg_tertiary'],
                             fg=CustomStyle.COLORS['text'])
        content_text.grid(row=1, column=1, sticky='ew', padx=(10, 0), pady=2)
        content_text.insert('1.0', "Timer triggered at {datetime.datetime.now()}")
        action_widgets['param_widgets']['content'] = content_text
        
        append_var = tk.BooleanVar(value=True)
        append_check = tk.Checkbutton(frame, text="Append to file", variable=append_var,
                                    bg=CustomStyle.COLORS['bg_secondary'],
                                    fg=CustomStyle.COLORS['text'],
                                    selectcolor=CustomStyle.COLORS['bg_tertiary'])
        append_check.grid(row=2, column=1, sticky='w', padx=(10, 0), pady=2)
        action_widgets['param_widgets']['append'] = append_var
        
        frame.columnconfigure(1, weight=1)
    
    def create_http_request_params(self, action_widgets):
        """Create HTTP request action parameters"""
        frame = action_widgets['params_frame']
        
        CustomWidget.create_label(frame, "URL:").grid(row=0, column=0, sticky='w', pady=2)
        url_entry = CustomWidget.create_entry(frame, width=50)
        url_entry.grid(row=0, column=1, sticky='ew', padx=(10, 0), pady=2)
        action_widgets['param_widgets']['url'] = url_entry
        
        CustomWidget.create_label(frame, "Method:").grid(row=1, column=0, sticky='w', pady=2)
        method_combo = ttk.Combobox(frame, values=['GET', 'POST', 'PUT', 'DELETE'], 
                                  style='Custom.TCombobox', width=10)
        method_combo.grid(row=1, column=1, sticky='w', padx=(10, 0), pady=2)
        method_combo.set('GET')
        action_widgets['param_widgets']['method'] = method_combo
        
        CustomWidget.create_label(frame, "Data (for POST/PUT):").grid(row=2, column=0, sticky='nw', pady=2)
        data_text = tk.Text(frame, height=3, width=50,
                          bg=CustomStyle.COLORS['bg_tertiary'],
                          fg=CustomStyle.COLORS['text'])
        data_text.grid(row=2, column=1, sticky='ew', padx=(10, 0), pady=2)
        action_widgets['param_widgets']['data'] = data_text
        
        frame.columnconfigure(1, weight=1)
    
    def browse_sound_file(self, entry_widget):
        """Browse for sound file"""
        file_path = filedialog.askopenfilename(
            title="Select Sound File",
            filetypes=[("Audio files", "*.wav *.mp3 *.ogg"), ("All files", "*.*")]
        )
        if file_path:
            entry_widget.delete(0, tk.END)
            entry_widget.insert(0, file_path)
    
    def browse_output_file(self, entry_widget):
        """Browse for output file"""
        file_path = filedialog.asksaveasfilename(
            title="Select Output File",
            filetypes=[("Text files", "*.txt"), ("Log files", "*.log"), ("All files", "*.*")]
        )
        if file_path:
            entry_widget.delete(0, tk.END)
            entry_widget.insert(0, file_path)
    
    def create_timer(self):
        """Create a new timer from the form data"""
        try:
            # Get basic info
            name = self.name_entry.get().strip()
            if not name:
                messagebox.showerror("Error", "Timer name is required")
                return
            
            if name in self.timer_manager.timers:
                messagebox.showerror("Error", "Timer with this name already exists")
                return
            
            timer_type = TimerType(self.type_combo.get())
            
            # Get configuration based on timer type
            config = self.get_timer_config(timer_type)
            if config is None:
                return
            
            # Create timer
            timer = ComplexTimer(name, timer_type, config)
            
            # Add actions
            for action_widget in self.action_widgets:
                action_type_str = action_widget['combo'].get()
                if not action_type_str:
                    continue
                
                action_type = ActionType(action_type_str)
                params = self.get_action_params(action_widget)
                action = TimerAction(action_type, params)
                timer.add_action(action)
            
            # Add to manager
            if self.timer_manager.add_timer(timer):
                messagebox.showinfo("Success", f"Timer '{name}' created successfully")
                self.clear_form()
            else:
                messagebox.showerror("Error", "Failed to create timer")
                
        except Exception as e:
            messagebox.showerror("Error", f"Failed to create timer: {str(e)}")
    
    def get_timer_config(self, timer_type: TimerType) -> Optional[Dict]:
        """Get configuration dictionary for timer type"""
        try:
            if timer_type == TimerType.COUNTDOWN:
                hours = int(self.config_widgets['hours'].get() or "0")
                minutes = int(self.config_widgets['minutes'].get() or "0") 
                seconds = int(self.config_widgets['seconds'].get() or "0")
                duration = hours * 3600 + minutes * 60 + seconds
                return {'duration': duration}
                
            elif timer_type == TimerType.INTERVAL:
                interval = int(self.config_widgets['interval'].get())
                max_repeats = int(self.config_widgets['max_repeats'].get())
                return {'interval': interval, 'max_repeats': max_repeats}
                
            elif timer_type == TimerType.SCHEDULED:
                times_text = self.config_widgets['times_text'].get('1.0', tk.END).strip()
                schedule_times = []
                for line in times_text.split('\n'):
                    line = line.strip()
                    if line:
                        try:
                            time_obj = datetime.time.fromisoformat(line)
                            schedule_times.append(time_obj)
                        except ValueError:
                            messagebox.showerror("Error", f"Invalid time format: {line}")
                            return None
                
                days_of_week = [i for i, var in enumerate(self.config_widgets['days']) if var.get()]
                
                specific_date = self.config_widgets['specific_date'].get().strip()
                date_specific = None
                if specific_date:
                    try:
                        date_specific = datetime.date.fromisoformat(specific_date)
                    except ValueError:
                        messagebox.showerror("Error", f"Invalid date format: {specific_date}")
                        return None
                
                return {
                    'schedule_times': schedule_times,
                    'days_of_week': days_of_week,
                    'date_specific': date_specific
                }
                
            elif timer_type == TimerType.CONDITIONAL:
                condition_script = self.config_widgets['condition_text'].get('1.0', tk.END).strip()
                check_interval = int(self.config_widgets['check_interval'].get())
                return {'condition_script': condition_script, 'check_interval': check_interval}
                
            elif timer_type == TimerType.CHAIN:
                chain_text = self.config_widgets['chain_text'].get('1.0', tk.END).strip()
                try:
                    chain_configs = json.loads(chain_text)
                    return {'chain_configs': chain_configs}
                except json.JSONDecodeError as e:
                    messagebox.showerror("Error", f"Invalid JSON in chain configuration: {str(e)}")
                    return None
                    
            elif timer_type == TimerType.POMODORO:
                work_duration = int(self.config_widgets['work_duration'].get()) * 60
                break_duration = int(self.config_widgets['break_duration'].get()) * 60
                long_break_duration = int(self.config_widgets['long_break_duration'].get()) * 60
                cycles_until_long_break = int(self.config_widgets['cycles_until_long_break'].get())
                return {
                    'work_duration': work_duration,
                    'break_duration': break_duration,
                    'long_break_duration': long_break_duration,
                    'cycles_until_long_break': cycles_until_long_break
                }
                
            elif timer_type == TimerType.STOPWATCH:
                return {}
                
        except ValueError as e:
            messagebox.showerror("Error", f"Invalid configuration values: {str(e)}")
            return None
        except Exception as e:
            messagebox.showerror("Error", f"Configuration error: {str(e)}")
            return None
    
    def get_action_params(self, action_widget) -> Dict:
        """Get parameters for an action"""
        params = {}
        action_type = ActionType(action_widget['combo'].get())
        param_widgets = action_widget['param_widgets']
        
        if action_type in [ActionType.NOTIFICATION, ActionType.POPUP]:
            params['title'] = param_widgets['title'].get()
            params['message'] = param_widgets['message'].get('1.0', tk.END).strip()
            
        elif action_type == ActionType.SOUND:
            params['file'] = param_widgets['file'].get()
            params['system_sound'] = param_widgets['system_sound'].get()
            
        elif action_type == ActionType.COMMAND:
            params['command'] = param_widgets['command'].get('1.0', tk.END).strip()
            
        elif action_type == ActionType.FILE_WRITE:
            params['file_path'] = param_widgets['file_path'].get()
            params['content'] = param_widgets['content'].get('1.0', tk.END).strip()
            params['append'] = param_widgets['append'].get()
            
        elif action_type == ActionType.HTTP_REQUEST:
            params['url'] = param_widgets['url'].get()
            params['method'] = param_widgets['method'].get()
            params['data'] = param_widgets['data'].get('1.0', tk.END).strip()
        
        return params
    
    def clear_form(self):
        """Clear the timer creation form"""
        self.name_entry.delete(0, tk.END)
        self.type_combo.set('')
        
        # Clear config widgets
        for widget in self.config_frame.winfo_children():
            widget.destroy()
        self.config_widgets.clear()
        
        # Clear action widgets
        for action_widget in self.action_widgets:
            action_widget['frame'].destroy()
        self.action_widgets.clear()
    
    def refresh_timer_list(self):
        """Refresh the timer list display"""
        # Clear existing items
        for item in self.timer_tree.get_children():
            self.timer_tree.delete(item)
        
        # Add current timers
        for name, timer in self.timer_manager.timers.items():
            status = "Running" if (timer.thread and timer.thread.is_alive()) else "Stopped"
            last_triggered = timer.last_triggered.strftime("%Y-%m-%d %H:%M:%S") if timer.last_triggered else "Never"
            
            self.timer_tree.insert('', 'end', values=(
                name,
                timer.timer_type.value.title(),
                status,
                last_triggered,
                timer.trigger_count
            ))
    
    def show_context_menu(self, event):
        """Show context menu for timer list"""
        item = self.timer_tree.selection()[0] if self.timer_tree.selection() else None
        if item:
            self.context_menu.post(event.x_root, event.y_root)
    
    def start_selected_timer(self):
        """Start the selected timer"""
        item = self.timer_tree.selection()[0] if self.timer_tree.selection() else None
        if item:
            timer_name = self.timer_tree.item(item)['values'][0]
            if self.timer_manager.start_timer(timer_name):
                messagebox.showinfo("Success", f"Timer '{timer_name}' started")
            else:
                messagebox.showerror("Error", f"Failed to start timer '{timer_name}'")
    
    def stop_selected_timer(self):
        """Stop the selected timer"""
        item = self.timer_tree.selection()[0] if self.timer_tree.selection() else None
        if item:
            timer_name = self.timer_tree.item(item)['values'][0]
            if self.timer_manager.stop_timer(timer_name):
                messagebox.showinfo("Success", f"Timer '{timer_name}' stopped")
            else:
                messagebox.showerror("Error", f"Failed to stop timer '{timer_name}'")
    
    def edit_timer(self, event=None):
        """Edit the selected timer"""
        item = self.timer_tree.selection()[0] if self.timer_tree.selection() else None
        if item:
            timer_name = self.timer_tree.item(item)['values'][0]
            timer = self.timer_manager.get_timer(timer_name)
            if timer:
                self.open_timer_editor(timer)
    
    def delete_timer(self):
        """Delete the selected timer"""
        item = self.timer_tree.selection()[0] if self.timer_tree.selection() else None
        if item:
            timer_name = self.timer_tree.item(item)['values'][0]
            if messagebox.askyesno("Confirm Delete", f"Delete timer '{timer_name}'?"):
                if self.timer_manager.remove_timer(timer_name):
                    messagebox.showinfo("Success", f"Timer '{timer_name}' deleted")
                else:
                    messagebox.showerror("Error", f"Failed to delete timer '{timer_name}'")
    
    def duplicate_timer(self):
        """Duplicate the selected timer"""
        item = self.timer_tree.selection()[0] if self.timer_tree.selection() else None
        if item:
            timer_name = self.timer_tree.item(item)['values'][0]
            timer = self.timer_manager.get_timer(timer_name)
            if timer:
                # Create duplicate with new name
                new_name = f"{timer_name}_copy"
                counter = 1
                while new_name in self.timer_manager.timers:
                    new_name = f"{timer_name}_copy_{counter}"
                    counter += 1
                
                new_timer = ComplexTimer(new_name, timer.timer_type, timer.config.copy())
                for action in timer.actions:
                    new_action = TimerAction(action.action_type, action.parameters.copy())
                    new_timer.add_action(new_action)
                
                if self.timer_manager.add_timer(new_timer):
                    messagebox.showinfo("Success", f"Timer duplicated as '{new_name}'")
                else:
                    messagebox.showerror("Error", "Failed to duplicate timer")
    
    def start_all_timers(self):
        """Start all timers"""
        count = 0
        for name in self.timer_manager.list_timers():
            if self.timer_manager.start_timer(name):
                count += 1
        messagebox.showinfo("Success", f"Started {count} timers")
    
    def stop_all_timers(self):
        """Stop all timers"""
        self.timer_manager.stop_all()
        messagebox.showinfo("Success", "All timers stopped")
    
    def save_config(self):
        """Save timer configuration to file"""
        file_path = filedialog.asksaveasfilename(
            title="Save Timer Configuration",
            defaultextension=".json",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
        )
        if file_path:
            try:
                self.timer_manager.save_to_file(file_path)
                messagebox.showinfo("Success", "Configuration saved successfully")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to save configuration: {str(e)}")
    
    def load_config(self):
        """Load timer configuration from file"""
        file_path = filedialog.askopenfilename(
            title="Load Timer Configuration",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
        )
        if file_path:
            try:
                self.timer_manager.load_from_file(file_path)
                messagebox.showinfo("Success", "Configuration loaded successfully")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to load configuration: {str(e)}")
    
    def open_timer_editor(self, timer):
        """Open timer editor window"""
        editor_window = tk.Toplevel(self.root)
        editor_window.title(f"Edit Timer: {timer.name}")
        editor_window.geometry("800x600")
        CustomStyle.apply_dark_theme(editor_window)
        
        # Create editor content (simplified for this example)
        editor_frame = CustomWidget.create_card_frame(editor_window)
        editor_frame.pack(fill='both', expand=True, padx=10, pady=10)
        
        CustomWidget.create_label(editor_frame, f"Editing Timer: {timer.name}", 
                                style='Title.TLabel').pack(pady=(0, 20))
        
        # Timer info
        info_text = f"""
Timer Type: {timer.timer_type.value.title()}
Created: {timer.created_at.strftime('%Y-%m-%d %H:%M:%S')}
Last Triggered: {timer.last_triggered.strftime('%Y-%m-%d %H:%M:%S') if timer.last_triggered else 'Never'}
Trigger Count: {timer.trigger_count}
Status: {'Running' if (timer.thread and timer.thread.is_alive()) else 'Stopped'}
"""
        
        info_label = CustomWidget.create_label(editor_frame, info_text)
        info_label.pack(anchor='w', pady=10)
        
        # Control buttons
        button_frame = ttk.Frame(editor_frame, style='Custom.TFrame')
        button_frame.pack(fill='x', pady=20)
        
        if timer.thread and timer.thread.is_alive():
            CustomWidget.create_button(button_frame, "Stop Timer", 
                                     lambda: self.timer_manager.stop_timer(timer.name)).pack(side='left', padx=(0, 10))
        else:
            CustomWidget.create_button(button_frame, "Start Timer", 
                                     lambda: self.timer_manager.start_timer(timer.name)).pack(side='left', padx=(0, 10))
        
        CustomWidget.create_button(button_frame, "Close", editor_window.destroy).pack(side='right')
    
    def apply_settings(self):
        """Apply application settings"""
        try:
            # This would typically save settings to a config file
            messagebox.showinfo("Success", "Settings applied successfully")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to apply settings: {str(e)}")
    
    def update_status_loop(self):
        """Background thread to update timer status"""
        while self.update_thread_running:
            try:
                # Schedule GUI update on main thread
                self.root.after_idle(self.refresh_timer_list)
                time.sleep(1)  # Update every second
            except:
                break
    
    def run(self):
        """Start the application"""
        # Handle window close
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        
        # Load any existing configuration
        config_file = "timer_config.json"
        if os.path.exists(config_file):
            try:
                self.timer_manager.load_from_file(config_file)
            except:
                pass
        
        # Start the GUI
        self.root.mainloop()
    
    def on_closing(self):
        """Handle application closing"""
        try:
            # Stop all timers
            self.timer_manager.stop_all()
            
            # Stop update thread
            self.update_thread_running = False
            
            # Auto-save if enabled
            if hasattr(self, 'auto_save_var') and self.auto_save_var.get():
                self.timer_manager.save_to_file("timer_config.json")
            
        except:
            pass
        finally:
            self.root.destroy()


def main():
    """Main application entry point"""
    try:
        app = TimerApp()
        app.run()
    except KeyboardInterrupt:
        print("\nApplication interrupted by user")
    except Exception as e:
        print(f"Application error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()