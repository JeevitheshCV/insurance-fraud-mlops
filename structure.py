import os

def print_project_structure_simple(startpath):
    """
    Prints a simple indented structure of a directory.
    """
    # Check if the path is a valid directory
    if not os.path.isdir(startpath):
        print(f"Error: The path '{startpath}' does not exist or is not a directory.")
        return

    print(f"Project Structure for: {startpath}\n")

    for root, dirs, files in os.walk(startpath):
        # Exclude common unwanted directories from the listing
        # You can add more directories like '.git', '.vscode', 'venv', etc.
        dirs[:] = [d for d in dirs if d not in ['__pycache__', '.git', 'venv']]
        
        level = root.replace(startpath, '').count(os.sep)
        indent = ' ' * 4 * (level)
        print(f'{indent}{os.path.basename(root)}/')
        
        sub_indent = ' ' * 4 * (level + 1)
        for f in sorted(files):
            print(f'{sub_indent}{f}')

# --- MAIN EXECUTION ---
if __name__ == "__main__":
    # Use a raw string (r"...") for Windows paths to avoid issues with backslashes
    project_path = r"D:\projects\fraud_detection\insurance-fraud-mlops"
    print_project_structure_simple(project_path)