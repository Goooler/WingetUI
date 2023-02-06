import sys
import json
import os
import time

try:
    apikey = open("APIKEY.txt", "r").read()
    print("  API key found in APIKEY.txt")
except FileNotFoundError:
    apikey = os.environ.get("TOLGEE_KEY", "")
    if (apikey == ""):
        apikey = input("Write api key and press enter: ")

os.chdir(os.path.dirname(__file__) + "/..") # move to root project

sys.path.append("wingetui")

from lang.lang_tools import *

# Update contributors
os.system(f"python scripts/get_contributors.py")

countOfChanges = len(os.popen("git status -s").readlines())

isAutoCommit = False
isSomeChanges = False

if len(sys.argv)>1:
    if (sys.argv[1] == "--autocommit"):
        isAutoCommit = True
    else:
        print("nocommit")
        print(sys.argv[1])


apiurl = f"https://app.tolgee.io/v2/projects/1205/export?format=JSON&structureDelimiter=&filterState=UNTRANSLATED&filterState=TRANSLATED&filterState=REVIEWED&zip=true"

try:
    import requests
except ImportError:
    os.system("pip install requests")
    import requests
import glob, zipfile

os.chdir("wingetui/lang")

print()
print("-------------------------------------------------------")
print()
print("  Downloading updated translations...")


response = requests.get(apiurl, headers={"X-API-Key": apikey})
if (not response.ok):
    statusCode = response.status_code
    print(f"  Error {statusCode}: {response.text}")
    if (statusCode == 403):
        print(f"  APIKEY is probably wrong!")
    exit(1)
f = open("langs.zip", "wb")
f.write(response.content)
langArchiveName = f.name
f.close()


print("  Download complete!")
print()
print("-------------------------------------------------------")
print()
print("  Extracting language files...")



downloadedLanguages = []
zip_file = zipfile.ZipFile(langArchiveName)

for file in glob.glob('lang_*.json'): # If the downloaded zip file is valid, delete old language files and extract the new ones
    os.remove(file)

for name in zip_file.namelist():
    lang = os.path.splitext(name)[0]
    if (lang in languageRemap):
        lang = languageRemap[lang]
    newFilename = f"lang_{lang}.json"
    downloadedLanguages.append(lang)

    try:
        zip_file.extract(name, "./")
        os.replace(name, newFilename)

        print(f"  Extracted {newFilename}")
    except KeyError as e:
        print(type(name))
        f = input(f"  The file {name} was not expected to be in here. Please write the name for the file. It should follow the following structure: lang_[CODE].json: ")
        zip_file.extract(f, "./")
        os.replace(f, newFilename)
        print(f"  Extracted {f}")
zip_file.close()
downloadedLanguages.sort()
os.remove("langs.zip")


print("  Process complete!")
print()
print("-------------------------------------------------------")
print()
print("  Generating translations file...")


langPerc = {}
langCredits = {}

for lang in downloadedLanguages:
    f = open(f"lang_{lang}.json", "r", encoding='utf-8')
    data = json.load(f)
    f.close()
    c = 0
    a = 0
    for key, value in data.items():
        c += 1
        if (value != None):
            a += 1
    credits = []
    try:
        credits = getTranslatorsFromCredits(data["{0} {0} {0} Contributors, please add your names/usernames separated by comas (for credit purposes)"])
    except KeyError as e:
        print(e)
        print("Can't get translator list!")
    langCredits[lang] = credits
    perc = "{:.0%}".format(a / c)
    if (perc == "100%" or lang == "en"):
        continue
    langPerc[lang] = perc

if (isAutoCommit):
    os.system("git add .")
countOfChanges = len(os.popen("git status -s").readlines()) - countOfChanges
isSomeChanges = True if countOfChanges > 0 else False

outputString = f"""
# Autogenerated file, do not modify it!!!

untranslatedPercentage = {json.dumps(langPerc, indent=2, ensure_ascii=False)}

languageCredits = {json.dumps(langCredits, indent=2, ensure_ascii=False)}
"""

f = open(f"../data/translations.py", "w", encoding="utf-8")
f.write(outputString.strip())
f.close()


print("  Process complete!")
print()
print("-------------------------------------------------------")
print()
print("  Updating README.md...")


# Generate language table
readmeFilename = "../../README.md"

f = open(readmeFilename, "r+", encoding="utf-8")
skip = False
data = ""
for line in f.readlines():
    if (line.startswith("<!-- Autogenerated translations -->")):
        data += line + getMarkdownSupportLangs() + "\nLast updated: "+str(time.ctime(time.time()))+"\n"
        print("  Text modified")
        skip = True
    if (line.startswith("<!-- END Autogenerated translations -->")):
        skip = False
    if (not skip): data += line
if (isSomeChanges):
    f.seek(0)
    f.write(data)
    f.truncate()
f.close()


print("  Process complete!")
print()
print("-------------------------------------------------------")
print()

if (isAutoCommit):
    if (not isSomeChanges):
        os.system("git reset --hard") # prevent clean
else:
    os.system("pause")
