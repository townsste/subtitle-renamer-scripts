import os
import sys
import shutil
import itertools
from glob import glob
from os.path import join
from os.path import basename
from difflib import SequenceMatcher
from collections import defaultdict

def similar(a, b):
  return SequenceMatcher(None, a, b).ratio()

workingDir = str(sys.argv[1])

print("workingDir", workingDir)

# Verify we're in the right spot
subsDir = ' '.join(glob(workingDir + '/*[sS][uU][bB]*'))
if (not os.path.isdir(subsDir)):
  print(workingDir, "is not a directory with subtitles in it")
  sys.exit(1)

# Files that are 1 layer deep
movieFiles = glob(subsDir + "/*.srt")
# Sort files by size
movieFiles = sorted( movieFiles, key =  lambda x: os.stat(x).st_size)

# Gets the ISO code "en", "fr", etc.
# from the file basename
def getLangCode(filename):
  n = filename.lower()
  # Todo sort which words have the highest
  # matches instead of winner take all
  if (similar("english.srt", n) > 0.9):
    print("matched whole word", n)
    return "eng"
  if (similar("_eng.srt", n) > 0.75):
    print("matched partial word", n)
    return "eng"
  if ('english' in n or 'eng' in n):
    print("matched in string compare", n)
    return "eng"
  # Add other language codes here if you like
  return None

# Get the parent folder name as the fallback option!
workingDirBasename = basename(workingDir)

# Check that a file with this name actually exists in the folder
def filter_movie_extensions(filepath):
  exts = [".mp4" , ".mkv", ".mov"]
  return os.path.splitext(filepath)[1] in exts

# Check if a file with the parent dir name in
# the title and a video file extension afterwards.
#
# e.g. for checkedName = "AVENGERS.1080p"
# "C/dir/to/movie/AVENGERS.1080p/" and a
# "C/dir/to/movie/AVENGERS.1080p/AVENGERS.1080p.mp4"
# right afterwards
def does_working_dir_contains_matching_media(checkedName):
  movieSeemingFiles = filter(filter_movie_extensions, glob(workingDir + "/" + checkedName + ".*"))
  return len(list(movieSeemingFiles)) > 0

def doFileCopy(oldFile, newFile):
  print (".")
  print("performing copy")
  print (oldFile)
  print ("------>")
  print (newFile)
  print (".")
  shutil.copyfile(oldFile, newFile)

def multipleSubs(subs, subsPath, lCode):
  # Logic for mutiple subtitles
  if (len(subs) == 3):
    print("3 Subtitles found")
    doFileCopy(subsPath[0], subs[0] + lCode + ".forced" + ".srt")
    doFileCopy(subsPath[1], subs[1] + lCode + ".srt")
    doFileCopy(subsPath[2], subs[2] + lCode + ".sdh" + ".srt")
  elif (len(subs) == 2):
    print("2 Subtitles found")
    # Compare the file size if <= 20kb assume as forced
    if (os.path.getsize(subsPath[0]) <= 20000):
      print("Forced Subtitles found")
      doFileCopy(subsPath[0], subs[0] + lCode + ".forced" + ".srt")
      doFileCopy(subsPath[1], subs[1] + lCode + ".srt")
    else:
      print("SDH Subtitles found")
      doFileCopy(subsPath[0], subs[0] + lCode + ".srt")
      doFileCopy(subsPath[1], subs[1] + lCode + ".sdh" + ".srt")
  elif (len(subs) == 1):
    print("1 Subtitle found")
    # Compare the file size if <= 20kb assume as forced
    if (os.path.getsize(subsPath[0]) <= 20000):
      doFileCopy(subsPath[0], subs[0] + lCode + ".forced" + ".srt")
    else:
      doFileCopy(subsPath[0], subs[0] + lCode + ".srt")
  else:
    print("More than 3 Subtitles found")
    for i in range(len(subs)):
      doFileCopy(subsPath[i], subs[i] + "(" + i + ")" + lCode + ".srt")

# Fix the movie files
# C/dir/to/movie/AVENGERS.1080p/
#   AVENGERS.1080p.mp4
#   Subs/
#       2_English.srt

# Create a Subtitle List to hold the files we want to keep.
subtitles = []
subtitlesPath = []
if (does_working_dir_contains_matching_media(workingDirBasename)):
  for filePath in movieFiles:
    print("on movie file", filePath)
    movieBaseName = basename(filePath)
    langCode = getLangCode(movieBaseName)
    if (langCode is None):
      print("Can't determine language code for =>", movieBaseName)
      continue
    # Add to list
    subtitles.append(join(workingDir, workingDirBasename + "."))
    subtitlesPath.append(filePath)
    
  # Send lists to sub logic function
  multipleSubs(subtitles, subtitlesPath, langCode)
else:
  print("This is not a movie directory", workingDir)

# Files that are 2 layers deep
showFiles = glob(subsDir + "/**/*.srt")

# Fix the TV show files
# C/dir/to/show/PENTHOUSE.1080p/
#   PENTHOUSE.S01E01.1080p.mp4
#   Subs/
#     PENTHOUSE.S01E01.1080p/
#       2_English.srt

# Dictionary to combine subtitles based on directory.
subtitleDict = {}
subtitlePathDict = {}
# Create a Subtitle List to hold the files based on their directory.
showSubtitles = []
showSubtitlesPath = []
for filePath in showFiles:
  showBaseName = basename(filePath)
  langCode = getLangCode(showBaseName)
  if (langCode is None):
    # print("Can't determine language code for =>", showBaseName)
    continue
  print("on show file", filePath)
  
  # Do a media match check
  episodeName = basename(os.path.dirname(filePath))
  print("episodeName", episodeName)
  if (not does_working_dir_contains_matching_media(episodeName)):
    print("no media found for episode", episodeName, "in workingDir", workingDir)
    continue

  # Add to dictionary to combine files based on directory
  if episodeName in subtitleDict:
    # append the new number to the existing array at this slot
    subtitleDict[episodeName].append(join(workingDir, episodeName + "."))
    subtitlePathDict[episodeName].append(filePath)
  else:
    # create a new array in this slot
    subtitleDict[episodeName] = [join(workingDir, episodeName + ".")]
    subtitlePathDict[episodeName] = [filePath]
    
# Loop through the two dictionaries to place subtitles into list based on the directory they are in
for x, x1 in zip(subtitleDict, subtitlePathDict):
  for y, y1 in zip(subtitleDict[x], subtitlePathDict[x1]):
    showSubtitles.append(y)
    showSubtitlesPath.append(y1)
    
  # Send lists to sub logic function
  multipleSubs(showSubtitles, showSubtitlesPath, langCode)
  # Clear lists for next dir subtitles
  showSubtitles.clear()
  showSubtitlesPath.clear()

