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

    args = parser.parse_args()

    path = args.path if args.path else os.getcwd()
    filter = args.filter if args.filter else "*"
    hidden = args.all
    recurse = args.recurse
    columns = int(args.columns) if args.columns else None

    return path, filter, hidden, recurse, columns


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


# def resolveIcon1(filename, itemType):
#     filename = filename.lower()
#     _, ext = os.path.splitext(filename)

#     if filename in icons[itemType]["WellKnown"]:
#         return icons[itemType]["WellKnown"][filename]
#     elif ext in icons[itemType]:
#         return icons[itemType][ext]
#     else:
#         return icons[itemType][""]


# def resolveColor1(filename, itemType):
#     filename = filename.lower()
#     _, ext = os.path.splitext(filename)

#     if filename in colors[itemType]["WellKnown"]:
#         return convertHexToSeq(colors[itemType]["WellKnown"][filename])
#     elif ext in colors[itemType]:
#         return convertHexToSeq(colors[itemType][ext])
#     else:
#         return ""


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
    resetCode = f"\033[0m"

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


if __name__ == "__main__":
    icons, colors, glyphs = loadJSONFiles()
    path, filter, hidden, recurse, columns = getArguments()
    files = listFiles(path, filter, hidden, recurse)

    if files == []:
        sys.exit()

    displayIcons(files, columns, 6)
