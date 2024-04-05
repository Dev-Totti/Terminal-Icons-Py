import os, sys, math, json, fnmatch
from argparse import ArgumentParser
from natsort import natsorted


def getArguments():
    parser = ArgumentParser(description="List Files In Directory With Icons")
    parser.add_argument("-p", "--path", type=str, help="Path to the Directory")
    parser.add_argument("-f", "--filter", type=str, help="Filter Files")
    parser.add_argument("-c", "--columns", help="Number of Columns")
    parser.add_argument("-r", "--recurse", action="store_true", help="Recurse Files")
    parser.add_argument("-a", "--all", action="store_true", help="Show Hidden Files")
    parser.add_argument("-d", "--detail", action="store_true", help="Show File Details")

    args = parser.parse_args()

    path = args.path if args.path else os.getcwd()
    filter = args.filter if args.filter else "*"
    hidden = args.all
    recurse = args.recurse
    detail = args.detail
    columns = int(args.columns) if args.columns else None

    return path, filter, hidden, recurse, detail, columns


def loadJSONFile(file):
    with open(file, encoding="utf-8") as f:
        data = json.load(f)
    return data


def loadJSONFiles():
    scriptDir = os.path.dirname(os.path.abspath(__file__))
    icons = loadJSONFile(os.path.join(scriptDir, "Data", "Icons.json"))
    colors = loadJSONFile(os.path.join(scriptDir, "Data", "Colors.json"))
    glyphs = loadJSONFile(os.path.join(scriptDir, "Data", "Glyphs.json"))
    return icons, colors, glyphs


def checkWindowsTerminal():
    if os.environ.get("WT_SESSION"):
        return True
    return False


def getTerminalWidth():
    try:
        return os.get_terminal_size().columns
    except OSError:
        return 80


def isHidden(path):
    return bool(os.stat(path).st_file_attributes & 0x02)


def listFiles(path=".", filter=None, hidden=False, recurse=False):
    files = []

    for root, dirs, filenames in os.walk(path):
        iterList = filenames + dirs

        for itemName in iterList:
            itemMatch = fnmatch.fnmatch(itemName, filter)

            if itemMatch:
                itemPath = os.path.join(root, itemName)
                itemHidden = isHidden(itemPath)
                itemJunction = os.path.isjunction(itemPath)

                if hidden or not itemHidden and not itemJunction:
                    itemType = "Directories" if os.path.isdir(itemPath) else "Files"
                    itemIcon, itemColor = getIconColor(itemName, itemType, itemJunction)
                    itemInfo = {
                        "FilePath": itemPath,
                        "FileBase": root,
                        "Filename": itemName,
                        "FileHidden": itemHidden,
                        "Type": itemType,
                        "Icon": itemIcon,
                        "Color": itemColor,
                    }

                    files.append(itemInfo)
        if not recurse:
            break

    return natsorted(files, key=lambda x: (x["Type"], x["FilePath"].lower()))


def getIconColor(filename, itemType, junction=False):
    filename = filename.lower()
    _, ext = os.path.splitext(filename)

    if filename in icons[itemType]["WellKnown"]:
        itemIcon = icons[itemType]["WellKnown"][filename]
    elif ext in icons[itemType]:
        itemIcon = icons[itemType][ext]
    else:
        itemIcon = icons[itemType][""]

    if filename in colors[itemType]["WellKnown"]:
        itemColor = convertHexToSeq(colors[itemType]["WellKnown"][filename])
    elif ext in colors[itemType]:
        itemColor = convertHexToSeq(colors[itemType][ext])
    else:
        itemColor = ""

    if junction:
        itemIcon = icons["Junction"][""]
        itemColor = convertHexToSeq(colors["Junction"][""])

    return itemIcon, itemColor


def convertHexToSeq(hexColor):
    red = int(hexColor[0:2], 16)
    green = int(hexColor[2:4], 16)
    blue = int(hexColor[4:6], 16)
    return f"\033[38;2;{red};{green};{blue}m"


def getMaxRowLen(filenames, numCols, padding=0, force=False):
    terminalWidth = getTerminalWidth()
    numRows = math.ceil(len(filenames) / numCols)
    cols = [[] for _ in range(numCols)]

    for i in range(len(filenames)):
        index = i // numRows
        cols[index].append(len(filenames[i]))

    maxColLen = [max(col) for col in cols if col != []]
    avgColLen = [int((sum(col) / len(col)) * 2) for col in cols if col != []]

    maxSumRowLen = sum(maxColLen) + padding * (numCols - 1) + 3
    maxAvgRowLen = sum(avgColLen) + padding * (numCols - 1) + 3

    if force:
        if maxAvgRowLen > terminalWidth:
            return maxAvgRowLen, avgColLen
    else:
        if maxSumRowLen <= terminalWidth:
            return maxSumRowLen, maxColLen
        elif maxAvgRowLen <= terminalWidth:
            return maxAvgRowLen, avgColLen

    return maxSumRowLen, maxColLen


def getMaxColumns(filenames, padding=0):
    terminalWidth = getTerminalWidth()
    avgColLen = int(sum(len(filename) for filename in filenames) / len(filenames))

    low = 2
    high = terminalWidth // avgColLen + 3

    while low < high:
        mid = (low + high) // 2

        maxRowLen, _ = getMaxRowLen(filenames, mid, padding)
        if maxRowLen > terminalWidth:
            high = mid
        else:
            low = mid + 1

    return max(mid - 1, 1) if mid == high else mid


