#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@author: garcia.wul
@contact: garcia.wul@alibaba-inc.com
@date: 2014/06/23
"""

import os
import sqlite3
import urllib2
import shutil
import tarfile
import hashlib

from mako.template import Template
from pyquery import PyQuery

currentPath = os.path.join(os.path.dirname(os.path.realpath(__file__)))

url = "http://www.css88.com/doc/underscore/"
content = urllib2.urlopen(url).read()
jQuery = PyQuery(content)

items = jQuery("#documentation p").items()
results = []
for item in items:
    if not item.attr("id") or not item.attr("id").isalpha():
        continue
    print item.find(".header").text()
    results.append({
        "name": item.find(".header").text().strip(),
        "type": "Function",
        "path": "index.html#" + item.find(".header").text().strip()
    })

# Step 1: create the docset folder
docsetPath = os.path.join(currentPath, "underscore-zh.docset", "Contents", "Resources", "Documents")
if not os.path.exists(docsetPath):
    os.makedirs(docsetPath)

# Step 2: Copy the HTML Documentation
fin = open(os.path.join(docsetPath, "index.html"), "w")
fin.write(content)
fin.close()

# Step 3: create the Info.plist file
infoTemplate = '''<?xml version="1.0" encoding="UTF-8"?>
<plist version="1.0">
<dict>
<key>CFBundleIdentifier</key>
<string>underscore.js</string>
<key>CFBundleName</key>
<string>underscore.js</string>
<key>DocSetPlatformFamily</key>
<string>underscore.js</string>
<key>dashIndexFilePath</key>
<string>index.html</string>
<key>dashIndexFilePath</key>
<string>index.html</string>
<key>isDashDocset</key><true/>
<key>isJavaScriptEnabled</key><true/>
</dict>
</plist>'''
infoPlistFile = os.path.join(currentPath, "underscore-zh.docset", "Contents", "Info.plist")
fin = open(infoPlistFile, "w")
fin.write(infoTemplate)
fin.close()

# Step 4: Create the SQLite Index
dbFile = os.path.join(currentPath, "underscore-zh.docset", "Contents", "Resources", "docSet.dsidx")
if os.path.exists(dbFile):
    os.remove(dbFile)
db = sqlite3.connect(dbFile)
cursor = db.cursor()

try:
    cursor.execute("DROP TABLE searchIndex;")
except Exception:
    pass

cursor.execute('CREATE TABLE searchIndex(id INTEGER PRIMARY KEY, name TEXT, type TEXT, path TEXT);')
cursor.execute('CREATE UNIQUE INDEX anchor ON searchIndex (name, type, path);')

insertTemplate = Template("INSERT OR IGNORE INTO searchIndex(name, type, path) VALUES ('${name}', '${type}', '${path}');")

# Step 5: Populate the SQLite Index
for result in results:
    sql = insertTemplate.render(name = result["name"], type = result["type"], path = result["path"])
    print sql
    cursor.execute(sql)
db.commit()
db.close()

# Step 6: copy icon
shutil.copyfile(os.path.join(currentPath, "icon.png"),
    os.path.join(currentPath, "underscore-zh.docset", "icon.png"))
shutil.copyfile(os.path.join(currentPath, "icon@2x.png"),
    os.path.join(currentPath, "underscore-zh.docset", "icon@2x.png"))

# Step 7: 打包
if not os.path.exists(os.path.join(currentPath, "dist")):
    os.makedirs(os.path.join(currentPath, "dist"))
tarFile = tarfile.open(os.path.join(currentPath, "dist", "underscore-zh.tgz"), "w:gz")
for root, dirNames, fileNames in os.walk("underscore-zh.docset"):
    for fileName in fileNames:
        fullPath = os.path.join(root, fileName)
        print fullPath
        tarFile.add(fullPath)
tarFile.close()

# Step 8: 更新feed url
feedTemplate = Template('''<entry>
    <version>1.6.0</version>
    <sha1>${sha1Value}</sha1>
    <url>https://raw.githubusercontent.com/magicsky/dash-underscore-zh/master/dist/underscore-zh.tgz</url>
</entry>''')
fout = open(os.path.join(currentPath, "dist", "underscore-zh.tgz"), "rb")
sha1Value = hashlib.sha1(fout.read()).hexdigest()
fout.close()
fin = open(os.path.join(currentPath, "underscore-zh.xml"), "w")
fin.write(feedTemplate.render(sha1Value = sha1Value))
fin.close()
