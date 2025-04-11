import os
import shutil
import tkinter as tk
from tkinter import filedialog, messagebox
from pathlib import Path
import time
import uuid

# Constants
LOG_FILE = "sorting_log.txt"
MAX_UNDO_STEPS = 100

# Define file categories
FILE_CATEGORIES = {
    "Documents": [".pdf", ".docx", ".txt", ".xlsx", ".pptx", ".doc", ".rtf", ".csv", ".odt"],
    "Images": [".jpg", ".png", ".jpeg", ".gif", ".bmp", ".tiff", ".svg", ".webp", ".heic"],
    "Videos": [".mp4", ".avi", ".mkv", ".mov", ".wmv", ".flv", ".webm", ".m4v", ".mpg"],
    "Music": [".mp3", ".wav", ".aac", ".flac", ".ogg", ".wma", ".m4a", ".opus"],
    "Archives": [".zip", ".rar", ".tar", ".7z", ".gz", ".bz2", ".xz", ".iso"],
    "Executables": [".exe", ".msi", ".bat", ".sh", ".app", ".dmg", ".pkg"],
    "Code": [
        # Source code files
        ".py", ".java", ".c", ".cpp", ".h", ".hpp", ".cs", ".js", ".ts", 
       ".php", ".rb", ".go", ".swift", ".kt", ".scala", ".m", ".pl",
        # Web files
        ".html", ".htm", ".css", ".scss", ".sass", ".less", ".jsx", ".tsx",
        # Configuration files
        ".json", ".yml", ".yaml", ".xml", ".toml", ".ini", ".cfg", ".conf",
        # Script files
        ".sh", ".bash", ".zsh", ".ps1", ".bat", ".cmd",
        # Build/development files
        ".md", ".markdown", ".rst", ".dockerfile", ".gitignore", ".gitattributes",
        # Data files
        ".sql", ".db", ".sqlite", ".dump",
       #  Other development files
       ".ipynb", ".env", ".lock"
    ],
    "Others": []
}

# Windows special folders
WINDOWS_FOLDERS = {
    "Documents": Path(os.path.expandvars("%USERPROFILE%")) / "Documents",
    "Pictures": Path(os.path.expandvars("%USERPROFILE%")) / "Pictures",
    "Videos": Path(os.path.expandvars("%USERPROFILE%")) / "Videos",
    "Music": Path(os.path.expandvars("%USERPROFILE%")) / "Music",
}

