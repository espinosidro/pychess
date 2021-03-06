import tkinter
from tkinter import filedialog, messagebox, Tk, Menu
from PIL import Image, ImageTk, ImageOps

###variables
master = Tk()

size = 800
divisions = 8
partition = size / divisions

pieceList = []
selectedPiece = None #piece that drew last
tileList = [] #list of tiles the last piece drew

tempTile = None #marked tile when nothing clicked

game = True #did somebody lose?

gameCache = [] #keep state of turns in memory

turn = "white"
oppositeTurn = "black"

debug = True

"""
colorPallete = {
    "bg": "peach puff",
    "tiles": "coral",
    "temp": "red",
    "mark": "yellow",
    "attack": "red"
}
"""
colorPallete = {
    "bg": "dark turquoise",
    "tile": "steel blue",
    "temp": "purple",
    "mark": "lawn green",
    "attack": "?"
}

###classes
class Piece:
    def __init__(self, column, row, side, piece):
        self.column = column
        self.row = row
        self.side = side
        self.tkobject = None #drawing of the piece itself
        self.loadSprite(piece)
        self.type = piece
        self.tilesToDraw = []

        self.map = [[None for row in range(divisions)] for column in range(divisions)]

    def loadSprite(self, piece):
        temp = Image.open("sprites/" + piece + "-" + self.side + ".png")
        offset = partition / 10
        temp.thumbnail((partition-offset,partition- offset))
        self.sprite = ImageTk.PhotoImage(temp)

    #run at the begining of every turn
    def update(self):
        pass

    #run everytime you want to draw yourself
    def draw(self):
        #draw itself
        canvas.delete(self.tkobject)
        x = partition * self.column + partition / 2
        y = partition * self.row + partition/ 2
        self.tkobject = canvas.create_image(x, y, image=self.sprite)

    def move(self, column, row):
        cacheGame() #snapshot the game before moving

        #kill any other piece on the tile
        piece = positionToPiece(column, row, oppositeTurn)
        if(piece):
            piece.delete()

        #move to tile
        self.column = column
        self.row = row
        self.draw()
        deleteTiles()
    
    def delete(self):
        #remove reference
        index = None
        for i in range(len(pieceList)):
            if pieceList[i].tkobject == self.tkobject:
                index = i
        pieceList.pop(index)
        #remove drawing
        canvas.delete(self.tkobject)
    
    #creates straight line in direction [column, row]
    def lineMark(self, directions):
        for dir in directions:
            column = self.column + dir[0]
            row = self.row + dir[1]
            while(True):
                if(Piece.tryMark(self, column, row) == False):
                    break
                else:
                    column += dir[0]
                    row += dir[1]

    #marks a tile if there is nothing or an enemy
    #returns false if it hits something that cannot be continued in a line
    #(an ally or enemy)
    def tryMark(self,column, row):
        if(column > 7 or row > 7 or column < 0 or row < 0): #out of bounds
            return False

        piece = positionToPiece(column, row)
        if(piece == False):
            self.mapTile(column, row)
        elif(piece.side == oppositeTurn):
            self.mapTile(column, row)
            return False
        else:
            return False

    def mapTile(self, column, row, color = colorPallete["mark"]): #mark a tile as possible to move
        self.tilesToDraw.append((column, row, color))
        self.map[column][row] = (column, row, color)

    def drawTiles(self): #draw the tiles where movement is possible
        for tile in self.tilesToDraw:
            x = partition * tile[0]
            y = partition * tile[1]

            tkobject = canvas.create_rectangle(x, y, x+partition, y+partition, fill=tile[2])
            tile = Tile(tile[0], tile[1], tkobject)

            tileList.append(tile)
        self.tilesToDraw.clear()

