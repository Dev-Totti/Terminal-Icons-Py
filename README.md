# Terminal-Icons-Py

This Python script provides a convenient way to list all files in a directory in a column view, similar to the `ls` command in Linux. The number of columns is automatically calculated based on the terminal width. Each file/folder is accompanied by a Nerd Font icon and color, inspired by the project *[Terminal-Icons](https://github.com/devblackops/Terminal-Icons)*.

#### Features:

- **Column View**: Display files and folders in a column layout for easy readability.
- **Automatic Column Calculation**: Adjusts the number of columns based on the terminal width.
- **Dynamic Column Width**: Each column dynamically adjusts its width depending on its content.
- **Details View**: This view provides file/dir size, attributes, and full path.
- **Nerd Font Icons**: Each file and folder is represented by a Nerd Font icon for added visual clarity.
- **Color Coding**: Utilizes color to distinguish between different types of files and folders.

#### Usage:
Simply run the Python script in the desired directory to view the contents in a visually appealing and organized column format.

```bash
python Terminal-Icons.py
```

#### Arguments:

```bash
python Terminal-Icons.py [-p <path>] [-f <filter>] [-c <columns>] [-r] [-a] [-d]
```
-p, --path <path>: Specify the directory path.

-f, --filter <filter>: Expression to filter files, e.g., *.exe.

-c, --columns <columns>: Number of columns to force in display.

-r, --recursive: Recursively list files and folders.

-a, --all: Show hidden files.

-d, --detail: Shows details view with additional information (file/dir size, attributes, and full path)
#### Dependencies:

- Python 3.x
- Nerd Fonts (for icons)

#### How It Works:

The script utilizes Python's built-in `os` module to list files and folders in the specified directory. It then calculates the optimal number of columns based on the terminal width and formats the output accordingly. Nerd Font icons and colors are applied to each entry for enhanced visualization.

#### License:

This project is licensed under the [MIT License](LICENSE). Feel free to use, modify, and distribute it as per the terms of the license.

#### Acknowledgments:

- Special thanks to the creators of *[Terminal-Icons](https://github.com/devblackops/Terminal-Icons)* for color/icon theme.
- This project is inspired by the functionality of the `ls` command in Linux.

#### Screenshots:
Columns View:

![Screenshot 2024-04-01 184750](https://github.com/Dev-Totti/Terminal-Icons-Py/assets/92545913/7b25bc45-ae03-4d9d-a2ef-6af4e536a12f)

Details View:

![2](https://github.com/Dev-Totti/Terminal-Icons-Py/assets/92545913/241cb888-4b2a-4036-a352-98ccd76a14eb)