class FileSorterApp:
    def __init__(self):
        self.root = tk.Tk()
        self.icon = tk.PhotoImage(file="icon.png")
        self.root.iconphoto(True, self.icon)
        self.root.withdraw()
        self.current_session_id = None
        
        # Initialize log file
        if not os.path.exists(LOG_FILE):
            open(LOG_FILE, 'w').close()
        
        self.open_main_window()

    def start_new_session(self):
        """Generate a new unique session ID for each sorting operation"""
        self.current_session_id = str(uuid.uuid4())

    def log_operation(self, source, destination):
        """Log a file move operation with session ID"""
        timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
        with open(LOG_FILE, "a") as f:
            f.write(f"{timestamp}|{self.current_session_id}|{source}|{destination}\n")
        self.clear_old_log_entries()

    def clear_old_log_entries(self):
        """Keep only the most recent operations"""
        if os.path.exists(LOG_FILE):
            with open(LOG_FILE, "r") as f:
                lines = f.readlines()
            if len(lines) > MAX_UNDO_STEPS:
                with open(LOG_FILE, "w") as f:
                    f.writelines(lines[-MAX_UNDO_STEPS:])

    def get_last_session_operations(self):
        """Get all operations from the most recent session"""
        if not os.path.exists(LOG_FILE):
            return []
        
        with open(LOG_FILE, "r") as f:
            lines = f.readlines()
        
        if not lines:
            return []
        
        # Find the most recent session ID
        last_session_id = None
        for line in reversed(lines):
            parts = line.strip().split("|")
            if len(parts) >= 3:
                last_session_id = parts[1]
                break
        
        if not last_session_id:
            return []
        
        # Get all operations from that session
        operations = []
        for line in reversed(lines):
            parts = line.strip().split("|")
            if len(parts) >= 4 and parts[1] == last_session_id:
                operations.append({
                    "timestamp": parts[0],
                    "session": parts[1],
                    "source": parts[2],
                    "destination": parts[3]
                })
        
        return operations

    def undo_last_session(self):
        """Undo only the most recent sorting session"""
        operations = self.get_last_session_operations()
        if not operations:
            messagebox.showinfo("Info", "No operations to undo!")
            return
        
        session_id = operations[0]["session"]
        session_time = operations[0]["timestamp"]
        
        if not messagebox.askyesno("Confirm Undo", 
                                 f"Undo last sort operation from {session_time}?\n"
                                 f"({len(operations)} files will be moved back)"):
            return
        
        success_count = 0
        error_count = 0
        
        for op in reversed(operations):  # Undo in reverse order of original moves
            try:
                # Create parent directory if it doesn't exist
                os.makedirs(os.path.dirname(op["source"]), exist_ok=True)
                
                # Move file back if it exists at destination
                if os.path.exists(op["destination"]):
                    shutil.move(op["destination"], op["source"])
                    success_count += 1
                
                # Try to remove empty directory
                dest_dir = os.path.dirname(op["destination"])
                if os.path.exists(dest_dir) and not os.listdir(dest_dir):
                    try:
                        os.rmdir(dest_dir)
                    except OSError:
                        pass  # Directory not empty or other error
                    
            except Exception as e:
                print(f"Error undoing {op['destination']}: {e}")
                error_count += 1
        
        # Remove undone operations from log
        if success_count > 0:
            with open(LOG_FILE, "r") as f:
                lines = f.readlines()
            
            # Keep only lines that aren't from this session
            with open(LOG_FILE, "w") as f:
                for line in lines:
                    parts = line.strip().split("|")
                    if len(parts) < 3 or parts[1] != session_id:
                        f.write(line)
        
        messagebox.showinfo("Undo Complete", 
                          f"Successfully undone {success_count} files\n"
                          f"Errors: {error_count}")

    def create_back_button(self, window):
        back_btn = tk.Button(
            window,
            text="← Back",
            font=("Arial", 12),
            bg="#F44336",
            fg="white",
            width=10,
            padx=10,
            pady=5,
            command=lambda: self.go_back(window)
        )
        back_btn.pack(anchor='nw', padx=10, pady=10)
        return back_btn

    def go_back(self, window):
        window.destroy()
        self.open_main_window()

    def select_folder(self, entry):
        folder_selected = filedialog.askdirectory()
        if folder_selected:
            entry.delete(0, tk.END)
            entry.insert(0, folder_selected)

    def open_main_window(self):
        self.main_root = tk.Toplevel()
        self.main_root.title("File Sorter - Home")
        self.main_root.geometry("500x550")
        self.main_root.resizable(False, False)
        self.main_root.configure(bg="#1E1E1E")

        tk.Label(self.main_root, text="Welcome to File Sorter", font=("Arial", 20, "bold"), fg="#FFFFFF", bg="#1E1E1E").pack(pady=20)
        tk.Label(self.main_root, text="Choose Sorting Method", font=("Arial", 14), fg="#CCCCCC", bg="#1E1E1E").pack()

        tk.Button(self.main_root, text="Sort within Folder", font=("Arial", 12), bg="#4CAF50", fg="white", width=30, height=2, command=self.open_subdirectory_sort).pack(pady=10)
        tk.Button(self.main_root, text="Sort to Custom Directory", font=("Arial", 12), bg="#2196F3", fg="white", width=30, height=2, command=self.open_custom_sort).pack(pady=10)
        tk.Button(self.main_root, text="Sort to Windows Directories", font=("Arial", 12), bg="#FF9800", fg="white", width=30, height=2, command=self.open_windows_sort_ui).pack(pady=10)
        tk.Button(self.main_root, text="Undo Last Operation", font=("Arial", 12), bg="#9C27B0", fg="white", width=30, height=2, command=self.undo_last_session).pack(pady=10)

    def open_subdirectory_sort(self):
        self.main_root.destroy()
        self.sort_files_window("Subdirectory Sort")

    def open_custom_sort(self):
        self.main_root.destroy()
        self.custom_sort_window = tk.Toplevel()
        self.custom_sort_window.title("Custom File Sorter")
        self.custom_sort_window.geometry("500x700")
        self.custom_sort_window.resizable(False, False)
        self.custom_sort_window.configure(bg="#1E1E1E")

        self.create_back_button(self.custom_sort_window)

        tk.Label(self.custom_sort_window, text="Custom File Sorting", font=("Arial", 18, "bold"), fg="#FFFFFF", bg="#1E1E1E").pack(pady=10)

        # Source folder selection
        tk.Label(self.custom_sort_window, text="Select Source Folder:", fg="#FFFFFF", bg="#1E1E1E").pack()
        self.source_entry = tk.Entry(self.custom_sort_window, width=50)
        self.source_entry.pack(pady=5)
        tk.Button(self.custom_sort_window, text="Browse", command=lambda: self.select_folder(self.source_entry), bg="#2196F3", fg="white").pack(pady=5)

        # Destination folder selection
        tk.Label(self.custom_sort_window, text="Select Destination Folder (Optional):", fg="#FFFFFF", bg="#1E1E1E").pack()
        self.dest_entry = tk.Entry(self.custom_sort_window, width=50)
        self.dest_entry.pack(pady=5)
        tk.Button(self.custom_sort_window, text="Browse", command=lambda: self.select_folder(self.dest_entry), bg="#2196F3", fg="white").pack(pady=5)

        # File type selection
        tk.Label(self.custom_sort_window, text="Select File Types to Sort:", fg="#FFFFFF", bg="#1E1E1E").pack(pady=10)
        
        self.file_type_vars = {}
        frame = tk.Frame(self.custom_sort_window, bg="#1E1E1E")
        frame.pack()
        
        for i, category in enumerate(FILE_CATEGORIES.keys()):
            self.file_type_vars[category] = tk.BooleanVar(value=True)
            cb = tk.Checkbutton(frame, text=category, variable=self.file_type_vars[category], 
                              fg="#FFFFFF", bg="#1E1E1E", selectcolor="#1E1E1E")
            cb.grid(row=i//2, column=i%2, sticky="w", padx=10, pady=5)

        # First N / Last N files
        tk.Label(self.custom_sort_window, text="Sort only first N files (leave empty for all):", fg="#FFFFFF", bg="#1E1E1E").pack(pady=10)
        self.first_n_entry = tk.Entry(self.custom_sort_window, width=10)
        self.first_n_entry.pack()

        tk.Label(self.custom_sort_window, text="OR", fg="#FFFFFF", bg="#1E1E1E").pack()

        tk.Label(self.custom_sort_window, text="Sort only last N files:", fg="#FFFFFF", bg="#1E1E1E").pack(pady=5)
        self.last_n_entry = tk.Entry(self.custom_sort_window, width=10)
        self.last_n_entry.pack()

        # Sort button
        tk.Button(self.custom_sort_window, text="Sort Files", font=("Arial", 14, "bold"), 
                 bg="#4CAF50", fg="white", padx=20, pady=10, width=20,
                 command=self.perform_custom_sort).pack(pady=20)

    def perform_custom_sort(self):
        self.start_new_session()
        source_folder = self.source_entry.get()
        if not source_folder:
            messagebox.showerror("Error", "Please select a source folder!")
            return

        dest_folder = self.dest_entry.get() if self.dest_entry.get() else source_folder

        selected_categories = {category: FILE_CATEGORIES[category] 
                             for category, var in self.file_type_vars.items() 
                             if var.get()}
        
        if not selected_categories:
            messagebox.showerror("Error", "Please select at least one file type to sort!")
            return

        first_n = self.first_n_entry.get()
        last_n = self.last_n_entry.get()
        
        try:
            first_n = int(first_n) if first_n else None
            last_n = int(last_n) if last_n else None
        except ValueError:
            messagebox.showerror("Error", "Please enter valid numbers for N files")
            return

        start_time = time.time()
        files = os.listdir(source_folder)
        sorted_count = 0

        if first_n:
            files = files[:first_n]
        elif last_n:
            files = files[-last_n:]

        for file in files:
            file_path = os.path.join(source_folder, file)
            if os.path.isfile(file_path):
                file_ext = os.path.splitext(file)[1].lower()
                file_moved = False

                for category, extensions in selected_categories.items():
                    if file_ext in extensions:
                        dest_dir = os.path.join(dest_folder, category)
                        os.makedirs(dest_dir, exist_ok=True)
                        try:
                            dest_path = os.path.join(dest_dir, file)
                            shutil.move(file_path, dest_path)
                            self.log_operation(file_path, dest_path)
                            sorted_count += 1
                            file_moved = True
                            break
                        except Exception as e:
                            print(f"Error moving {file}: {e}")
                            file_moved = True
                            break

                if not file_moved and "Others" in selected_categories:
                    dest_dir = os.path.join(dest_folder, "Others")
                    os.makedirs(dest_dir, exist_ok=True)
                    try:
                        dest_path = os.path.join(dest_dir, file)
                        shutil.move(file_path, dest_path)
                        self.log_operation(file_path, dest_path)
                        sorted_count += 1
                    except Exception as e:
                        print(f"Error moving {file}: {e}")

        end_time = time.time()
        time_taken = end_time - start_time
        
        messagebox.showinfo("Success", 
                          f"Files sorted successfully!\n"
                          f"Total files moved: {sorted_count}\n"
                          f"Time taken: {time_taken:.2f} seconds")

    def open_windows_sort_ui(self):
        self.main_root.destroy()
        
        self.windows_sort_root = tk.Toplevel()
        self.windows_sort_root.title("Sort to Windows Directories")
        self.windows_sort_root.geometry("500x400")
        self.windows_sort_root.resizable(False, False)
        self.windows_sort_root.configure(bg="#1E1E1E")

        self.create_back_button(self.windows_sort_root)

        tk.Label(self.windows_sort_root, text="Sort to Windows Directories", font=("Arial", 18, "bold"), fg="#FFFFFF", bg="#1E1E1E").pack(pady=20)
        
        tk.Label(self.windows_sort_root, text="Select Source Folder:", fg="#FFFFFF", bg="#1E1E1E").pack()
        self.folder_entry = tk.Entry(self.windows_sort_root, width=50)
        self.folder_entry.pack(pady=5)
        tk.Button(self.windows_sort_root, text="Browse", command=lambda: self.select_folder(self.folder_entry), bg="#2196F3", fg="white").pack(pady=5)
        
        tk.Button(self.windows_sort_root, text="Sort Files", font=("Arial", 14, "bold"), bg="#4CAF50", fg="white", padx=20, pady=10, width=20,
                  command=self.sort_files_to_windows_folders).pack(pady=20)

    def sort_files_to_windows_folders(self):
        self.start_new_session()
        source_folder = self.folder_entry.get()
        if not source_folder:
            messagebox.showerror("Error", "Please select a source folder!")
            return

        start_time = time.time()
        files_moved = 0
        
        for file in os.listdir(source_folder):
            file_path = os.path.join(source_folder, file)
            if os.path.isfile(file_path):
                file_ext = os.path.splitext(file)[1].lower()
                
                destination_folder = None
                for category, extensions in FILE_CATEGORIES.items():
                    if file_ext in extensions:
                        if category == "Images":
                            destination_folder = WINDOWS_FOLDERS.get("Pictures")
                        elif category in WINDOWS_FOLDERS:
                            destination_folder = WINDOWS_FOLDERS.get(category)
                        break
                
                if destination_folder:
                    try:
                        os.makedirs(destination_folder, exist_ok=True)
                        dest_path = destination_folder / file
                        shutil.move(file_path, str(dest_path))
                        self.log_operation(file_path, str(dest_path))
                        files_moved += 1
                    except Exception as e:
                        print(f"Error moving {file}: {e}")

        end_time = time.time()
        time_taken = end_time - start_time
        
        messagebox.showinfo("Sorting Complete", 
                           f"Moved {files_moved} files to Windows directories.\n"
                           f"Time taken: {time_taken:.2f} seconds")
        self.windows_sort_root.destroy()
        self.open_main_window()

    def sort_files_window(self, title):
        self.sort_root = tk.Toplevel()
        self.sort_root.title(title)
        self.sort_root.geometry("500x400")
        self.sort_root.resizable(False, False)
        self.sort_root.configure(bg="#1E1E1E")

        self.create_back_button(self.sort_root)

        tk.Label(self.sort_root, text=title, font=("Arial", 20, "bold"), fg="#FFFFFF", bg="#1E1E1E").pack(pady=10)
        
        tk.Label(self.sort_root, text="Select Source Folder:", fg="#FFFFFF", bg="#1E1E1E").pack()
        self.source_entry = tk.Entry(self.sort_root, width=50)
        self.source_entry.pack(pady=5)
        tk.Button(self.sort_root, text="Browse", command=lambda: self.select_folder(self.source_entry), bg="#2196F3", fg="white").pack(pady=5)

        tk.Button(self.sort_root, text="Sort Files", font=("Arial", 14, "bold"), bg="#4CAF50", fg="white", padx=20, pady=10, width=20,
                 command=self.perform_subdirectory_sort).pack(pady=20)

    def perform_subdirectory_sort(self):
        self.start_new_session()
        source_folder = self.source_entry.get()
        if not source_folder:
            messagebox.showerror("Error", "Please select a source folder!")
            return

        start_time = time.time()
        sorted_count = 0

        for file in os.listdir(source_folder):
            file_path = os.path.join(source_folder, file)
            if os.path.isfile(file_path):
                file_ext = os.path.splitext(file)[1].lower()
                file_moved = False

                for category, extensions in FILE_CATEGORIES.items():
                    if file_ext in extensions:
                        dest_folder = os.path.join(source_folder, category)
                        os.makedirs(dest_folder, exist_ok=True)
                        try:
                            dest_path = os.path.join(dest_folder, file)
                            shutil.move(file_path, dest_path)
                            self.log_operation(file_path, dest_path)
                            sorted_count += 1
                            file_moved = True
                            break
                        except Exception as e:
                            print(f"Error moving {file}: {e}")
                            file_moved = True
                            break

                if not file_moved:
                    dest_folder = os.path.join(source_folder, "Others")
                    os.makedirs(dest_folder, exist_ok=True)
                    try:
                        dest_path = os.path.join(dest_folder, file)
                        shutil.move(file_path, dest_path)
                        self.log_operation(file_path, dest_path)
                        sorted_count += 1
                    except Exception as e:
                        print(f"Error moving {file}: {e}")

        end_time = time.time()
        time_taken = end_time - start_time
        
        messagebox.showinfo("Success", 
                           f"Files sorted successfully!\n"
                           f"Total files moved: {sorted_count}\n"
                           f"Time taken: {time_taken:.2f} seconds")

# Start the application
if __name__ == "__main__":
    app = FileSorterApp()
    tk.mainloop()