class King(Piece):
    def __init__(self, column, row, side):
        Piece.__init__(self, column, row, side, "king")
        self.hasMoved = False

    def checkCastling(self):
        def checkRook(column, row): #no need to put this function on a higher scope
            rook = positionToPiece(column, row)
            if(
                rook != False and
                rook.type == "rook" and
                rook.hasMoved == False and
                rook.side == self.side
            ):
                rook.castling = self
                return True
            return False
        
        #right:
        if(
            positionToPiece(self.column + 1, self.row) == False and
            positionToPiece(self.column + 2, self.row) == False and
            checkRook(self.column + 3, self.row) == True
        ):
            Piece.mapTile(self, self.column + 3, self.row)

        #left:
        if(
            positionToPiece(self.column - 1, self.row) == False and
            positionToPiece(self.column - 2, self.row) == False and
            positionToPiece(self.column - 3, self.row) == False and
            checkRook(self.column - 4, self.row) == True
        ):
            Piece.mapTile(self, self.column - 4, self.row)

    def checkAttack(self, column, row):
        pass
    
    def mapMovements(self):
        #movement
        for i in (-1, 0,1):
            for r in (-1,0,1):
                Piece.tryMark(self, self.column + i, self.row + r)

        #castling
        if(self.hasMoved == False):
            self.checkCastling()

    def click(self):
        self.mapMovements()
        Piece.drawTiles(self)
    
    def move(self, column, row):
        self.hasMoved = True
        Piece.move(self, column, row)

    #check at the begining of the turn if its under attack
    def update(self):
        pass

class Rook(Piece): #torre
    directions = ((1,0), (0,1), (-1,0), (0,-1))
    def __init__(self, column, row, side):
        Piece.__init__(self, column, row, side, "rook")
        self.hasMoved = False

        #helper variable for King's castling
        self.castling = None
    
    def mapMovements(self):
        if(self.hasMoved == False and self.castling != None and selectedPiece == self.castling and self.row == self.castling.row): #if the king was selected before
            cacheGame()
            if(self.castling.column > self.column): #if rook is to the left
                self.column = self.column + 3
                self.castling.column = self.column -1

            else: #if rook is to the right
                self.column = self.column -2 
                self.castling.column = self.column + 1
            self.draw()
            self.castling.draw()
            self.castling = None
            changeTurn() #change turn
            return
        else: self.castling = None
        
        Piece.lineMark(self, Rook.directions)
        
    def click(self):
        self.mapMovements()
        Piece.drawTiles(self)

    def move(self, column, row):
        self.hasMoved = True
        Piece.move(self,column, row)

class Pawn(Piece):
    def __init__(self, column, row, side):
        #standard start
        Piece.__init__(self, column, row, side, "pawn")

        #which way can this move
        if(side == "black"):
            self.direction = -1
        else: self.direction = 1

        self.hasMoved = False #allow double move on first turn

    def mapMovements(self):
        if(positionToPiece(self.column, self.row + self.direction) == False):
            Piece.mapTile(self, self.column, self.row+self.direction)
            if(self.hasMoved == False and positionToPiece(self.column, self.row + self.direction *2) == False):
                Piece.mapTile(self, self.column, self.row + self.direction *2)
        
        #mark attacks
        if(positionToPiece(self.column -1, self.row + self.direction, oppositeTurn)):
            Piece.mapTile(self, self.column -1, self.row + self.direction)
        if(positionToPiece(self.column + 1, self.row + self.direction, oppositeTurn)):
            Piece.mapTile(self, self.column + 1, self.row + self.direction)
    
    def click(self):
        self.mapMovements()
        Piece.drawTiles(self)

    def move(self, column, row):
        self.hasMoved = True
        Piece.move(self, column, row)

        #let change type when getting to the other side
        if(self.direction == 1 and self.row == 7) or (self.direction == -1 and self.row == 0):
            pieceList.append(Queen(self.column, self.row, self.side)) #just turns into a queen, not going to add an extra ui for choosing the piece...
            Piece.delete(self)

class Knight(Piece): #caballo
    moves = ((1,2), (2,1))
    def __init__(self, column, row, side):
        Piece.__init__(self, column, row, side, "knight")
    
    def mapMovements(self):
        for move in Knight.moves:
            for i in (-1, 1): 
                for r in (-1,1):
                    Piece.tryMark(self, self.column + move[0] * i, self.row + move[1] * r)
    
    def click(self):
        self.mapMovements()
        Piece.drawTiles(self)

class Bishop(Piece): #alfil
    directions = ((1,1), (-1,1), (1,-1), (-1,-1))
    def __init__(self, column, row, side):
        Piece.__init__(self, column, row, side, "bishop")

    def mapMovements(self):
        Piece.lineMark(self, Bishop.directions)

    def click(self):
        self.mapMovements()
        Piece.drawTiles(self)

