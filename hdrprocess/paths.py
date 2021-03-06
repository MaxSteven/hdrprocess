#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Description
+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
Methods dealing specifically with path strings and folder/file structures

"""

# IMPORT STANDARD LIBRARIES
import os
import re
import ntpath
import errno
import stat

# IMPORT STANDARD LIBRARIES
# import logger.common.loggingServices as loggingservices
# LOGGER = loggingservices.init_logger()
import filesequencer as fileSeq


def path_leaf(path):
    """
    os.path.split()[-1] doesn't work in all cases (if you run the script in
    Linux and attempt to split a Windows-Style path). This function is a
    solution by Lauritz V. Thaulow

    .. Reference::
        https://stackoverflow.com/questions/8384737

    Args:
    path (str): The full path to get the filename from

    Returns:
        str: The filename at the end of the path
    """
    head, tail = ntpath.split(path)
    return tail or ntpath.basename(head)
# end path_leaf


def os_path_split_asunder(path, debug=False):
    """
    IMPORTANT: before running, you must use os.path.splitdrive(path)
    and separate the drive and path. Otherwise Windows paths will
    create errors. You'll have to manually add the drive letter back in

    This method is comparably safer for splitting and merging paths
    than other methods such as replace_sep_with_string

     >>> path = r'C:\some\path'
     >>> drive, path = os.splitdrive(path)
     >>> splitPath = os_path_split_asunder(path)
     ['some', 'path']

    Args:
        path (str): The string path to be processed
        debug (bool): Whether or not to send debug information to stdout
                      to catch in a logger
    Returns:
        list: A list which contains the entire path, separated by folders
    """
    parts = []
    while True:
        newpath, tail = os.path.split(path)
        if debug: print repr(path), (newpath, tail)
        if newpath == path:
            assert not tail
            if path: parts.append(path)
            break
        parts.append(tail)
        path = newpath
    parts.reverse()
    parts = [x for x in parts if x != '']
    return parts
# end os_path_split_asunder


def walk_level(someDir, level=1, output="files"):
    """
    walk_level will recursively traverse a given folder and output, files,
    folders, or both in the form of a list

    Args:
        someDir (str): The directory to walk into
        level (int): The number of folders down allowed
        output (str): Decide if you want files/folders/files+folders as return

    Returns:
        list of strs: A list of files/folders/files+folders
    """
    someDir = someDir.rstrip(os.path.sep)
    assert os.path.isdir(someDir)
    numSep = someDir.count(os.path.sep)

    outputPossibilities = ['FILES', 'FOLDERS', 'FILES+FOLDERS']
    output = output.upper()
    if output not in outputPossibilities:
        raise RuntimeError('Option: "{}" did not receive proper args. '
                           'Possiblities are {}'.format(output,
                                                        outputPossibilities))
    for root, dirs, files in os.walk(someDir):
        if output.upper() == "FILES":
            for file in files:
                yield os.path.join(root, file)
        elif output.upper() == "FILES+FOLDERS":
            for dir in dirs:
                yield os.path.join(root, dir)
            for file in files:
                yield os.path.join(root, file)
        elif output.upper() == 'FOLDERS':
            for dir in dirs:
                yield os.path.join(root, dir)
        numSepCurrent = root.count(os.path.sep)
        if numSep + level <= numSepCurrent:
            del dirs[:]
# end walklevel


def mkdir_p(path, existsOk=True):
    """
    Emulates the linux command mkdir -p, where the command makes a dir and
    all of its parent dirs if they do not exist

    Args:
        path (str): The path of folders that you wish to create
        existsOk (bool): Decides if the command should be permitted to run
                         if the dir already exists

    Returns:
        bool: True/False depending on whether or not path as properly created
    """
    try:
        os.makedirs(path)
    except OSError as exc:  # Python >2.5
        if existsOk and exc.errno == errno.EEXIST and os.path.isdir(path):
            pass
        else:
            raise

    if os.path.isdir(path):
        return True
    else:
        return False
# end mkdir_p


def get_expanded_str_from_index(inputH, index):
    """
    Returns a given number from a parseable string
    as an expanded string with correct padding

    .. TODO::
     If time, go back and make this function more memory efficient

    Args:
        inputH (str): The full path to a file or filename
        index (int): The numbered frame to retrieve from the expanded string

    Returns:
        str: The expanded string without any expression or formatted text
    """
    matchTest = path_leaf(inputH)
    expansionTest = list(fileSeq.expand_sequence(matchTest))
    return expansionTest[index]
# end get_expanded_str_from_index


def parse_sequence(inputH, rootPath, checkExist):
    """
    Files files from a formatted string with expression (TCL %04d,
    Houdini-style $F4, Nuke's ####) are parsed into full file names and tested
    for existence

    Example input:
     >>> someFile = "some_file_$F2.tiff"
     Generator Object containing...
     some_file_00.tiff some_file_01.tiff some_file_02.tiff some_file_03.tiff
     some_file_04.tiff some_file_05.tiff some_file_06.tiff some_file_07.tiff
     some_file_08.tiff some_file_09.tiff

    Args:
        inputH (str): The file/folder path to parse
        rootPath (str): Used for attempting to resolve relative paths and checking
                        File(s)/Folder(s) for existence
        checkExist (bool): True/False

    Yields:
        str: A generator containing all of the parsed strings found
    """
    matchTest = path_leaf(inputH)
    expansionTest = list(fileSeq.expand_sequence(matchTest))

    if expansionTest[0] is not None:
        matchTest = expansionTest
        dirname = os.path.dirname(inputH)
        for m in matchTest:
            mTest = os.path.normpath(os.path.join(dirname, m))
            if is_relative(mTest):
                mTest = os.path.join(rootPath, mTest)
                mTest = os.path.normpath(mTest)

            # attempt hard join
            if checkExist and (not os.path.isfile(mTest) \
                    or not os.path.isdir(mTest)):
                continue  # skip
            elif os.path.isfile(mTest) or os.path.isdir(mTest):
                # LOGGER.info("[+] File/Folder: {f} found from, "
                # "{f1}".format(f=mTest, f1=inputH))
            # ::AUTHORNOTE:: add support for strings that aren't yet files/folders
            # for examples, strings that represents files that will be rendered
            # assume
            yield mTest
# end parse_seqence


def is_parseable(string):
    """
    Checks if a file/folder path has text in it that could be considered
    "Able to be parsed" or expanded into a sequence of files

    .. TODO::
     Replace this with a regex that detects if there is ####, $F4, or %04d

    Args:
        string (str): The string to check

    Returns:
        bool: True/False
    """
    if "#" in string:
        return True
    elif "%" in string:
        return True
    elif "$" in string:
        return True
    else:
        return False
# end is_parseable


def replace_sep_with_string(path, inputH):
    """
    Replaces the seperators in a string of text with inputH

    .. Note::
     DEPRECATED in-favor of os.path.normcase()/os.path.normpath()

    Args:
        path (str): The path to replace the separators
        inputH (str or anything): The object to replace separators with

    Returns:
        str: The original path, with eahc of its separators replaced
    """
    matchRe = re.compile(r"//|/|\\*?")  # get all types of separators
    line = matchRe.sub(path, inputH)
    return line
# end replace_sep_with_string


def search_parent_count(string):
    """
    Looks at a relative path and determines how many parent folders back
    the path is refers to, if at all

    Example:
     >>> search_parent_count("../../some/path/foo.bar")
     2

    Args:
        string (str): The (presumably relative path) string to check

    Returns:
        int: The number of parent folders to search back
    """
    reMatch = re.compile(r'(?:\.\./)|(?:\.\.\\)|(?:\./)|(?:\.\\)')
    match = re.findall(reMatch, string)

    if match is None or match == []:
        return None
    elif len(match[0]) == 2:
        return {'match': match[0],
                'count': len(match),
                'is_current_dir': True}
    elif len(match[0]) == 3:
        return {'match': match[0],
                'count': len(match),
                'is_current_dir': False}
# end search_parent_count


def is_current_dir(string):
    """
    Checks if the path has a relative prefix that references
    the current directory

    Args:
        string (str): The filepath that may or may not prefix with ./|.\\

    Returns:
        bool: True/False
    """
    reMatch = re.compile(r'(?:\./)|(?:\.\\)')
    match = re.findall(reMatch, string)

    if search_parent_count(string) is not None and \
       len(search_parent_count(string)['match']) == 3:
        return False  # catch exceptions for ../, ..\, and ..\\
    elif match is None or match == []:
        return False  # nothing found
    else:
        return True  # found ./, .\, or .\\
# end is_current_dir


def is_relative(string):
    """
    OS-Naive method that checks if the current path has a relative prefix

    Args:
        string (str): The filepath to check for relative path markers

    Returns:
        bool: True/False
    """
    _, winfilename = os.path.splitdrive(string)
    if not string.startswith('/') or winfilename != string:
        return True

    if search_parent_count(string) is not None or is_current_dir(string):
        return True
    else:
        return False
# end is_relative


def get_size(startPath='.'):
    """
    Gets size of a folder

    Args:
        startPath (str): The full path that is the base directory of get_size

    Returns:
        int: The total size, in bytes
    """
    totalSize = 0
    for dirpath, dirnames, filenames in os.walk(startPath):
        for f in filenames:
            fp = os.path.join(dirpath, f)
            totalSize += os.path.getsize(fp)
    return totalSize
# end get_size


def get_maya_files(inputH, level, endswith):
    """
    Gets all files that match a certain extension from a list of files
    and folders. Supports recursion

    .. Note::
     Written with Maya files in mind but actually supports any file-type

    Args:
        inputH (str): an iterable which contains full paths to folders
        level (int): The number of subfolders allowed to search for maya files.
                     Set to a large number to mimic the behavior of a fully
                     recursive query (once it reaches the end it will terminate
                     on its own)
        endswith (str or tuple of strs): The file extension to search for.
                                         If you want to return all files, use *

    Yields:
        str: An iterable of full paths to files
    """
    for entry in inputH:
        if os.path.isdir(entry):
            getListings = walk_level(entry, level)
            files = list(getListings)
            files = [f for f in files if os.path.isfile(f)]
            files = [f for f in files if f.endswith(endswith)]
        elif os.path.isfile(entry):
            files = [entry]
        else:
            temp = '[-] The following input, "{f}", is not a valid '\
                   'file or folder'.format(f=f)
            # LOGGER.error(temp)

        for f in files:
            yield f
# end get_maya_files


# def ignore_paths(path):
#     """
#     Designates which files to ignore in a struct-tree representing
#     file(s)/folder(s). For an example of how it's used, see: :ref:`syncmeister`
#     """
#     def ignoref(p, files):
#         return (f for f in files if os.abspath(os.path.join(p, f)) == path)
#     return ignoref
# # end ignore_paths

def get_common_parent_dir_pair(path1, path2, mustExist=True, mustMatch=True):
    """
    Compares two paths for a common prefix much like os.path.commonprefix() but
    has the additional functionality of checking if the results are not partial
    matches and whether or not the match exists as a file/folder

    Args:
        path1 (str): One of the paths to be compared
        path2 (str): Another path to be compared
        mustExist (bool): Requires that the prefix obtained must actually exist

    Returns:
        bool: True/False
    """
    if len(path1) > len(path2):
        # swap the strings if the user input them out of order
        path1, path2 = path2, path1

    commonPrefix = os.path.commonprefix([path1, path2])
    if commonPrefix == "":
        return None
    elif commonPrefix != "" and not mustMatch and mustExist \
                                              and os.path.exists(commonPrefix):
        return commonPrefix
    elif commonPrefix != "" and not mustExist and not mustMatch:
        return commonPrefix

    _, commonPath = os.path.splitdrive(commonPrefix)
    _, path = os.path.splitdrive(path2)  # only one path is needed for testing

    commonPathSplit = os_path_split_asunder(commonPath)
    pathSplit = os_path_split_asunder(path)

    for index, folder in enumerate(pathSplit):
        # this is a precaution to make sure partial commonprefixes
        if commonPathSplit[-1] == folder:
            return os.path.join(commonPathSplit)
    return None
# end get_common_parent_dir_pair


def has_common_parent_dir(path, comparisonPaths,
                          mustExist=True, mustMatch=True):
    """
    has_common_parent_dir is built for the purpose of determining if a given
    iterable (list or iterable) contains a string that is a parent directory.
    This function was made because os.path.commonprefix() frequently returns
    directories starting with "/|\\|\\\\" or a substring of files/folders that
    don't exist and there's no way to error check it.

    Example of why os.path.commonprefix sucks:
     >>> path1 = "some/directory/within/project.txt"
     >>> path2 = "some/directory/withstanding/project.txt"
     >>> os.path.commonprefix([path1, path2])
     "some/directory/with"  # This is not necessarily a file or folder!

    .. TODO::
     It may be worth doing in the future to remake this as a wrapper function
     to os.path.commonprefix() and simply test if any folder starts with the
     substring match and, if that same matched folder is the [-1] index of the
     checked file(s)/folder(s) it could return True and still do the same thing

    Args:
        path (str): The path that supposedly is the root of all other paths listed
                    in comparisonPaths
        comparisonPaths (iterable of strs): An iterable of paths to check
                                            against path for a common parent
                                            directory

    Returns:
        bool: True/False
    """
    for index, item in enumerate(comparisonPaths):
        # temp paths - remove the instance of path in list
        if path != item:
            hasCommonDir = get_common_parent_dir_pair(path,
                                                      item,
                                                      mustExist=mustExist,
                                                      mustMatch=mustMatch)
            if hasCommonDir is not None:
                break
    else:
        return False

    return True
# end has_common_parent_dir


if __name__ == '__main__':
    print(__doc__)
    # import tempfile
    # fileH = tempfile.mkstemp()[1]
    # bytes = 10240
    # size = test_byte_file(fileH)
    # if size != bytes:
    #     sys.exit("It didn't work")
    # path1 = "/home/selecaotwo/Desktop/destination_folder"
    # path1 = "C:/home/selecaotwo/Desktop/destination_folder"
    # path2 = "C:/home/selecaotwo/Desktop/src_folder"
    # match = get_common_parent_dir_pair(path1, path2, mustExist=False)
    # print match
