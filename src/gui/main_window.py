import tkinter as tk
from tkinter import ttk, scrolledtext, filedialog, messagebox
import threading
import time
from datetime import datetime
import os
from typing import Optional
import sys
import json

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from components.automation_engine import AutomationEngine
from components.logger import logger


class WafidAutomationGUI:
    """Main GUI window for the Wafid automation tool"""
    
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Wafid Medical Appointment Automation Tool")
        self.root.geometry("1000x700")
        self.root.minsize(800, 600)
        
        # Initialize automation engine
        self.automation_engine = AutomationEngine()
        
        # GUI state
        self.is_automation_running = False
        self.csv_file_path = ""
        self.target_center = ""
        
        # Setup GUI components
        self.setup_styles()
        self.create_widgets()
        self.setup_logger_callback()
        self.update_status_loop()
        
        # Center window on screen
        self.center_window()
    
    def setup_styles(self):
        """Configure ttk styles"""
        style = ttk.Style()
        style.theme_use('clam')
        
        # Configure custom styles
        style.configure('Title.TLabel', font=('Arial', 14, 'bold'))
        style.configure('Header.TLabel', font=('Arial', 10, 'bold'))
        style.configure('Success.TButton', background='#4CAF50')
        style.configure('Warning.TButton', background='#FF9800')
        style.configure('Error.TButton', background='#F44336')
    
    def create_widgets(self):
        """Create and layout GUI widgets"""
        # Main title
        title_label = ttk.Label(
            self.root, 
            text="Wafid Medical Appointment Automation Tool",
            style='Title.TLabel'
        )
        title_label.pack(pady=(10, 20))
        
        # Create main container with notebook
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill='both', expand=True, padx=10, pady=(0, 10))
        
        # Configuration tab
        self.config_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.config_frame, text="Configuration")
        self.create_config_tab()
        
        # Console tab
        self.console_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.console_frame, text="Live Console")
        self.create_console_tab()
        
        # Statistics tab
        self.stats_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.stats_frame, text="Statistics")
        self.create_stats_tab()
        
        # Results tab
        self.results_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.results_frame, text="Results")
        self.create_results_tab()
    
    def create_config_tab(self):
        """Create configuration tab"""
        # Target Medical Center
        center_frame = ttk.LabelFrame(self.config_frame, text="Target Medical Center", padding=10)
        center_frame.pack(fill='x', padx=10, pady=5)
        
        ttk.Label(center_frame, text="Medical Center Name:").pack(anchor='w')
        self.center_entry = ttk.Entry(center_frame, width=50)
        self.center_entry.pack(fill='x', pady=(5, 0))
        
        ttk.Button(
            center_frame, 
            text="Set Target Center",
            command=self.set_target_center
        ).pack(pady=(10, 0))
        
        # CSV File Selection
        csv_frame = ttk.LabelFrame(self.config_frame, text="Candidate Data", padding=10)
        csv_frame.pack(fill='x', padx=10, pady=5)
        
        ttk.Label(csv_frame, text="CSV File:").pack(anchor='w')
        csv_input_frame = ttk.Frame(csv_frame)
        csv_input_frame.pack(fill='x', pady=(5, 0))
        
        self.csv_path_var = tk.StringVar()
        ttk.Entry(csv_input_frame, textvariable=self.csv_path_var, state='readonly').pack(side='left', fill='x', expand=True)
        ttk.Button(csv_input_frame, text="Browse", command=self.browse_csv_file).pack(side='right', padx=(5, 0))
        
        ttk.Button(
            csv_frame, 
            text="Load Candidate Data",
            command=self.load_candidate_data
        ).pack(pady=(10, 0))
        
        # Current Status
        status_frame = ttk.LabelFrame(self.config_frame, text="Current Status", padding=10)
        status_frame.pack(fill='x', padx=10, pady=5)
        
        self.status_text = tk.Text(status_frame, height=6, wrap=tk.WORD, state='disabled')
        self.status_text.pack(fill='both', expand=True)
        
        # Control Buttons
        control_frame = ttk.Frame(self.config_frame)
        control_frame.pack(fill='x', padx=10, pady=20)
        
        self.start_button = ttk.Button(
            control_frame, 
            text="Start Automation",
            command=self.start_automation,
            style='Success.TButton'
        )
        self.start_button.pack(side='left', padx=(0, 10))
        
        self.stop_button = ttk.Button(
            control_frame, 
            text="Stop Automation",
            command=self.stop_automation,
            style='Error.TButton',
            state='disabled'
        )
        self.stop_button.pack(side='left', padx=(0, 10))
        
        ttk.Button(
            control_frame, 
            text="Refresh Proxies",
            command=self.refresh_proxies
        ).pack(side='left', padx=(0, 10))
        
        ttk.Button(
            control_frame, 
            text="Clear Logs",
            command=self.clear_logs
        ).pack(side='left')
    
    def create_console_tab(self):
        """Create live console tab"""
        console_frame = ttk.LabelFrame(self.console_frame, text="Real-time Logs", padding=10)
        console_frame.pack(fill='both', expand=True, padx=10, pady=5)
        
        # Console text widget with scrollbar
        self.console_text = scrolledtext.ScrolledText(
            console_frame,
            wrap=tk.WORD,
            state='disabled',
            font=('Consolas', 9)
        )
        self.console_text.pack(fill='both', expand=True)
        
        # Console controls
        console_controls = ttk.Frame(console_frame)
        console_controls.pack(fill='x', pady=(10, 0))
        
        ttk.Button(
            console_controls,
            text="Export Logs (CSV)",
            command=self.export_logs_csv
        ).pack(side='left', padx=(0, 10))
        
        ttk.Button(
            console_controls,
            text="Export Network Logs (JSON)",
            command=self.export_network_logs
        ).pack(side='left')
        
        ttk.Button(
            console_controls,
            text="Auto-scroll",
            command=self.toggle_auto_scroll
        ).pack(side='right')
        
        self.auto_scroll = True
    
    def create_stats_tab(self):
        """Create statistics tab"""
        stats_main_frame = ttk.LabelFrame(self.stats_frame, text="Automation Statistics", padding=10)
        stats_main_frame.pack(fill='both', expand=True, padx=10, pady=5)
        
        # Statistics display
        self.stats_text = tk.Text(stats_main_frame, height=20, wrap=tk.WORD, state='disabled')
        self.stats_text.pack(fill='both', expand=True)
        
        # Stats control buttons
        stats_controls = ttk.Frame(stats_main_frame)
        stats_controls.pack(fill='x', pady=(10, 0))
        
        ttk.Button(
            stats_controls,
            text="Refresh Stats",
            command=self.update_statistics
        ).pack(side='left', padx=(0, 10))
        
        ttk.Button(
            stats_controls,
            text="Reset Stats",
            command=self.reset_statistics
        ).pack(side='left')
    
    def create_results_tab(self):
        """Create results tab"""
        results_main_frame = ttk.LabelFrame(self.results_frame, text="Payment URLs", padding=10)
        results_main_frame.pack(fill='both', expand=True, padx=10, pady=5)
        
        # Results table
        columns = ('Timestamp', 'Candidate', 'Email', 'Country', 'City', 'Payment URL')
        self.results_tree = ttk.Treeview(results_main_frame, columns=columns, show='headings', height=15)
        
        for col in columns:
            self.results_tree.heading(col, text=col)
            if col == 'Payment URL':
                self.results_tree.column(col, width=300)
            else:
                self.results_tree.column(col, width=120)
        
        # Scrollbar for results
        results_scrollbar = ttk.Scrollbar(results_main_frame, orient='vertical', command=self.results_tree.yview)
        self.results_tree.configure(yscrollcommand=results_scrollbar.set)
        
        self.results_tree.pack(side='left', fill='both', expand=True)
        results_scrollbar.pack(side='right', fill='y')
        
        # Results controls
        results_controls = ttk.Frame(results_main_frame)
        results_controls.pack(fill='x', pady=(10, 0))
        
        ttk.Button(
            results_controls,
            text="Refresh Results",
            command=self.refresh_results
        ).pack(side='left', padx=(0, 10))
        
        ttk.Button(
            results_controls,
            text="Export Results",
            command=self.export_results
        ).pack(side='left')
    
    def setup_logger_callback(self):
        """Setup logger callback for real-time console updates"""
        logger.set_gui_callback(self.add_console_message)
    
    def center_window(self):
        """Center the window on the screen"""
        self.root.update_idletasks()
        width = self.root.winfo_width()
        height = self.root.winfo_height()
        x = (self.root.winfo_screenwidth() // 2) - (width // 2)
        y = (self.root.winfo_screenheight() // 2) - (height // 2)
        self.root.geometry(f'{width}x{height}+{x}+{y}')
    
    def add_console_message(self, message: str):
        """Add message to console (thread-safe)"""
        def update_console():
            self.console_text.configure(state='normal')
            self.console_text.insert(tk.END, message + '\n')
            self.console_text.configure(state='disabled')
            
            if self.auto_scroll:
                self.console_text.see(tk.END)
        
        # Schedule update in main thread
        self.root.after(0, update_console)
    
    def update_status(self, message: str):
        """Update status text"""
        def update():
            self.status_text.configure(state='normal')
            self.status_text.delete(1.0, tk.END)
            self.status_text.insert(1.0, message)
            self.status_text.configure(state='disabled')
        
        self.root.after(0, update)
    
    def set_target_center(self):
        """Set target medical center"""
        center_name = self.center_entry.get().strip()
        if not center_name:
            messagebox.showerror("Error", "Please enter a medical center name")
            return
        
        self.target_center = center_name
        self.automation_engine.set_target_medical_center(center_name)
        messagebox.showinfo("Success", f"Target medical center set: {center_name}")
        self.update_status_display()
    
    def browse_csv_file(self):
        """Browse for CSV file"""
        filename = filedialog.askopenfilename(
            title="Select CSV File",
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")]
        )
        
        if filename:
            self.csv_file_path = filename
            self.csv_path_var.set(filename)
    
    def load_candidate_data(self):
        """Load candidate data from CSV"""
        if not self.csv_file_path:
            messagebox.showerror("Error", "Please select a CSV file first")
            return
        
        if self.automation_engine.load_candidate_data(self.csv_file_path):
            messagebox.showinfo("Success", "Candidate data loaded successfully")
            self.update_status_display()
        else:
            messagebox.showerror("Error", "Failed to load candidate data")
    
    def start_automation(self):
        """Start automation in separate thread"""
        if not self.target_center:
            messagebox.showerror("Error", "Please set target medical center first")
            return
        
        if not self.automation_engine.form_handler.candidate_data:
            messagebox.showerror("Error", "Please load candidate data first")
            return
        
        self.is_automation_running = True
        self.start_button.configure(state='disabled')
        self.stop_button.configure(state='normal')
        
        # Setup callbacks
        self.automation_engine.set_callbacks(
            success_callback=self.on_automation_success,
            status_callback=self.update_status
        )
        
        # Start automation in separate thread
        automation_thread = threading.Thread(
            target=self.run_automation,
            daemon=True
        )
        automation_thread.start()
    
    def run_automation(self):
        """Run automation (called in separate thread)"""
        try:
            success = self.automation_engine.start_automation()
            
            def finish():
                self.is_automation_running = False
                self.start_button.configure(state='normal')
                self.stop_button.configure(state='disabled')
                
                if success:
                    messagebox.showinfo("Success", "Automation completed successfully!")
                    self.refresh_results()
            
            self.root.after(0, finish)
            
        except Exception as e:
            def error():
                self.is_automation_running = False
                self.start_button.configure(state='normal')
                self.stop_button.configure(state='disabled')
                messagebox.showerror("Error", f"Automation failed: {e}")
            
            self.root.after(0, error)
    
    def stop_automation(self):
        """Stop automation"""
        self.automation_engine.stop_automation()
        self.is_automation_running = False
        self.start_button.configure(state='normal')
        self.stop_button.configure(state='disabled')
    
    def on_automation_success(self):
        """Called when automation succeeds"""
        def success_update():
            messagebox.showinfo("Success", "Match found and booking completed!")
            self.refresh_results()
        
        self.root.after(0, success_update)
    
    def refresh_proxies(self):
        """Refresh proxy list"""
        def refresh():
            self.automation_engine.proxy_manager.refresh_proxy_list()
            messagebox.showinfo("Success", "Proxy list refreshed")
        
        threading.Thread(target=refresh, daemon=True).start()
    
    def clear_logs(self):
        """Clear all logs"""
        logger.clear_logs()
        self.console_text.configure(state='normal')
        self.console_text.delete(1.0, tk.END)
        self.console_text.configure(state='disabled')
        messagebox.showinfo("Success", "Logs cleared")
    
    def toggle_auto_scroll(self):
        """Toggle auto-scroll for console"""
        self.auto_scroll = not self.auto_scroll
    
    def update_status_loop(self):
        """Update status periodically"""
        if hasattr(self, 'automation_engine'):
            self.update_status_display()
            self.update_statistics()
        
        # Schedule next update
        self.root.after(5000, self.update_status_loop)  # Update every 5 seconds
    
    def update_status_display(self):
        """Update the status display"""
        try:
            stats = self.automation_engine.get_statistics()
            
            status_text = f"Target Medical Center: {self.target_center or 'Not set'}\n"
            status_text += f"CSV File: {os.path.basename(self.csv_file_path) if self.csv_file_path else 'Not loaded'}\n"
            status_text += f"Candidate: {stats.get('candidate_summary', 'None')}\n"
            status_text += f"Automation Status: {'Running' if self.is_automation_running else 'Stopped'}\n"
            status_text += f"Working Proxies: {stats.get('total_working', 0)}\n"
            status_text += f"Current Attempt: {stats.get('current_attempt', 0)}/{stats.get('max_retries', 0)}"
            
            self.status_text.configure(state='normal')
            self.status_text.delete(1.0, tk.END)
            self.status_text.insert(1.0, status_text)
            self.status_text.configure(state='disabled')
            
        except Exception as e:
            print(f"Error updating status: {e}")
    
    def update_statistics(self):
        """Update statistics display"""
        try:
            stats = self.automation_engine.get_statistics()
            
            stats_text = "=== AUTOMATION STATISTICS ===\n\n"
            stats_text += f"Target Medical Center: {stats.get('target_center', 'Not set')}\n"
            stats_text += f"Candidate: {stats.get('candidate_summary', 'None')}\n\n"
            
            stats_text += "=== ATTEMPT STATISTICS ===\n"
            stats_text += f"Total Attempts: {stats.get('attempts', 0)}\n"
            stats_text += f"Current Attempt: {stats.get('current_attempt', 0)}\n"
            stats_text += f"Max Retries: {stats.get('max_retries', 0)}\n"
            stats_text += f"Matches Found: {stats.get('matches_found', 0)}\n"
            stats_text += f"Runtime: {stats.get('total_time', 0):.2f} seconds\n\n"
            
            stats_text += "=== PROXY STATISTICS ===\n"
            stats_text += f"Total Working Proxies: {stats.get('total_working', 0)}\n"
            stats_text += f"Proxies Used: {stats.get('proxies_used', 0)}\n"
            stats_text += f"Available Proxies: {stats.get('available_count', 0)}\n"
            stats_text += f"Current Proxy: {stats.get('current_proxy', 'None')}\n\n"
            
            stats_text += "=== STATUS ===\n"
            stats_text += f"Automation Running: {stats.get('is_running', False)}\n"
            stats_text += f"Last Updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
            
            self.stats_text.configure(state='normal')
            self.stats_text.delete(1.0, tk.END)
            self.stats_text.insert(1.0, stats_text)
            self.stats_text.configure(state='disabled')
            
        except Exception as e:
            print(f"Error updating statistics: {e}")
    
    def reset_statistics(self):
        """Reset statistics"""
        self.automation_engine.reset_statistics()
        self.update_statistics()
        messagebox.showinfo("Success", "Statistics reset")
    
    def refresh_results(self):
        """Refresh results table"""
        try:
            # Clear existing items
            for item in self.results_tree.get_children():
                self.results_tree.delete(item)
            
            # Load payment URLs CSV if it exists
            csv_file = "data/payment_urls.csv"
            if os.path.exists(csv_file):
                import pandas as pd
                df = pd.read_csv(csv_file)
                
                for _, row in df.iterrows():
                    self.results_tree.insert('', 'end', values=(
                        row.get('timestamp', ''),
                        row.get('candidate_name', ''),
                        row.get('email', ''),
                        row.get('country', ''),
                        row.get('city', ''),
                        row.get('payment_url', '')
                    ))
            
        except Exception as e:
            print(f"Error refreshing results: {e}")
    
    def export_results(self):
        """Export results to CSV"""
        try:
            filename = filedialog.asksaveasfilename(
                title="Export Results",
                defaultextension=".csv",
                filetypes=[("CSV files", "*.csv"), ("All files", "*.*")]
            )
            
            if filename:
                # Copy payment URLs file
                import shutil
                source_file = "data/payment_urls.csv"
                if os.path.exists(source_file):
                    shutil.copy2(source_file, filename)
                    messagebox.showinfo("Success", f"Results exported to {filename}")
                else:
                    messagebox.showwarning("Warning", "No results to export")
        
        except Exception as e:
            messagebox.showerror("Error", f"Failed to export results: {e}")
    
    def export_logs_csv(self):
        """Export logs to CSV"""
        try:
            filename = filedialog.asksaveasfilename(
                title="Export Logs (CSV)",
                defaultextension=".csv",
                filetypes=[("CSV files", "*.csv"), ("All files", "*.*")]
            )
            
            if filename:
                if logger.export_logs_csv(filename):
                    messagebox.showinfo("Success", f"Logs exported to {filename}")
                else:
                    messagebox.showerror("Error", "Failed to export logs")
        
        except Exception as e:
            messagebox.showerror("Error", f"Failed to export logs: {e}")
    
    def export_network_logs(self):
        """Export network logs to JSON"""
        try:
            filename = filedialog.asksaveasfilename(
                title="Export Network Logs (JSON)",
                defaultextension=".json",
                filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
            )
            
            if filename:
                if logger.export_network_logs_json(filename):
                    messagebox.showinfo("Success", f"Network logs exported to {filename}")
                else:
                    messagebox.showerror("Error", "Failed to export network logs")
        
        except Exception as e:
            messagebox.showerror("Error", f"Failed to export network logs: {e}")
    
    def run(self):
        """Start the GUI application"""
        self.root.mainloop()


if __name__ == "__main__":
    app = WafidAutomationGUI()
    app.run()