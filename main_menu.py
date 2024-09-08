import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import requests
import pandas as pd
import json
import os
from concurrent.futures import ThreadPoolExecutor
from itertools import cycle
from datetime import datetime as dt
import webbrowser
import threading


# Class for configuring the User-Agent
class UserAgentConfig(tk.Toplevel):
    def __init__(self, parent):
        super().__init__(parent)
        self.title("Configure User-Agent")
        self.geometry("400x200")
        self.configure(bg='#1e1e1e')
        self.parent = parent
        self.create_widgets()

    # Create the input fields and buttons
    def create_widgets(self):
        label = ttk.Label(self, text="Enter a user agent:")
        label.pack(pady=10)

        self.user_agent_entry = ttk.Entry(self, width=50)
        self.user_agent_entry.pack(pady=10)

        save_button = ttk.Button(self, text="Save", command=self.save_user_agent)
        save_button.pack(pady=10)

    # Save the User-Agent and update the configuration
    def save_user_agent(self):
        user_agent = self.user_agent_entry.get().strip()
        if user_agent:
            self.parent.save_config('user_agent', user_agent)  # Save to config.json
            messagebox.showinfo("Success", "User-Agent saved successfully.")
            self.parent.update_user_agent()
            self.destroy()  # Close the window once the User-Agent is saved
            self.parent.load_main_app()  # Load the main window
        else:
            messagebox.showwarning("Warning", "The User-Agent field cannot be empty.")