def displayIcons(filesInfo, numCols=1, padding=0):
    fileNames = [file["Filename"] for file in filesInfo]
    terminalWidth = getTerminalWidth()

    if numCols == None:
        numCols = getMaxColumns(fileNames, padding)

    maxRowLen, maxColLen = getMaxRowLen(fileNames, numCols, padding, True)

    maxRowLenNoPad = sum(maxColLen)
    terminalEmptySpace = terminalWidth - padding * (numCols - 1) - 3

    if maxRowLen > terminalWidth:
        maxColLen = [col * terminalEmptySpace // maxRowLenNoPad for col in maxColLen]

    numRows = math.ceil(len(filesInfo) / numCols)
    numCols = math.ceil(len(filesInfo) / numRows)

    colsPadding = " " * (padding - 3 if checkWindowsTerminal() else padding - 4)
    extraPadding = "" if checkWindowsTerminal() else " "

    for i in range(numRows):
        outputRows = ""
        for j in range(numCols):
            index = i + j * numRows
            if index < len(filesInfo):
                itemFilename = filesInfo[index]["Filename"]
                itemHidden = filesInfo[index]["FileHidden"]

                itemColor = filesInfo[index]["Color"]
                itemIcon = glyphs[filesInfo[index]["Icon"]]["char"]
                itemIconLen = len(itemIcon.encode("UTF-16-LE")) // 2

                if itemHidden:
                    itemFilename = f"*{itemFilename}"

                itemName = itemFilename.ljust(maxColLen[j])[: maxColLen[j]]

                if len(itemName) < len(itemFilename):
                    itemName = itemName[:-1] + "…"

                if itemIconLen == 1:
                    itemName += extraPadding

                item = f"{itemColor}{itemIcon}  {itemName}{resetCode}{colsPadding}"
                outputRows += item

        print(outputRows.rstrip())


def getAttributes(filepath):
    attribute_symbols = {
        "D": lambda path: "d" if os.path.isdir(path) else "-",
        "A": lambda st: "a" if st.st_file_attributes & 0x20 else "-",
        "R": lambda st: "r" if st.st_file_attributes & 0x01 else "-",
        "H": lambda st: "h" if st.st_file_attributes & 0x02 else "-",
        "S": lambda st: "s" if st.st_file_attributes & 0x04 else "-",
    }

    st = os.stat(filepath)
    attributes = [
        attribute_symbols[key](filepath if key == "D" else st)
        for key in attribute_symbols
    ]

    return "".join(attributes)


def formatSize(size):
    units = ["-B", "KB", "MB", "GB", "TB"]
    unit_index = 0
    while size >= 1024 and unit_index < len(units) - 1:
        size /= 1024.0
        unit_index += 1

    decimal_places = 2 if unit_index > 1 else 0

    return f"{size:.{decimal_places}f} {units[unit_index]}"


def displayDetails(filesInfo, recurse=False):
    terminalWidth = getTerminalWidth()

    filenames = [fileInfo["Filename"] for fileInfo in filesInfo]
    basenames = [fileInfo["FileBase"] for fileInfo in filesInfo]

    MaxNameLen = max(len(name) for name in filenames)
    MaxBaseLen = max(len(name) for name in basenames)

    AvgNameLen = int(sum(len(name) for name in filenames) / len(filenames) * 1.2)

    MaxRowLen = MaxNameLen + MaxBaseLen + 20

    if MaxRowLen > terminalWidth:
        MaxNameLen = AvgNameLen

    EmptySpace = terminalWidth - MaxNameLen - 20

    for file in filesInfo:
        filePath = file["FilePath"]
        fileBase = file["FileBase"]
        fileName = file["Filename"]
        fileColor = file["Color"]
        fileIcon = glyphs[file["Icon"]]["char"]

        itemName = fileName.ljust(MaxNameLen)[:MaxNameLen]
        itemName = itemName[:-1] + "…" if len(itemName) < len(fileName) else itemName
        itemName = f"{fileColor}{fileIcon}  {itemName}{resetCode}"

        if os.path.isdir(filePath):
            itemSize = sum(
                os.path.getsize(os.path.join(root, f))
                for root, _, files in os.walk(filePath)
                for f in files
            )
        else:
            itemSize = os.stat(filePath).st_size

        itemSize = formatSize(itemSize)
        itemMode = getAttributes(filePath)

        print(f"{itemMode} {itemName} {itemSize:>9}", end="")

        if recurse:
            overflowPrint(fileBase, EmptySpace, MaxNameLen + 20)
        else:
            print()

        # remaining = ""
        # if len(fileBase) > EmptySpace:
        #     remaining = fileBase[EmptySpace:]
        #     fileBase = fileBase[:EmptySpace]
        # print(f"{' ' * (MaxNameLen + 20)}{filebaseColor}{remaining}{resetCode}")


def overflowPrint(text, length, offset, aux=False):
    print("\033[38;2;120;120;120m", end="")
    if aux:
        if len(text) > length:
            print(f"{' ' * offset}{text[:length]}")
            overflowPrint(text[length:], length, offset, True)
        else:
            print(f"{' ' * offset}{text}")
    else:
        if len(text) > length:
            print(f" {text[:length]}")
            overflowPrint(text[length:], length, offset, True)
        else:
            print(f" {text}")
    print(resetCode, end="")


if __name__ == "__main__":
    resetCode = f"\033[0m"
    icons, colors, glyphs = loadJSONFiles()
    path, filter, hidden, recurse, detail, columns = getArguments()
    files = listFiles(path, filter, hidden, recurse)

    if files == []:
        sys.exit()

    if detail:
        displayDetails(files, recurse)
    else:
        displayIcons(files, columns, 6)
