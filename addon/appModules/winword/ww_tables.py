# appModules\winword\ww_tables.py
#A part of wordAccessEnhancement add-on
#Copyright (C) 2019 paulber19
#This file is covered by the GNU General Public License.


import addonHandler
addonHandler.initTranslation()
from logHandler import log
import config
import api
import wx
import gui
import ui
import speech
from NVDAObjects.window.winword import WordDocument
import time
from .ww_wdConst import wdActiveEndPageNumber , wdFirstCharacterLineNumber , wdGoToTable
from .ww_collection import Collection, CollectionElement,ReportDialog
import sys
import os
_curAddon = addonHandler.getCodeAddon()
path = os.path.join(_curAddon.path, "shared")
sys.path.append(path)
from ww_utils  import printDebug
del sys.path[-1]

class Table(CollectionElement):
	_rowPositions = {"nextInRow": "next", "previousInRow": "previous", "firstInRow": "first", "lastInRow": "last", "current": "current"}
	_columnPositions = {"nextInColumn": "next", "previousInColumn": "previous", "firstInColumn": "first", "lastInColumn": "last", "current": "current"}
	
	def __init__(self, parent, item):
		super(Table, self).__init__(parent, item)
		self.columnsCount = item.Columns.Count
		self.rowsCount = item.Rows.Count
		self.range = item.Range
		self.title = ""
		self.uniform = item.uniform
		self.start = item.range.Start
		r = self.parent.doc.range (self.start, self.start)
		self.line = r.information(wdFirstCharacterLineNumber )
		self.page = r.Information(wdActiveEndPageNumber )
	
	def formatInfos(self):
		sInfo = _("""Page {page}, line {line}
Title: {title}
Number of rows: {rowsCount}
Number of columns: {columnsCount}
""")
		sInfo = sInfo.replace("\n", "\r\n")
		return sInfo.format(page =self.page, line= self.line, title= self.title, rowsCount = self.rowsCount, columnsCount = self.columnsCount)
	
	def getMoveInRow(self, position):
		if position == "current": return None
		if position in self._rowPositions:
			return True
		elif position in self._columnPositions:
			return False
		return None
	def _getCellIndexInCollection(self, cell, collection):
		for i in range(0, len(collection)):
			element= collection[i]
			if (element.rowIndex == cell.rowIndex) and (element.columnIndex == cell.columnIndex):
				return i
		return None
	
	def moveToCell(self, position, curCell ):
		(rowIndex, columnIndex) = (curCell.rowIndex, curCell.columnIndex)
		printDebug ("moveToCell: position = %s, rowIndex: %s, columnIndex= %s"%(position, rowIndex, columnIndex))
		if  position in self._rowPositions:
			cells = self._getCellsOfRow(rowIndex)
			newCell = self._getCellInCollection(cells, self._rowPositions[position], self._getCellIndexInCollection(curCell, cells))
			if newCell is None or newCell.columnIndex  == columnIndex:
				ui.message(_("Row's limit"))
				newCell = None
		elif position in self._columnPositions:
			cells = self._getCellsOfColumn(columnIndex)
			newCell = self._getCellInCollection(cells, self._columnPositions[position], self._getCellIndexInCollection(curCell, cells))
			if newCell is None or newCell.rowIndex  == rowIndex:
				ui.message(_("Column's limit"))
				newCell = None
		else:
			# error
			log.warning("moveToCell error: %s, %s"%(type, whichOne))
			return None
		if newCell == None:
			return None
		newCell.goTo()
		return newCell
	
	
	def _getCellInCollection(self, cells, position, index):
		printDebug ("_getCellInCollection: position= %s"%position)
		try:
			if position == "previous":
				cell = cells[index-1 if index>0 else None]
			elif position == "next":
				cell = cells[index+1 if index+1 <len(cells) else None]
			elif position == "first":
				cell = cells[0]
			elif position == "last":
				cell = cells[-1]
			elif position == "current":
				cell = cells[index]
			else:
				# error
				cell = None
		except:
			cell = None
		return cell
		
	def _getCellsOfRow(self, rowIndex):
		cells = []
		for i in range(1, self.columnsCount+1):

			try:
				cell = self.obj.cell(rowIndex, i)

			except:
				continue
			cells.append(Cell(self, cell))

		return cells
	


	def _getCellsOfColumn (self, columnIndex):
		cells = []
		for i in range(1, self.rowsCount+1):
			try:
				cell = self.obj.cell(i, columnIndex)

			except:
				continue
			cells.append(Cell(self, cell))



		return cells



	def sayElement(self, elementType, position, currentCell, reportAllCells = False):
		printDebug ("sayElement: %s, %s, reportAllCells = %s"%(elementType, position, reportAllCells))
		if elementType == "row":
			self.sayRow(self._rowPositions[position], currentCell)
		elif elementType == "column":
			self.sayColumn(self._columnPositions[position], currentCell)
		elif elementType == "cell":
			if reportAllCells:
				if position in self._rowPositions:
					pos = self._rowPositions[position]
					self.sayColumn(pos, currentCell)
				elif position in self._columnPositions:
					pos = self._columnPositions[position]
					self.sayRow(pos, currentCell)
			else:
				self.sayCell(position, currentCell)
		else:
			# error
			log.error("SayElement invalid parameters %s" %type)

	def sayCell(self,  position= "current", currentCell = None,columnHeader = None ):
		printDebug ("sayCell: position= %s,   columnHeader = %s, row= %s, column=%s"%(position, columnHeader, currentCell.rowIndex, currentCell.columnIndex))
		newCell = None
		row = None
		if position == "current":
			currentCell.sayText(self.parent, columnHeader)
			return
		
		if position in self._rowPositions:
			cells = self._getCellsOfRow(currentCell.rowIndex)
			row = True
			pos = self._rowPositions[position]
		elif  position in self._columnPositions:
			cells = self._getCellsOfColumn(currentCell.columnIndex)
			row = False
			pos = self._columnPositions[position]
		else:
			#error
			log.error ("error, sayCell invalid parameter %s" %whichOne)
			return
		
		if newCell is None:
			index = self._getCellIndexInCollection(currentCell, cells)
			newCell = self._getCellInCollection(cells, pos, index)
			if newCell is None:
				if row is None:
					pass
				elif row:
					ui.message(_("Row's limit"))
				else:
					ui.message(_("Column's limit"))
				return
			if row is True:
				ui.message(_("column %s") %newCell.columnIndex)
			elif row is False:
				ui.message(_("row %s") %newCell.rowIndex)
			newCell.sayText(self.parent, columnHeader = row if columnHeader is None else columnHeader)

	def sayRow(self, position, currentCell):
		cells = self._getCellsOfColumn(currentCell.columnIndex)
		index = self._getCellIndexInCollection(currentCell, cells)
		cell = self._getCellInCollection(cells, position, index)
		if cell is None:
			ui.message(_("Column's limit"))
			return
		cells = self._getCellsOfRow(cell.rowIndex)
		ui.message(_("row %s") %cell.rowIndex)
		for cell in cells:
			time.sleep(0.01)
			self.sayCell("current", cell, columnHeader = True)
	
	def sayColumn (self, position, currentCell):
		cells = self._getCellsOfRow(currentCell.rowIndex)
		index = self._getCellIndexInCollection(currentCell, cells)
		cell = self._getCellInCollection(cells, position, index)
		if cell is None:
			ui.message(_("Row's limit"))
			return
		ui.message(_("column %s") %cell.columnIndex)
		cells = self._getCellsOfColumn(cell.columnIndex)
		for cell in cells:
			time.sleep(0.01)
			self.sayCell("current", cell, columnHeader = False)