# Main window class for the app
class BrowserWindow(tk.Tk):
    def __init__(self):
        super().__init__()
        self.selected_cik = None
        self.selected_ticker = None
        self.data = pd.DataFrame()
        self.directory_path = tk.StringVar()

        # Load saved configuration
        config_data = self.load_config()
        saved_directory = config_data.get('directory', '')
        user_agent = config_data.get('user_agent', '')

        if saved_directory:
            self.directory_path.set(saved_directory)
        self.user_agent_data = {'User-Agent': user_agent} if user_agent else None

        self.thread_pool = ThreadPoolExecutor(max_workers=4)

        self.geometry('850x500')
        self.title('Mini-Terminal')
        self.iconbitmap(f'images/logo.ico')

        self.configure(bg='#1e1e1e')

        self.style = ttk.Style()
        self.style.theme_use('clam')

        # Configure styles
        self.style.configure("TMenu", background='#e67e00', foreground='#000000', font=('Arial', 10, 'bold'))
        self.style.configure("TButton", background='#d67d1e', foreground='#000000', font=('Arial', 10, 'bold'))
        self.style.configure("TLabel", font=('Arial', 12), background='#1e1e1e', foreground='#f5f5f5')
        self.style.configure("TEntry", font=('Arial', 12), fieldbackground='#2d2d2d', foreground='#f5f5f5')
        self.style.configure("Treeview", font=('Arial', 10), rowheight=25, background='#2d2d2d', foreground='#f5f5f5', fieldbackground='#2d2d2d')
        self.style.configure("Treeview.Heading", font=('Arial', 12, 'bold'), background='#242426', foreground='#f5f5f5')
        self.style.map("TButton", background=[('active', '#555555')], foreground=[('active', '#ffffff')])

        # Show User-Agent configuration if not set
        if not self.user_agent_data:
            self.withdraw()  # Hide main window until User-Agent is set
            self.open_user_agent_window(modal=True)
        else:
            self.show_loading_screen()
            self.after(100, self.load_main_app)

    # Show a loading screen while the app initializes
    def show_loading_screen(self):
        self.loading_screen = tk.Toplevel(self)
        self.loading_screen.geometry('400x300')
        self.loading_screen.configure(bg='#1e1e1e')
        self.loading_screen.overrideredirect(True)
        self.loading_screen.update_idletasks()

        width = self.loading_screen.winfo_width()
        height = self.loading_screen.winfo_height()
        x = (self.loading_screen.winfo_screenwidth() // 2) - (width // 2)
        y = (self.loading_screen.winfo_screenheight() // 2) - (height // 2)
        self.loading_screen.geometry(f'{width}x{height}+{x}+{y}')

        container = tk.Frame(self.loading_screen, bg='#1e1e1e')
        container.place(relx=0.5, rely=0.5, anchor='center')

        self.canvas = tk.Canvas(container, width=120, height=120, bg='#1e1e1e', highlightthickness=0)
        self.canvas.pack()

        self.spinner_items = [
            self.canvas.create_oval(50, 20, 70, 40, fill='#f5f5f5'),
            self.canvas.create_oval(70, 20, 90, 40, fill='#f5f5f5'),
            self.canvas.create_oval(90, 40, 110, 60, fill='#f5f5f5'),
            self.canvas.create_oval(90, 60, 110, 80, fill='#f5f5f5'),
            self.canvas.create_oval(70, 80, 90, 100, fill='#f5f5f5'),
            self.canvas.create_oval(50, 80, 70, 100, fill='#f5f5f5'),
            self.canvas.create_oval(30, 60, 50, 80, fill='#f5f5f5'),
            self.canvas.create_oval(30, 40, 50, 60, fill='#f5f5f5')
        ]

        self.spinner_items_cycle = cycle(self.spinner_items)
        self.animate_spinner()

        self.text_label = ttk.Label(container, text="Loading...", style="TLabel", background='#1e1e1e',
                                    foreground='#f5f5f5')
        self.text_label.pack(pady=20)

        self.loading_screen.transient(self)
        self.loading_screen.grab_set()

    # Animate the loading spinner
    def animate_spinner(self):
        next_item = next(self.spinner_items_cycle)
        for item in self.spinner_items:
            self.canvas.itemconfig(item, fill='#f5f5f5')
        self.canvas.itemconfig(next_item, fill='#ffcc00')
        self.loading_screen.after(100, self.animate_spinner)

    # Load company data from the SEC API
    def _load_company_data(self):
        try:
            headers = self.user_agent_data
            response = requests.get("https://www.sec.gov/files/company_tickers.json", headers=headers)
            response.raise_for_status()
            company_tickers = response.json()
            if company_tickers:
                self.data = pd.DataFrame.from_dict(company_tickers, orient='index')
                self.data['cik_str'] = self.data['cik_str'].astype(str).str.zfill(10)
            else:
                raise ValueError("No valid data received from the API.")
        except (requests.exceptions.RequestException, ValueError) as e:
            self.data = pd.DataFrame()
            self.show_user_agent_error(e)

    # Build the main GUI
    def _build_gui(self):
        menu_frame = tk.Frame(self, bg='#FF851B', height=25)
        menu_frame.pack(fill='x')

        config_button = tk.Menubutton(menu_frame, text="Configuration", bg='#FF851B', fg='#000000',
                                      font=('Arial', 10, 'bold'))
        config_button.pack(side='left', padx=2)

        options_menu = tk.Menu(config_button, tearoff=0, bg='#FF851B', fg='#000000', font=('Arial', 10, 'bold'))
        config_button.config(menu=options_menu)

        options_menu.add_command(label='User agent', command=self.open_user_agent_window)
        options_menu.add_command(label='Output directory', command=self.select_directory)

        help_button = tk.Menubutton(menu_frame, text="Help", bg='#FF851B', fg='#000000', font=('Arial', 10, 'bold'))
        help_button.pack(side='left', padx=2)

        help_menu = tk.Menu(help_button, tearoff=0, bg='#FF851B', fg='#000000', font=('Arial', 10, 'bold'))
        help_button.config(menu=help_menu)

        help_menu.add_command(label='Documentation', command=self.open_documentation)

        top_frame = tk.Frame(self, bg='#1e1e1e')
        top_frame.pack(fill='x', pady=10, padx=10)

        label = ttk.Label(top_frame, text="Search by CIK, company name or ticker")
        label.grid(row=0, column=0, sticky='w')

        self.entry = ttk.Entry(top_frame, width=50)
        self.entry.grid(row=0, column=1, padx=10, sticky='ew')
        self.entry.bind('<KeyRelease>', self.on_keyrelease)

        self.listbox = ttk.Treeview(self, columns=('cik', 'ticker', 'title'), show='headings')
        self.listbox.heading('cik', text='CIK')
        self.listbox.heading('ticker', text='Ticker')
        self.listbox.heading('title', text='Name')
        self.listbox.column('cik', width=100)
        self.listbox.column('ticker', width=100)
        self.listbox.column('title', width=500)
        self.listbox.pack(fill='both', expand=True, padx=10, pady=10)
        self.listbox.bind('<<TreeviewSelect>>', self.on_select)

        bottom_frame = tk.Frame(self, bg='#1e1e1e', padx=10, pady=10)
        bottom_frame.pack(fill='x', pady=10, padx=10)

        directory_label = ttk.Label(bottom_frame, text="Selected directory:")
        directory_label.grid(row=0, column=0, sticky='w')

        self.directory_display = ttk.Label(bottom_frame, textvariable=self.directory_path, width=60, anchor='w')
        self.directory_display.grid(row=0, column=1, padx=10, sticky='ew')

        export_button = ttk.Button(bottom_frame, text='Export to Excel', command=self.get_financial_data)
        export_button.grid(row=1, column=0, columnspan=2, sticky='w', pady=10)

        self.grid_rowconfigure(2, weight=1)
        self.grid_columnconfigure(1, weight=1)

    # Load the main app
    def load_main_app(self):
        self._build_gui()
        self.close_loading_screen()
        self._load_company_data()
        self.deiconify()
        self.focus_force()
        self.entry.focus_set()

    # Close the loading screen
    def close_loading_screen(self):
        if hasattr(self, 'loading_screen'):
            self.loading_screen.destroy()

    # Update the User-Agent in the app and reload data
    def update_user_agent(self):
        config_data = self.load_config()
        user_agent = config_data.get('user_agent', '')
        self.user_agent_data = {'User-Agent': user_agent} if user_agent else None
        if self.user_agent_data:
            self._load_company_data()

    # Open the documentation page in a browser
    def open_documentation(self):
        webbrowser.open("https://github.com/samuellleo/Mini-Terminal?tab=readme-ov-file#mini-terminal")

    # Export financial data to Excel
    def get_financial_data(self):
        def extract_data(all_data, path=None):
            result = []
            if path is None:
                path = []

            if isinstance(all_data, dict):
                for key, value in all_data.items():
                    new_path = path + [key]
                    if key == 'label':
                        label = {'label': value}

                    elif key == 'units':
                        for unit_key, unit_values in value.items():
                            for item in unit_values:
                                new_dict = {}

                                if 'label' in locals():
                                    new_dict.update(label)

                                new_dict.update(item)

                                result.append(new_dict)
                    else:
                        result.extend(extract_data(value, new_path))
            elif isinstance(all_data, list):
                for item in all_data:
                    result.extend(extract_data(item, path))

            return result

        def perform_data_fetching():
            headers = self.user_agent_data
            cik = self.selected_cik
            directory_path = self.directory_path.get()
            ticker = self.selected_ticker

            if cik and headers and directory_path and ticker:
                try:
                    all_data = requests.get(
                        f'https://data.sec.gov/api/xbrl/companyfacts/CIK{cik}.json',
                        headers=headers
                    ).json()

                    time_value = dt.now().strftime("%Y%m%d_%H%M%S")
                    financial_data = extract_data(all_data)
                    clean_financial_data = pd.DataFrame(financial_data)

                    excel_file_name = os.path.join(directory_path, f'{ticker}_{time_value}.xlsx')
                    clean_financial_data.to_excel(excel_file_name, index=False)

                except Exception as e:
                    messagebox.showerror("ERROR", str(e))
                finally:
                    loading_screen.destroy()
            else:
                messagebox.showwarning("ERROR", "All fields are mandatory")
                loading_screen.destroy()

        loading_screen = tk.Toplevel(self)
        loading_screen.geometry("300x100")
        loading_screen.title("Loading")
        loading_screen.configure(bg='#1e1e1e')
        loading_screen.overrideredirect(True)
        loading_screen.resizable(False, False)

        loading_screen.update_idletasks()
        x = (loading_screen.winfo_screenwidth() - loading_screen.winfo_width()) // 2
        y = (loading_screen.winfo_screenheight() - loading_screen.winfo_height()) // 2
        loading_screen.geometry(f"+{x}+{y}")

        label = ttk.Label(loading_screen, text="Processing data...", style="TLabel")
        label.pack(pady=20)

        progress = ttk.Progressbar(loading_screen, mode='indeterminate', style="TProgressbar")
        progress.pack(expand=True, fill='x', padx=20)
        progress.start()

        threading.Thread(target=perform_data_fetching).start()

    # Open a file dialog to select the output directory
    def select_directory(self):
        directory = filedialog.askdirectory()
        if directory:
            self.directory_path.set(directory)
            self.save_config('directory', directory)  # Save selected directory

    # Save configuration to config.json
    def save_config(self, key, value):
        try:
            config = {}
            if os.path.exists('config.json'):
                with open('config.json', 'r') as f:
                    config = json.load(f)
            config[key] = value
            with open('config.json', 'w') as f:
                json.dump(config, f)
        except Exception as e:
            messagebox.showerror("Error", f"Error saving {key}: {str(e)}")

    # Load saved configuration from config.json
    def load_config(self):
        if os.path.exists('config.json'):
            try:
                with open('config.json', 'r') as f:
                    return json.load(f)
            except Exception as e:
                messagebox.showerror("Error", f"Error loading config: {str(e)}")
                return {}
        return {}

    # Search functionality for company data
    def search(self, value):
        self.listbox.delete(*self.listbox.get_children())
        if not self.data.empty and value:
            data_filtered = self.data[(self.data['cik_str'].str.lower().str.contains(value)) |
                                      (self.data['title'].str.lower().str.contains(value)) |
                                      (self.data['ticker'].str.lower().str.contains(value))].head(15)
            for _, row in data_filtered.iterrows():
                title_upper = row['title'].upper()
                self.listbox.insert("", "end", values=(row['cik_str'], row['ticker'], title_upper))

    # Handle search input changes
    def on_keyrelease(self, event):
        value = event.widget.get().strip().lower()
        self.after(300, lambda: self.search(value))

    # Handle selection from the listbox
    def on_select(self, event):
        selected_item = self.listbox.selection()
        if selected_item:
            values = self.listbox.item(selected_item, 'values')
            self.selected_cik = values[0]
            self.selected_ticker = values[1]

    # Open the User-Agent configuration window
    def open_user_agent_window(self, modal=False):
        config_window = UserAgentConfig(self)
        if modal:
            self.wait_window(config_window)

    # Show error if there's an issue with the User-Agent or API data
    def show_user_agent_error(self, error):
        error_message = f"Connection error or invalid data: {error}\n\n" \
                        "The User-Agent used may not be valid. " \
                        "Try changing the User-Agent from the configuration menu."
        messagebox.showerror("Connection Error", error_message)


# Start the application
if __name__ == "__main__":
    app = BrowserWindow()
    app.mainloop()