class Queen(Piece):
    directions = ((1,0), (0,1), (-1,0), (0,-1), (1,1), (-1,1), (1,-1), (-1,-1))
    def __init__(self, column, row, side):
        Piece.__init__(self, column, row, side, "queen")
    
    def mapMovements(self):
        Piece.lineMark(self, Queen.directions)
    
    def click(self):
        self.mapMovements()
        Piece.drawTiles(self)

class Tile:
    def __init__(self, column, row, tkobject):
        self.column = column
        self.row = row
        self.tkobject = tkobject

###functions
#delete all pieces, turn to white
def resetGame():
    #this ones are redundant but want to make sure nothing gets away when restarting
    global selectedPiece, tempTile
    canvas.delete(tempTile)
    tempTile = None
    selectedPiece = None

    deleteTiles()
    for piece in pieceList:
        canvas.delete(piece.tkobject)
    pieceList.clear()

def newGame():
    #create pieces
    resetGame()

    global turn, oppositeTurn
    turn = "white"
    oppositeTurn = "black"

    pieceOrder = (Rook, Knight, Bishop, Queen, King, Bishop, Knight, Rook) #helper
    for i in range(0,8):
        #add pawns
        pieceList.append(Pawn(i,6, "black"))
        pieceList.append(Pawn(i,1, "white"))
        #add everything else
        pieceList.append(pieceOrder[i](i, 7, "black"))
        pieceList.append(pieceOrder[i](i, 0, "white"))
    
    cacheGame() #first state of the cache, somewhat useless but necessary to keep behaviour consistant
    drawPieces()

#load cache from disk into memory
def loadCache():
    gameCache.clear() #delete everything else
    file = filedialog.askopenfile(defaultextension=".pychess")

    if file is None:
        tkinter.messagebox.showerror("No file chosen")
        return

    lines = file.readlines()
    file.close()

    if(lines.pop(0) != "pychess-standard-file-format-version-2\n"):
        tkinter.messagebox.showerror("Invalid file format", "the file you are trying to load is not a pychess file")
        return

    newCache = ""
    for line in lines:
        newCache = newCache + line

    #print(newCache)
    gameCache.append(newCache)

#write last state of the cache to disk
def writeCache():
    file = filedialog.asksaveasfile(mode='w', defaultextension=".pychess")
    if file is None:
        tkinter.messagebox.showerror("No name entered")
        return

    #std way of saving
    file.write("pychess-standard-file-format-version-2\n")

    #write the last cache
    file.write(gameCache[-1])
    file.close()

#save the current state of the game in the memory
def cacheGame():
    newCache = ""
    for piece in pieceList:
        newCache = newCache + piece.type + " " + str(piece.column) + " " + str(piece.row) + " " + piece.side + "\n"
    newCache = newCache + "turn " + turn + " " + oppositeTurn + "\n" #turn
    newCache = newCache + "game " + str(game) #is the game still going on or did somebody win?
    gameCache.append(newCache)

#restore game from last state
def restoreCache():
    if(len(gameCache) < 1):
        return

    cache = gameCache.pop()
    cache = cache.split("\n")

    resetGame()

    for line in cache:
        temp = line.split()
        classes = {"pawn": Pawn, "rook": Rook, "knight": Knight, "bishop": Bishop, "queen": Queen,"king": King}
    
        if temp[0] in classes: #create instances from name
            pieceList.append(classes[temp[0]](int(temp[1]), int(temp[2]), temp[3]))
        elif(temp[0] == "turn"):
            global turn, oppositeTurn
            turn = temp[1]
            oppositeTurn = temp[2]
        elif temp[0] == "game":
            global game
            game = bool(temp[0])
        elif(temp[0] == "#"):
            #ignore comments, note that the marker needs to be separated by a space
            pass
        else:
            tkinter.messagebox.showerror("Invalid data", "the file you are trying to load contains invalid data")
            return
    drawPieces()

def loadGame():
    loadCache()
    restoreCache()

def printCache():
    print(gameCache[-1])

#given coordinates returns column and row
def clickToPosition(x,y):
    column, row = -1, -1
    for i in range(divisions): #column
        if(x >= partition * i and x <= partition * (i + 1)):
            column = i
    for i in range(divisions): #row
        if(y >= partition * i and y <= partition * (i+1)):
            row = i

    return column, row