class Tables(Collection):
	_propertyName = (("Tables",Table),)
	_name = (_("Table"), _("Tables"))
	_wdGoToItem = wdGoToTable
	def __init__(self, parent, obj, rangeType):
		self.rangeType = rangeType
		self.dialogClass = TablesDialog
		self.noElement = _("No table")
		super(Tables, self).__init__( parent, obj)
		
class TablesDialog(ReportDialog):

	def __init__(self, parent,obj ):
		super(TablesDialog, self).__init__(parent,obj)
		
	def initializeGUI (self):
		self.lcLabel = _("Tables")
		self.lcColumns = (
			(_("Table"), 100),
			(_("Location"),150),
			(_("Title"),300),
			(_("Number of rows"),100) ,
			(_("Number of columns"),100)
			)
		lcWidth = 0
		for column in self.lcColumns:
			lcWidth = lcWidth + column[1]
			
		self.lcSize = (lcWidth, self._defaultLCWidth)
		
		self.buttons = (
			(100, _("&Go to"),self.goTo),
			(101, _("&Delete"), self.delete),
			)


		self.tc1 = None
		self.tc2 = None



	def get_lcColumnsDatas(self, element):
		location = (_("Page {page}, line {line}")).format(page = element.page, line= element.line)
		index = self.collection.index(element)+1

		datas = (index,location, element.title, element.rowsCount, element.columnsCount)
		return datas



class Cell(CollectionElement):
	def __init__(self, parent,item ):
		super(Cell, self).__init__(parent, item)
		self.wordDocument = self.parent.parent
		self.columnIndex = item.ColumnIndex
		self.rowIndex = item.RowIndex
		"""
		self.height = item.Height
		self.width = item.Width
		self.heightRule = item.HeightRule #wdRowHeightRule
		self.nestingLevel = item.NestingLevel
		self.next = item.Next
		self.previous = item.Previous
		"""
		self.range = item.Range
		self.start = self.range.Start
		#self.tables = item.Tables
	
	def sayText (self, wordDocument, columnHeader= None):
		printDebug ("cell setText: columnHeader= %s"%columnHeader)
		headerText = ""
		reportTableHeadersFlag = config.conf['documentFormatting']["reportTableHeaders"]
		if reportTableHeadersFlag:
			if columnHeader is not None:
				headerText=wordDocument.fetchAssociatedHeaderCellText(self.obj,columnHeader)
			else:
				columnHeaderText=wordDocument.fetchAssociatedHeaderCellText(self.obj,columnHeader = True)
				rowHeaderText=wordDocument.fetchAssociatedHeaderCellText(self.obj,columnHeader = False)
				headerText = "%s, %s"%(rowHeaderText, columnHeaderText)
			ui.message(headerText)
		text = self.obj.Range.Text
		text = text[:-2]
		if text != "":
			ui.message(text)
		else:
			ui.message(_("empty"))

	def moveToCell(self, type, whichOne ):
		row = Row(self, self.row)
		column = Column(self, self.column)
		if type == "row":
			if (whichOne in ["first", "previous"] and column.isFirst) or (whichOne in ["last", "next"] and column.isLast):
				#table's limit
				ui.message(_("table's limit"))
				return False
			newCell = row.getCell(whichOne, self.columnIndex)
		elif type == "column":
			if (whichOne in  ["first", "previous"] and row.isFirst) or (whichOne in ["last", "next"] and row.isLast):
				#table's limit
				ui.message(_("table's limit"))
				return False
			# move cell in column
			newCell = column.getCell(whichOne, self.rowIndex)
		else:
			# error
			log.error("moveToCell: invalid parameter %s" %type)
		if newCell:
			newCell.goTo()
			return newCell
		return False
