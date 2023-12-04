import sys, random
from PyQt5.QtWidgets import QMainWindow, QFrame, QDesktopWidget, QApplication, QHBoxLayout, QLabel
from PyQt5.QtCore import Qt, QBasicTimer, pyqtSignal
from PyQt5.QtGui import QPainter, QColor, QPen

from tetris import BOARD_DATA, BOARD2_DATA, Shape
from ai import TETRIS_AI

class Tetris(QMainWindow):
    def __init__(self):
        super().__init__()

        # Player 1
        self.isStarted = False
        self.isPaused = False
        self.nextMove = None
        self.lastShape = Shape.shapeNone

        # Player 2
        self.isStarted2 = False
        self.isPaused2 = False
        self.nextMove2 = None
        self.lastShape2 = Shape.shapeNone

        self.initUI()

    def initUI(self):
        # Universal
        self.gridSize = 22
        self.speed = 10
        self.timer = QBasicTimer()
        self.setFocusPolicy(Qt.StrongFocus)
        hLayout = QHBoxLayout()

        # Player 1
        self.tboard = Board(self, self.gridSize)
        hLayout.addWidget(self.tboard)
        self.sidePanel = SidePanel(self, self.gridSize)
        hLayout.addWidget(self.sidePanel)
        self.statusbar = self.statusBar()
        self.tboard.msg2Statusbar[str].connect(self.statusbar.showMessage)

        # Player 2
        self.tboard2 = Board2(self, self.gridSize)
        hLayout.addWidget(self.tboard2)
        self.sidePanel2 = SidePanel2(self, self.gridSize)
        hLayout.addWidget(self.sidePanel2)
        self.statusbar2 = self.statusBar()
        self.tboard2.msg2Statusbar[str].connect(self.statusbar2.showMessage)

        # Universal
        self.start()

        self.center()
        self.setWindowTitle('Multiplayer Tetris')
        self.show()

        self.setFixedSize(2*(self.tboard.width() + self.sidePanel.width()),
                          self.sidePanel.height() + self.statusbar.height())

    def center(self):
        # Universal
        screen = QDesktopWidget().screenGeometry()
        size = self.geometry()
        self.move((screen.width() - size.width()) // 2, (screen.height() - size.height()) // 2)

    def start(self):
        # TODO: Make concurrent

        # Player 1
        if self.isPaused:
            return
        self.isStarted = True
        self.tboard.score = 0
        BOARD_DATA.clear()
        #self.tboard.msg2Statusbar.emit(str(self.tboard.score))
        BOARD_DATA.createNewPiece()

        # Player 2
        if self.isPaused2:
            return
        self.isStarted2 = True
        self.tboard2.score = 0
        BOARD2_DATA.clear()
        self.tboard.msg2Statusbar.emit(str(self.tboard.score) + " vs " + str(self.tboard2.score))
        BOARD2_DATA.createNewPiece()

        # Universal
        self.timer.start(self.speed, self)

    def updateWindow(self):
        self.tboard.updateData()
        self.sidePanel.updateData()
        self.tboard2.updateData()
        self.sidePanel2.updateData()
        self.update()

    def timerEvent(self, event):
        if BOARD_DATA.winner == None:

            if event.timerId() == self.timer.timerId():
                # Player 1
                if TETRIS_AI and not self.nextMove:
                    self.nextMove = TETRIS_AI.nextMove()
                if self.nextMove:
                    k = 0
                    while BOARD_DATA.currentDirection != self.nextMove[0] and k < 4:
                        BOARD_DATA.rotateRight()
                        k += 1
                    k = 0
                    while BOARD_DATA.currentX != self.nextMove[1] and k < 5:
                        if BOARD_DATA.currentX > self.nextMove[1]:
                            BOARD_DATA.moveLeft()
                        elif BOARD_DATA.currentX < self.nextMove[1]:
                            BOARD_DATA.moveRight()
                        k += 1
                lines = BOARD_DATA.moveDown()
                if lines >= 1:
                    BOARD_DATA.sabotage(lines)
                self.tboard.score += lines
                if self.lastShape != BOARD_DATA.currentShape:
                    self.nextMove = None
                    self.lastShape = BOARD_DATA.currentShape

                # Player 2
                if TETRIS_AI and not self.nextMove2:
                    self.nextMove2 = TETRIS_AI.nextMove2()
                if self.nextMove2:
                    k = 0
                    while BOARD2_DATA.currentDirection != self.nextMove2[0] and k < 4:
                        BOARD2_DATA.rotateRight()
                        k += 1
                    k = 0
                    while BOARD2_DATA.currentX != self.nextMove2[1] and k < 5:
                        if BOARD2_DATA.currentX > self.nextMove2[1]:
                            BOARD2_DATA.moveLeft()
                        elif BOARD2_DATA.currentX < self.nextMove2[1]:
                            BOARD2_DATA.moveRight()
                        k += 1
                lines = BOARD2_DATA.moveDown()
                self.tboard2.score += lines
                if lines >= 1:
                    BOARD2_DATA.sabotage(lines)
                if self.lastShape2 != BOARD2_DATA.currentShape:
                    self.nextMove2 = None
                    self.lastShape2 = BOARD2_DATA.currentShape

                # Universal
                self.updateWindow()
            else:
                super(Tetris, self).timerEvent(event)
        else:
            print("Winner")

def drawSquare(painter, x, y, val, s):
    colorTable = [0x000000, 0xCC6666, 0x66CC66, 0x6666CC,
                  0xCCCC66, 0xCC66CC, 0x66CCCC, 0xDAAA00, 0x555555]

    if val == 0:
        return

    color = QColor(colorTable[val])
    painter.fillRect(x + 1, y + 1, s - 2, s - 2, color)

    painter.setPen(color.lighter())
    painter.drawLine(x, y + s - 1, x, y)
    painter.drawLine(x, y, x + s - 1, y)

    painter.setPen(color.darker())
    painter.drawLine(x + 1, y + s - 1, x + s - 1, y + s - 1)
    painter.drawLine(x + s - 1, y + s - 1, x + s - 1, y + 1)


class SidePanel(QFrame):
    def __init__(self, parent, gridSize):
        super().__init__(parent)
        # Universal
        self.setFixedSize(gridSize * 5,gridSize * BOARD_DATA.height)
        self.move(gridSize * BOARD_DATA.width, 0)
        self.gridSize = gridSize

    def updateData(self):
        self.update()

    def paintEvent(self, event):
        # Universal
        painter = QPainter(self)

        # Player 1
        minX, maxX, minY, maxY = BOARD_DATA.nextShape.getBoundingOffsets(0)

        dy = 3 * self.gridSize
        dx = (self.width() - (maxX - minX) * self.gridSize) / 2

        val = BOARD_DATA.nextShape.shape
        for x, y in BOARD_DATA.nextShape.getCoords(0, 0, -minY):
            drawSquare(painter, x * self.gridSize + dx, y * self.gridSize + dy, val, self.gridSize)

        # Draw line
        painter.setPen(QPen(QColor(0x777777), 8))
        painter.drawLine(self.width() - 1, 0, self.width() - 1, self.height())
        painter.setPen(QPen(QColor(0x777777), 8)) 
        painter.drawLine(self.width(), 0, self.width(), self.height())

class SidePanel2(QFrame):
    def __init__(self, parent, gridSize):
        super().__init__(parent)
        # Universal
        self.setFixedSize(gridSize * 5,gridSize * BOARD2_DATA.height)
        self.move(gridSize * BOARD2_DATA.width * 2 + gridSize * 5, 0)
        self.gridSize = gridSize

    def updateData(self):
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        minX, maxX, minY, maxY = BOARD2_DATA.nextShape.getBoundingOffsets(0)
        dy = 3 * self.gridSize
        dx = (self.width() - (maxX - minX) * self.gridSize) / 2
        val = BOARD2_DATA.nextShape.shape
        for x, y in BOARD2_DATA.nextShape.getCoords(0, 0, -minY):
            drawSquare(painter, x * self.gridSize + dx, y * self.gridSize + dy, val, self.gridSize)


class Board(QFrame):
    msg2Statusbar = pyqtSignal(str) # Player 1
    speed = 10

    def __init__(self, parent, gridSize):
        super().__init__(parent)
        self.setFixedSize(gridSize * BOARD_DATA.width, gridSize * BOARD_DATA.height)
        self.gridSize = gridSize
        self.initBoard()

    def initBoard(self):
        # Player 1
        self.score = 0
        BOARD_DATA.clear()

    def paintEvent(self, event):
        painter = QPainter(self)
        # Draw backboard
        for x in range(BOARD_DATA.width):
            for y in range(BOARD_DATA.height):
                val = BOARD_DATA.getValue(x, y)
                drawSquare(painter, x * self.gridSize, y * self.gridSize, val, self.gridSize)
        # Draw current shape
        for x, y in BOARD_DATA.getCurrentShapeCoord():
            val = BOARD_DATA.currentShape.shape
            drawSquare(painter, x * self.gridSize, y * self.gridSize, val, self.gridSize)
        # Draw a border
        painter.setPen(QColor(0x777777))
        painter.drawLine(self.width()-1, 0, self.width()-1, self.height())
        painter.setPen(QColor(0xCCCCCC))
        painter.drawLine(self.width(), 0, self.width(), self.height())

    def updateData(self):
        self.msg2Statusbar.emit(str(self.tboard.score) + " vs " + str(self.tboard2.score))
        self.update()


class Board2(QFrame):
    msg2Statusbar = pyqtSignal(str)
    speed = 10

    def __init__(self, parent, gridSize):
        super().__init__(parent)
        self.setFixedSize(gridSize * BOARD_DATA.width, gridSize * BOARD_DATA.height)
        self.move(gridSize * BOARD2_DATA.width + gridSize * 5, 0)
        self.gridSize = gridSize
        self.initBoard()

    def initBoard(self):
        self.score2 = 0
        BOARD2_DATA.clear()

    def paintEvent(self, event):
        painter = QPainter(self)
        # Draw backboard
        for x in range(BOARD2_DATA.width):
            for y in range(BOARD2_DATA.height):
                val = BOARD2_DATA.getValue(x, y)
                drawSquare(painter, x * self.gridSize, y * self.gridSize, val, self.gridSize)
        # Draw current shape
        for x, y in BOARD2_DATA.getCurrentShapeCoord():
            val = BOARD2_DATA.currentShape.shape
            drawSquare(painter, x * self.gridSize, y * self.gridSize, val, self.gridSize)
        # Draw a border
        painter.setPen(QColor(0x777777))
        painter.drawLine(self.width()-1, 0, self.width()-1, self.height())
        painter.setPen(QColor(0xCCCCCC))
        painter.drawLine(self.width(), 0, self.width(), self.height())

    def updateData(self):
        self.msg2Statusbar.emit(str(self.score))
        self.update()


if __name__ == '__main__':
    # random.seed(32)
    app = QApplication([])
    tetris = Tetris()
    sys.exit(app.exec_())
