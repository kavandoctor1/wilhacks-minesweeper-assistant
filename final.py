from copy import deepcopy
import keyboard
import pyautogui
import time
import random
import sys


class MineSweeper:
    def __init__(self, SHOWFLAGS):
        self.SHOWFLAGS = SHOWFLAGS
        self.UNCLICKED = 0
        self.MINES = {}
        self.GRID = []

    #Used for debugging purposes
    def printGrid(self):
        print('Grid is: ')
        for row in [[self.GRID[i][j] for i in range(self.GRIDSIZE[0])] for j in range(self.GRIDSIZE[1])]:
            print(' '.join(row))
        print()

    #Parse the color constants
    def initColors(self,tileColors):
        self.BG = tileColors[0]
        self.ZERO = tileColors[1]
        self.tileColors = tileColors[2:]

    #Determine if two pixels are roughly equal
    def pixelsclose(self,p1,p2):
        return all(abs(p1[i]-p2[i])<10 for i in range(3))
    
    #Get the pixel location from the row and column index on the grid
    def getCenter(self,row,col):
        a = round(self.LEFTCORNER[0] + self.SCREENDIMS[0]*row/self.GRIDSIZE[0] + self.SCREENDIMS[0]/(2*self.GRIDSIZE[0]))
        b = round(self.LEFTCORNER[1] + self.SCREENDIMS[1]*col/self.GRIDSIZE[1] + self.SCREENDIMS[1]/(2*self.GRIDSIZE[1]))
        return (a,b)
    
    #Check if the user has pressed the exit keybind
    def checkexit(self):
        if keyboard.is_pressed('q'):
            print('Breaking due to \'q\' press')
            self.run()
        if keyboard.is_pressed('x'):
            print('Exiting due to \'x\' press')
            sys.exit()
    
    #Helper function that returns all adjacent cells to a given cell
    def neighboring(self,i,j):
        neighbors = []
        for x in [-1,0,1]:
            for y in [-1,0,1]:
                if (x,y) == (0,0): continue
                if 0 <= i+x < self.GRIDSIZE[0] and 0 <= j+y < self.GRIDSIZE[1]:
                    neighbors.append((i+x,j+y))
        return neighbors
    
    #Clicks on all cells that are determined to not be mines in the array nonMines
    def clickall(self,nonMines):
        for row,col in nonMines:
            a,b = self.getCenter(row,col)
            #Unflag if mistakenly flagged by user
            if (row,col) in self.markedFlags:
                pyautogui.click(a,b,button='right')
            pyautogui.click(a,b)
            self.UNCLICKED-=1
            self.checkexit()
    
    #Choose the closest flag to the user's mouse to click as a hint
    def clickone(self,nonMines):
        best = (-1,-1)  
        mind = pow(10,9)
        x,y = pyautogui.position()
        for row, col in nonMines:
            a,b = self.getCenter(row,col)
            if (x-a)**2 + (y-b)**2 < mind:
                best = (a,b)
                mind = (x-a)**2 + (y-b)**2
            if (row,col) in self.markedFlags:
                pyautogui.click(a,b,button='right')
        pyautogui.click(best)
        self.UNCLICKED-=1
            
    #Flag all mines (right click) in the array mines
    def flagall(self,mines):
        for mine in mines:
            self.MINES[mine] = True
            if mine in self.markedFlags:continue
            if self.SHOWFLAGS:
                a,b = self.getCenter(mine[0],mine[1])
                pyautogui.click(a,b,button='right')
                self.checkexit()
    
    #Recursive function to generate all possibilites (mine/nonmine) for a given set of cells
    #Only returns possibilities that are consistent with squares around it
    def gen(self,GRID,left):
        self.checkexit()
        if len(left) == 0: return [GRID]
        a,b = left.pop()
        ways = self.gen(deepcopy(GRID),deepcopy(left))
        ans = []
        nb = []
        for ax,by in self.neighboring(a,b):
            if GRID[ax][by] in '1234567':
                nb.append((ax,by))
        for w in ways:
            for poss in ['x',' ']:
                newgrid = deepcopy(w)
                newgrid[a][b] = poss
                works = True
                for i,j in nb:
                    k = int(GRID[i][j])
                    empty,mines,total = 0,0,0
                    for ix,jy in self.neighboring(i,j):
                        if newgrid[ix][jy] == ' ': empty += 1
                        elif newgrid[ix][jy] == 'x': mines += 1
                        if newgrid[ix][jy] in ' x-': total += 1
                    if mines > k or total - empty < k: works = False
                if works: ans.append(newgrid)
        return ans

    def connectedComponents(self,adj):
        #Create adjacency list for adj
        nbl = []
        for a,b in adj:

            nbs = []
            for c,d in adj:
                if (a,b) == (c,d): continue
                if abs(a-c)<=2 and abs(b-d)<=2:
                    nbs.append((c,d))
            nbl.append(nbs)
        #Use coloring algorithm to determine different connected components
        colors = [-1 for _ in range(len(adj))]
        color = 0 
        for i in range(len(adj)):
            if colors[i] == -1:
                self.dfs(adj,nbl,i,colors,color)
                color +=1
        #return the different components (different colors)
        groups = [[adj[i] for i in range(len(adj)) if colors[i] == c] for c in range(color)]
        
        print([len(group) for group in groups])
        
        return groups

    #Helper function that helps split the cells into connected components
    def dfs(self,adj,nbl,i,colors,color):
        colors[i] = color
        for nb in nbl[i]:
            if colors[adj.index(nb)]== -1:
                self.dfs(adj,nbl,adj.index(nb),colors,color)

    def getMines(self):
        mines = []
        for i in range(self.GRIDSIZE[0]):
            for j in range(self.GRIDSIZE[1]):
                cell = self.GRID[i][j]
                empty = 0
                for ix,jy in self.neighboring(i,j):
                    if self.GRID[ix][jy] not in '_1234567':
                        empty += 1
                if cell in '1234567' and int(cell) == empty:
                    for ix,jy in self.neighboring(i,j):
                        if self.GRID[ix][jy] == '-':
                            mines.append((ix,jy))
                            self.MINES[(ix,jy)] = True
        return sorted(list(set(mines)))

    def getNonMines(self):
        noMines = []
        for i in range(self.GRIDSIZE[0]):
            for j in range(self.GRIDSIZE[1]):
                cell = self.GRID[i][j]
                filled = 0
                for ix,jy in self.neighboring(i,j):
                    if self.GRID[ix][jy] == 'x':
                        filled += 1
                if cell in '1234567' and int(cell) == filled:
                    for ix,jy in self.neighboring(i,j):
                        if self.GRID[ix][jy] == '-':
                            noMines.append((ix,jy))

        return sorted(list(set(noMines)))
    
    #Returns all unclicked squares that are adjacent to a clicked square
    def unclickedToSearch(self):
        adj = []
        for i in range(self.GRIDSIZE[0]):
            for j in range(self.GRIDSIZE[1]):
                if self.GRID[i][j] == '-':
                    isadj = False
                    for ix,jy in self.neighboring(i,j):
                        if self.GRID[ix][jy] in '1234567' or self.MINES[(ix,jy)]:
                            isadj = True
                    if isadj:
                        adj.append((i,j))
        return adj
    #Clicks on a valid square as a hint for the user
    def hint(self):
        #Gets grid, and error handles
        if self.getGrid() == 'bad':
            self.paramsReady = False
            return

        #Checks if the grid has not yet been clicked on (the game has not started)
        if sum(sum(1 for c in r if c != '-') for r in self.GRID) < 3:
            a,b = self.getCenter(random.randint(1,self.GRIDSIZE[0]-1),random.randint(1,self.GRIDSIZE[1]-1))
            pyautogui.click(a,b)
            time.sleep(0.5)
            return
        
        #Finds the squares that are forced to be mines i.e. a 3 surrounded by only 3 unclicked squares
        mines = self.getMines()
        for i in range(self.GRIDSIZE[0]):
            for j in range(self.GRIDSIZE[1]):
                if self.MINES[(i,j)]: self.GRID[i][j] = 'x'

        self.printGrid()
        #Finds the squares that are forced to not be mines
        #i.e. a square adjacent to a 1, that is already adjacent to amine
        noMines = self.getNonMines()
        
        
        #If nonmine found, click on it and return
        if len(noMines) > 0:
            self.clickone(noMines)
            return
        #If all mines have been found, then click on all unclicked squares
        if self.NUMMINES == sum(1 for i in range(self.GRIDSIZE[0]) for j in range(self.GRIDSIZE[1]) if self.MINES[(i,j)]):
            self.clickall([(i,j) for i in range(self.GRIDSIZE[0]) for j in range(self.GRIDSIZE[1]) if not self.MINES[(i,j)] and self.GRID[i][j] == '-'])
            self.paramsReady = False
            return
        
        #Find all unclicked squares that are adjacent to a non-unclicked square
        adj = self.unclickedToSearch()
        
        groups = self.connectedComponents(adj)
        for group in groups:
            ways = self.gen(deepcopy(self.GRID),deepcopy(group))
            mines = []
            empty = []
            for i,j in group:
                poss = set()
                for w in ways:
                    poss.add(w[i][j])
                if len(poss) == 1: 
                    k = list(poss)[0]
                    if k == 'x':
                        mines.append((i,j))
                    else:
                        empty.append((i,j))
            if len(empty) > 0:
                self.clickone(empty)
                return
        print('Grid is unsolvable.')
        return



    def solve(self):
        while True:
            if self.getGrid() == 'bad':
                self.paramsReady = False
                return
            if sum(sum(1 for c in r if c != '-') for r in self.GRID) < 3:
                a,b = self.getCenter(random.randint(1,self.GRIDSIZE[0]-1),random.randint(1,self.GRIDSIZE[1]-1))
                pyautogui.click(a,b)
                time.sleep(0.5)
                continue
            self.printGrid()
            mines = self.getMines()
            self.flagall(mines)
            for i in range(self.GRIDSIZE[0]):
                for j in range(self.GRIDSIZE[1]):
                    if self.MINES[(i,j)]: self.GRID[i][j] = 'x'
            noMines = self.getNonMines()
            self.clickall(noMines)
            if self.NUMMINES == sum(1 for i in range(self.GRIDSIZE[0]) for j in range(self.GRIDSIZE[1]) if self.MINES[(i,j)]):
                self.clickall([(i,j) for i in range(self.GRIDSIZE[0]) for j in range(self.GRIDSIZE[1]) if not self.MINES[(i,j)] and self.GRID[i][j] == '-'])
                self.paramsReady = False
                return
            if len(noMines) > 0:
                continue
            adj = self.unclickedToSearch()
            groups = self.connectedComponents(adj)
            totalclicked = 0
            

            for group in groups:
                ways = self.gen(deepcopy(self.GRID),deepcopy(group))
                mines = []
                empty = []
                for i,j in group:
                    poss = set()
                    for w in ways:
                        poss.add(w[i][j])
                    if len(poss) == 1: 
                        k = list(poss)[0]
                        if k == 'x':
                            mines.append((i,j))
                        else:
                            empty.append((i,j))
                self.flagall(mines)
                self.clickall(empty)
                totalclicked += len(mines) + len(empty)
            if totalclicked ==  0:
                print('Grid is unsolvable.')
                break


