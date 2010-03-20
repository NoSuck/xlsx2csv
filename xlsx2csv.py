#!/usr/bin/python

__author__ = "Dilshod Temirkhodjaev <tdilshod@gmail.com>"


import csv, datetime, zipfile, sys
import xml.parsers.expat
from xml.dom import minidom

#
# example: xlsx2csv("test.xslx", open("test.csv", "w+"))
#
def xlsx2csv(infilepath, outfile):
    writer = csv.writer(outfile, quoting=csv.QUOTE_MINIMAL)
    ziphandle = zipfile.ZipFile(infilepath)
    self.shared_strings = SharedStrings(ziphandle.read("xl/sharedStrings.xml"))

    #self.workbook = Workbook(ziphandle.read("xl/workbook.xml"))
    #for i in self.workbook.sheets:
    #    SharedStrings(ziphandle.read("xl/worksheets/sheet%s.xml" %(i['id'])))

    Sheet(self.shared_strings, ziphandle.read("xl/worksheets/sheet1.xml"), writer)
    ziphandle.close()

class Workbook(object):
    sheets = []
    def __init__(self, data):
        workbookDoc = minidom.parseString(data)
        sheets = workbookDoc.firstChild.getElementsByTagName("sheets")[0]
        for sheetNode in sheets.childNodes:
            name = sheetNode._attrs["name"].value
            id = int(sheetNode._attrs["r:id"].value[3:])
            self.sheets.append({'name': name, 'id': id})

class SharedStrings:
    parser = None
    strings = []
    si = False
    t = False
    value = ""

    def __init__(self, data):
        self.parser = xml.parsers.expat.ParserCreate()
        self.parser.CharacterDataHandler = self.handleCharData
        self.parser.StartElementHandler = self.handleStartElement
        self.parser.EndElementHandler = self.handleEndElement
        self.parser.Parse(data)

    def handleCharData(self, data):
        if self.t: self.value+= data

    def handleStartElement(self, name, attrs):
        if name == 'si':
            self.si = True
        elif name == 't' and self.si:
            self.t = True
            self.value = ""

    def handleEndElement(self, name):
        if name == 'si':
            self.si = False
            self.strings.append(self.value)
        elif name == 't':
            self.t = False

class Sheet:
    parser = None
    writer = None
    sharedString = None

    in_sheet = False
    in_row = False
    in_cell = False
    in_cell_value = False
    in_cell_formula = False

    #rows = []
    #cells = {}
    columns = {}
    rowNum = None
    colType = None
    #cellId = None
    #formula = None
    s_attr = None
    data = None

    def __init__(self, sharedString, data, writer):
        self.writer = writer
        self.sharedStrings = sharedString.strings
        self.parser = xml.parsers.expat.ParserCreate()
        self.parser.CharacterDataHandler = self.handleCharData
        self.parser.StartElementHandler = self.handleStartElement
        self.parser.EndElementHandler = self.handleEndElement
        self.parser.Parse(data)

    def handleCharData(self, data):
        if self.in_cell_value:
            if self.colType == "s":
                # shared
                self.data = self.sharedStrings[int(data)]
            #elif self.colType == "b": # boolean
            elif self.s_attr:
                if self.s_attr == '2':
                    self.data = (datetime.date(1899, 12, 30) + datetime.timedelta(float(data))).strftime("%Y-%m-%d")
                elif self.s_attr == '3':
                    self.data = str(float(data) * 24*60*60)
                elif self.s_attr == '4':
                    self.data = (datetime.datetime(1899, 12, 30) + datetime.timedelta(float(data))).strftime("%Y-%m-%d %H:%M:%S")
                else:
                    self.data = data
            else:
                self.data = data
        #elif self.in_cell_formula:
        #    self.formula = data

    def handleStartElement(self, name, attrs):
        if self.in_row and name == 'c':
            self.colType = attrs.get("t")
            self.s_attr = attrs.get("s")
            cellId = attrs.get("r")
            self.colNum = cellId[:len(cellId)-len(self.rowNum)]
            #self.formula = None
            self.data = ""
            self.in_cell = True
        elif self.in_cell and name == 'v':
            self.in_cell_value = True
        #elif self.in_cell and name == 'f':
        #    self.in_cell_formula = True
        elif self.in_sheet and name == 'row' and attrs.has_key('r'):
            self.rowNum = attrs['r']
            self.in_row = True
            self.columns = {}
        elif name == 'sheetData':
            self.in_sheet = True

    def handleEndElement(self, name):
        if self.in_cell and name == 'v':
            self.in_cell_value = False
        #elif self.in_cell and name == 'f':
        #    self.in_cell_formula = False
        elif self.in_cell and name == 'c':
            t = 0
            for i in self.colNum: t = t*26 + ord(i) - 65
            self.columns[t] = self.data
            self.in_cell = False
        if self.in_row and name == 'row':
            d = [""] * (max(self.columns.keys()) + 1)
            for k in self.columns.keys():
                d[k] = self.columns[k]
            #self.rows.append(d)
            self.writer.writerow(d)
            self.in_row = False
        elif self.in_sheet and name == 'sheetData':
            self.in_sheet = False

if __name__ == "__main__":
    if len(sys.argv) == 2:
        XLSX2CSV(sys.argv[1], sys.stdout)
    elif len(sys.argv) == 3:
        f = open(sys.argv[2], "w+")
        XLSX2CSV(sys.argv[1], f)
        f.close()
    else:
        print "Usage: xlsx2csv <infile> [<outfile>]"