#given a position returns a tile or False
def positionToTile(column, row):
    for tile in tileList:
        if(tile.column == column and tile.row == row):
            return tile
    return False

#given a position and side returns the piece or False
def positionToPiece(column, row, side = None):
    for piece in pieceList:
        if(piece.column == column and piece.row == row):
            if(side != None):
                if(piece.side == side): return piece
            else: return piece
    return False

def updatePieces():
    for piece in pieceList:
        piece.update()

def drawPieces():
    for piece in pieceList:
        piece.draw()

#delete tiles marked by any piece
def deleteTiles():
    for tile in tileList:
        canvas.delete(tile.tkobject)
    tileList.clear()

#change the turn
def changeTurn():
    global turn, oppositeTurn
    turn, oppositeTurn = oppositeTurn, turn
    deleteTiles()

    whiteKing = False
    blackKing = False

    for piece in pieceList:
        if(piece.type == "king"):
            if(piece.side == "white"):
                whiteKing = True
            elif(piece.side == "black"):
                blackKing = True
    global game
    if(whiteKing == False):
        game = "black"
    elif (blackKing == False):
        game = "white"

#draw a tile, marking what was clicked
def drawTempTile(column, row):
    global tempTile
    canvas.delete(tempTile)

    x = column * partition
    y = row * partition

    tempTile = canvas.create_rectangle(x, y, x+partition, y+partition, fill=colorPallete["temp"])

def click(event): #core game logic
    global game
    if(game != True):
        tkinter.messagebox.showinfo("Winner", "Winner: " + str(game))
        return

    updatePieces() #update pieces, pretty much exclusively for the king...

    #get click
    column, row = clickToPosition(event.x, event.y)
    drawTempTile(column, row)

    piece = positionToPiece(column, row, turn) #select piece, only allow side currently playing

    global selectedPiece
    #core logic
    if(piece): #if piece was clicked then mark tiles
        if(selectedPiece != None): #but if a piece was already selected then first clear the tiles that it marked
            deleteTiles()
        
        piece.click()
        selectedPiece = piece

    elif(positionToTile(column, row)): #if tile was clicked move to the tile, if there is a piece on the tile being moved to then kill that piece
        selectedPiece.move(column, row)
        changeTurn()
        selectedPiece = None

    else: #if nothing was clicked mark tile
        drawTempTile(column, row)
        deleteTiles()
        selectedPiece = None

    #draw pieces to have everything above potentially marked tiles
    drawPieces()

###init
##TK prepare
canvas = tkinter.Canvas(master, width=size, height=size, bg=colorPallete["bg"])
canvas.pack()

#create menu
menubar = tkinter.Menu(master) #create menu
filemenu = tkinter.Menu(menubar, tearoff=0)
filemenu.add_command(label="New Game", command=newGame)
filemenu.add_command(label="Open Game", command=loadGame)
filemenu.add_command(label="Save Game", command=writeCache)
filemenu.add_separator()
filemenu.add_command(label="Exit", command=master.quit)
menubar.add_cascade(label="File", menu=filemenu)

editmenu = tkinter.Menu(menubar, tearoff=0)
editmenu.add_command(label="Undo", command=restoreCache)
menubar.add_cascade(label="Edit", menu=editmenu)

if(debug == True):
    debugmenu = tkinter.Menu(menubar, tearoff=0)
    debugmenu.add_command(label="print cache", command=printCache)
    menubar.add_cascade(label="Debug", menu=debugmenu)

master.config(menu=menubar) #display menu

#make clicking run the "click" function that handles all the core logic
canvas.bind("<Button-1>", click)

#draw the board
for i in range(divisions): #create the lines
    canvas.create_line(0, partition * i, size, partition * i)
    canvas.create_line(partition * i, 0, partition*i, size)

for row in range(0, divisions, 2): #color the tiles
    for column in range(0, divisions, 2):
        canvas.create_rectangle(column * partition, row* partition, (column+1)*partition, (row+1)*partition, fill=colorPallete["tile"])
        canvas.create_rectangle((column+1) * partition, (row+1)* partition, (column+2)*partition, (row+2)*partition, fill=colorPallete["tile"])

newGame()

#start program
tkinter.mainloop()