#https://www.google.com/fbx?fbx=minesweeper

class Google(MineSweeper):

    #Gets grid level: easy, medium or hard
    def getGridParameters(self):
        s = pyautogui.screenshot()
        self.LEFTCORNER = None
        w,h = s.size
        for i in range(0,w,3):
            done = False
            for j in range(0,h,3):
                if s.getpixel((i,j)) == self.BG[0] and not self.LEFTCORNER:
                    self.LEFTCORNER = (i,j)
                if s.getpixel((i,j)) == self.BG[1]:
                    #Top left of second square (used to determine size)
                    FIRSTPUT = (i,j)
                    done = True;break
            if done: break
        for i in range(w-1,0,-3):
            done = False
            for j in range(h-1,0,-3):
                if s.getpixel((i,j)) in self.BG+self.ZERO:
                    self.RIGHTCORNER = (i,j)
                    done = True;break
            if done: break
        #If there is no Left Corner, then the user is not on the correct website
        if self.LEFTCORNER == None:
            print('Wrong screen')
            return False
        self.SCREENDIMS = (self.RIGHTCORNER[0]-self.LEFTCORNER[0],self.RIGHTCORNER[1]-self.LEFTCORNER[1])
        size = (FIRSTPUT[1] - self.LEFTCORNER[1])/(self.RIGHTCORNER[1]-self.LEFTCORNER[1])
        if size  > 1/9:
            self.GRIDSIZE = (10,8)
            self.LEVEL = 'easy'
            self.NUMMINES = 10
        elif size > 1/17:
            self.GRIDSIZE = (18,14)
            self.LEVEL = 'medium'
            self.NUMMINES = 40
        else:
            self.GRIDSIZE = (24,20)
            self.LEVEL = 'hard'
            self.NUMMINES = 99
        self.MINES = {(i,j) : False for i in range(self.GRIDSIZE[0]) for j in range(self.GRIDSIZE[1]) }
        return True
        
    def getGrid(self,failedbefore = False):  
        time.sleep(self.TIMEINC)
        #reset mines
        screenShot = pyautogui.screenshot()
        self.GRID = [['?' for _ in range(self.GRIDSIZE[1])] for _ in range(self.GRIDSIZE[0])]
        self.markedFlags = set()
        for i in range(self.GRIDSIZE[0]):
            for j in range(self.GRIDSIZE[1]):
                #Find type for each square in grid
                a,b  = self.getCenter(i,j)
                #Reduce search space to just the center region of the square
                sq = round(self.SCREENDIMS[0]/(6*self.GRIDSIZE[0]))
                for inc1 in range(-sq,sq):
                    pixel = screenShot.getpixel((a+inc1,b+inc1))
                    if self.GRID[i][j] in '1234567': break
                    if pixel in self.BG:
                        self.GRID[i][j] = '-'
                    elif pixel in self.ZERO:
                        self.GRID[i][j] = '_'
                    else:
                        for ind in range(len(self.tileColors)):
                            if self.pixelsclose(pixel,self.tileColors[ind]):
                                self.GRID[i][j] = str(ind+1)
                                break
                        if self.pixelsclose(pixel,(242,54,7)):
                            self.markedFlags.add((i,j))

        #Error handling   
        unreadable = sum(row.count('?') for row in self.GRID)
        self.UNCLICKED = 0
        for i in range(self.GRIDSIZE[0]):
            for j in range(self.GRIDSIZE[1]):
                if self.GRID[i][j] in 'x-?':
                    self.UNCLICKED += 1
        if unreadable > 3 and self.NUMMINES - self.UNCLICKED < 3 and failedbefore:
            self.paramsReady = False
            return 'bad'
        elif unreadable > 2:
            print()
            for row in [[self.GRID[i][j] for i in range(self.GRIDSIZE[0])] for j in range(self.GRIDSIZE[1])]:
                print(' '.join(row))
            print('Grid unreadable')
            self.paramsReady = False
            #Try 2 times, in case there was an unexpected issue the first time
            if failedbefore:
                return 'bad'
            else:
                return self.getGrid(failedbefore=True)
        return self.GRID

    def run(self):
        self.paramsReady = False
        #Main input loop
        while True:
            if keyboard.is_pressed('h'):
                if not self.paramsReady:
                    self.paramsReady=self.getGridParameters()
                if self.paramsReady:
                    self.hint()
            elif keyboard.is_pressed('s'):
                if not self.paramsReady:
                    self.paramsReady=self.getGridParameters()
                if self.paramsReady:
                    self.solve()

#Constants for Google Minesweeper
SHOWFLAGS = True
BG = [(170, 215, 81),(162, 209, 73)]
ZERO = [(215, 184, 153),(229, 194, 159)]
ONE = (25, 118, 210)
TWO = (57,143,61)
THREE = (211,47,47)
FOUR = (123,31,162)
FIVE = (255,144,2)
SIX = (0,151,167)
SEVEN = (66,66,66)
FLAG = (242,54,7)


google = Google(SHOWFLAGS)

#Delay time to prevent parsing bugs
google.TIMEINC = 0.3

google.initColors([BG,ZERO,ONE,TWO,THREE,FOUR,FIVE,SIX,SEVEN])

#Welcome Message
print("Welcome to Minesweeper Assistant")
print("Head over to Google Minesweeper to begin")
print("Press (h) to get a hint, and (s) to autosolve")

#Begin
google.run()
