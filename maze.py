import serial
import time
import threading
import queue
import string
import copy
from tkinter import *
import math
ser = serial.Serial('/dev/cu.usbserial-AM026GAN', 38400, timeout=0)
out_q = queue.Queue()
in_q = queue.Queue()
ang_q = queue.Queue()
#I have to use global varible becasue I used multi-threading and using global variable is the easiest way to work with multi-threading
DCM = [] #the lsit of dcms
Z_B = [] #the list of Z body vectors
J_B = [] #the list of J body vectors
I_B = [] #the list of I body vectors
#The default value of readings from 3 sensors, needed so that the code doesn't crash
Rx = 0
Ry = 0
Rz = 0
zDegrees = 0
yDegrees = 0
xDegrees = 0
RateX = 0
RateY = 0
RateZ = 0
coordinateprev = [0,0,0]
coordinate= [0,0,0]
DCM_1 = [[]]
####################################
#objects
####################################
#Used tutorial here: https://www.packtpub.com/mapt/book/Application-Development/9781785889738/7/ch07lvl1sec88/3D%20graphics%20with%20Tkinter
class Framework():
    def __init__(self,object):
        if(object == "cube"):
            self.type = "cube"
            self.object = self.transpose_matrix([
                        [-100,-100,100],#1
                        [-100, 100,100],#2
                        [100,100,100],#3
                        [100,-100,100],#4
                        [-100,-100,-100],#5
                        [-100,100,-100],#6
                        [100,100,-100],#7
                        [100,-100,-100]#8
                        ])
        elif(object == "pyramid"):
            self.type = "pyramid"
            self.object = self.transpose_matrix([
                        [0,0,100*math.sqrt(3)],#1
                        [0, 100*math.sqrt(3),-100/3*math.sqrt(3)],#2
                        [150,-100/3*math.sqrt(3),-100/3*math.sqrt(3)],#3
                        [-150,-100/3*math.sqrt(3),-100/3*math.sqrt(3)],#4
                        ])    
                        
        elif(object == "octahedron"):
            self.type = "octahedron"
            self.object = self.transpose_matrix([
                        [0,0,100*math.sqrt(2)],#1
                        [100,-100,0],#2
                        [-100,-100,0],#3
                        [-100,100,0],#4
                        [100,100,0],#5
                        [0,0,-100*math.sqrt(2)]
                        ])  
                        
    def transpose_matrix(self,matrix):
        return list(zip(*matrix))
            
    def translate_3dvector(self, x,y,z,dx,dy, dz):
        return [x+dx, y+dy, z+dz]
        
    def translate_vector(self, x,y,dx,dy):
        return x+dx, y+dy
        
    def matrix_multiply(self, matrix_a, matrix_b):
        zip_b = list(zip(*matrix_b))
        return [[sum(ele_a*ele_b for ele_a, ele_b in zip(row_a, col_b))
                 for col_b in zip_b] for row_a in matrix_a]
                 
    def rotate_along_x(self, x, shape):
        return self.matrix_multiply([[1, 0, 0],[0, math.cos(x), - math.sin(x)], [0, math.sin(x), math.cos(x)]], shape)

    def rotate_along_y(self, y, shape):
        return self.matrix_multiply([[math.cos(y), 0, math.sin(y)], [0, 1, 0], [-math.sin(y), 0, math.cos(y)]], shape)

    def rotate_along_z(self, z, shape):
        return self.matrix_multiply([[math.cos(z), math.sin(z), 0],[-math.sin(z), math.cos(z), 0], [0, 0, 1]], shape)

    def draw_object(self,graph, data):
        self.graph =graph
        if(self.type == "cube"):
            points_to_draw_lines=[[0,1,3,4],
            [2,1,3,6],
            [5,1,4,6],
            [7,3,4,6]]
        elif(self.type == "pyramid"):
            points_to_draw_lines=[[0,1,2,3],
            [1,2,3],
            [2,3]]
        elif(self.type == "octahedron"):
            points_to_draw_lines = [[0,1,2,3,4],
            [1,2,4,5],
            [2,3,5],
            [3,4,5],
            [4,5]]
        if(data.mode != "play"):
            data.w = graph.winfo_width()/2
            data.h = graph.winfo_height()/2
            colorlist = ["red", "orange","yellow", "green", "cyan", "blue","purple"]
            fill = colorlist[data.index]
            graph.delete(ALL)
            #print(self.cube)
            for i in points_to_draw_lines:
                for j in i:
                    graph.create_line(self.translate_vector(self.object[0][i[0]],self.object[1][i[0]],data.w,data.h), self.translate_vector(self.object[0][j], self.object[1][j], data.w,data.h), fill = fill)
        else:
            data.w = data.margin
            data.h = data.margin
            fill = "grey"
            graph.delete(ALL)
            #print(self.cube)
            for i in points_to_draw_lines:
                for j in i:
                    graph.create_line(self.translate_vector(self.object[0][i[0]]/10,self.object[1][i[0]]/10,data.w+data.curc*data.wid+data.wid/2,data.h+data.curr*data.leng+data.leng/2), self.translate_vector(self.object[0][j]/10, self.object[1][j]/10, data.w+data.curc*data.wid+data.wid/2,data.h+data.curr*data.leng+data.leng/2), fill = fill)            
                
    def onTimerFired(self, data):
        if(data.mode == "Intro"):
            data.index += 1
            if(data.index >= 6): data.index = 0
            self.object = self.rotate_along_x(data.rotate_speed, self.object)
            self.object = self.rotate_along_y(data.rotate_speed, self.object)
            self.object = self.rotate_along_z(data.rotate_speed, self.object)
        elif(data.mode == "Initialize"):
            data.index += 1
            if(data.index >= 6): data.index = 0
            self.animation(data)
        if(data.mode == "play"):
            self.object = self.rotate_along_x(data.rotate_speed, self.object)
            self.object = self.rotate_along_y(data.rotate_speed, self.object)
            self.object = self.rotate_along_z(data.rotate_speed, self.object)
            self.play_maze(data)
    #for the two functions below I used the code here:https://www.packtpub.com/mapt/book/Application-Development/9781785889738/7/ch07lvl1sec88/3D%20graphics%20with%20Tkinter
    def on_mouse_motion(self, event):
        print("run")
        self.epsilon = lambda d: d * 0.01
        dx = self.last_y - event.y
        self.object = self.rotate_along_x(self.epsilon(-dx), self.object)
        #print("E = ", end="")
        #print(self.epsilon(-dx))
        dy = self.last_x - event.x
        self.object = self.rotate_along_y(self.epsilon(dy), self.object)
        self.on_mouse_clicked(event)
    
        
    def on_mouse_clicked(self, event):
        self.last_x = event.x
        self.last_y = event.y

    def animation(self,data):
        a = self.get_data_usingAcceleration()
        self.imu_motion(a)
        self.imu_translation()
    
    def animationOnlyRotation(self,data):
        a = self.get_data_usingAcceleration()
        self.imu_motion(a)        
        
    def get_data_usingAcceleration(self):
        global Rx, Ry, Rz
        if(-1<RateX<1):
            x = 0
        else: x = math.atan2(Ry, Rz)
        if(-1<RateY<1):
            y = 0 
        else:
            y = math.atan2(Rx,Rz)
        if(-1<RateZ<1):
            z = 0 
        else:
            z = math.atan2(Rx,Ry)
        b = [x,y,z]
        return b
        
    #change the object according to the sensor
    def imu_motion(self, a):
        try:
            self.object = self.rotate_along_x(a[0]/50, self.object)
            self.object = self.rotate_along_y(a[1]/50, self.object)
            self.object = self.rotate_along_z(a[2]/50, self.object)
            #self.draw_cube()
        except:
            print("Didn't work")
            
    def imu_translation(self):
        #print("translation")
        global coordinate, coordinateprev
        self.ebuc = self.transpose_matrix(self.object)
        NewMatrix = []
        for row in self.ebuc:
            NewMatrix += [list(row)]
        for row in range(len(self.ebuc)):
            #Newrow = list(row)
            NewMatrix[row][0] += (coordinate[0] - coordinateprev[0])
            NewMatrix[row][1] += (coordinate[1] - coordinateprev[1])
            NewMatrix[row][2] += (coordinate[2] - coordinateprev[2])
            #print("row = ", row)
        #print(self.ebuc())
        self.object = self.transpose_matrix(NewMatrix)
        #print(self.cube)
    
    def play_maze(self, data):
        global Rx, Ry
        if(0<Rx<0.3): Rx = 0
        elif(-0.7<Ry<0.7): Ry = 0
        if(Rx == 0):
            if(Ry>0): data.dir = "U"
            elif(Ry == 0): data.dir = None
            else: data.dir = "D"
        elif(Ry == 0):
            if(Rx > 0): data.dir = "R"
            elif(Rx<0): data.dir ="L"
        else:
            dir = math.atan(Ry/Rx)
            if(math.pi/4<dir<=math.pi*3/4): data.dir = "U"
            elif(-math.pi/4<dir<math.pi/4): data.dir = "R"
            elif(math.pi*3/4<dir<=math.pi*5/4): data.dir = "L"
            else: data.dir ="D"
            print(math.atan(Ry/Rx))
        print(data.dir)        
    
    
#############################
#The list of target functions
#############################
def readValues():
    try:
        data = ser.readline()
        msg = data.decode('utf-8').split("=")#decode the binary string into normal string
        #print(msg)
        if(msg != ['']):
            dataValue = msg[0].split("\\")[0]#then get the value of the data    
            
            print("dataValue = ", dataValue)
            out_q.put(dataValue)
        time.sleep(1)
    except: #ser.SerialException:
        print('Data error')
        time.sleep(1)

def doMath():
    global Rx, Ry, Rz
    global xDegrees, yDegrees, zDegrees
    global RateX, RateY, RateZ
    global coordinate, coordinateprev
    global DCM_1
    if Rx < 0.10 and Rx >0: Rx = 0
    if Ry < 0.03 and Ry > -0.02: Ry = 0
    if Rz < 0.02 and Rz > -0.02: Rz = 0
    if RateX < 0.5 and RateX > -0.5: RateX = 0
    if RateY < 0.5 and RateY > -0.5: RateY = 0
    if RateZ < 0.5 and RateZ > -0.5: RateZ = 0
    #Put the readings from sensor into matrices
    A = [Rx, Ry, Rz]#the 3 axis accelerometer output
    #print("A = ", A)
    M = [xDegrees, yDegrees, zDegrees]#the corrected 3-axis magnetometer output 
    K_b = [-1*i for i in A]#Zenith KB
    I_b = copy.copy(M)#magnetic north IB
    J_b = copy.copy(crossProduct(K_b, I_b))
    DCM_B = [I_b,J_b, K_b]
    #print("DCM_B = ", DCM_B)
    DCM_G = copy.copy(transMatrix(DCM_B))
    #print("DCM_G = ", DCM_G)
    deltaAng = [RateX, RateY, RateZ]
    #print("deltaAng = ", deltaAng)
    K_b1 = matrixAddition(K_b, crossProduct(deltaAng, K_b))
    J_b1 = matrixAddition(J_b, crossProduct(deltaAng, J_b))  
    I_b1 = matrixAddition(I_b, crossProduct(deltaAng, I_b))
    Err = (dotProduct(I_b1,J_b1)/2)
    #print("Err = ", Err)
    I_b1_c = listSub(I_b1, multiByCst(Err, J_b1))
    J_b1_c = listSub(J_b1, multiByCst(Err, I_b1))
    K_b1_c = crossProduct(I_b1,J_b1_c)
    DCM_1 = transMatrix([I_b1, J_b1, K_b1])
    #print("DCM_1 = ", DCM_1)
    A = [Rx, Ry, Rz]#the 3 axis accelerometer output
    lenA = math.sqrt(Rx**2 + Ry**2 + Rz**2)
    A = multiByCst(1/lenA, A)
    #print("Two side of the multiplication = ", DCM_1, " and ", A)
    coordinateprev = coordinate
    coordinate = matrixMultiplication(DCM_1, [1,0,0])
    print("Coordinate = ", coordinate)
         
#The communication from readSensor thread to doMath thread
def dataCom():
    global Rx, Ry, Rz
    global xDegrees, yDegrees, zDegrees
    global RateX, RateY, RateZ
    try:
        data = out_q.get()
        #namestring = data[0] + "=" + str(data[1])
        #print(namestring)
        #for i in data.split(":"):
        setVaribles("Rx",float(data.split(":")[0]))
        setVaribles("Ry",float(data.split(":")[1]))
        setVaribles("Rz",float(data.split(":")[2]))
        setVaribles("RateX",float(data.split(":")[3]))
        setVaribles("RateY",float(data.split(":")[4]))
        setVaribles("RateZ",float(data.split(":")[5]))
        setVaribles("xDegrees",float(data.split(":")[6]))
        setVaribles("yDegrees",float(data.split(":")[7]))
        a = float(data.split(":")[8])
        setVaribles("zDegrees",float(data.split(":")[8]))
    except:
        print("no data ")

    
#############################
#The list of helper functions
#############################      
  


def setVaribles(name, value):
    global Rx, Ry, Rz
    global xDegrees, yDegrees, zDegrees
    global RateX, RateY, RateZ
    if(name == "Rx"): 
        Rx = value
    elif(name == "Ry"): Ry = value
    elif(name == "Rz"): Rz = value
    elif(name == "Ry"): RY = value
    elif(name == "RateX"): RateX = value
    elif(name == "RateY"): RateY = value
    elif(name == "RateZ"): RateZ = value
    elif(name == "xDegrees"): xDegrees = value
    elif(name == "yDegrees"): yDegrees = value
    elif(name == "zDegrees"): zDegrees = value
    pass

#the cross product in 3-dim vectors
def crossProduct(a,b):
    return [a[1]*b[2]-a[2]*b[1], a[2]*b[0]-a[0]*b[2],a[0]*b[1]-a[1]*b[0]]
    
#multiply a bector by a constant
def multiByCst(c,V):
    newV = [0]*len(V)
    for i in range(len(V)):
        newV[i] = c*V[i]
    return newV

#vector subtraction
def listSub(A, B):
    NewList = []
    for i in range(len(A)):
        NewList += [A[i]-B[i]]
    return NewList

#the dot product of 3-dim vectors
def dotProduct(a,b):        
    return a[0]*b[0]+a[1]*b[1]+a[2]*b[2]

#the addition of matrices
def matrixAddition(a,b):
    NewMatrix = []
    for i in range(len(a)):
        NewMatrix.append(a[i]+b[i])
    return NewMatrix
    
#the multiplication of matrices
def matrixMultiplication(a,b):
    sum = 0
    NewMatrix = []
    for r in range(len(a)):
        for c in range(len(a[0])):
                sum += a[r][c]*b[c]
        NewMatrix.append(sum)
        sum = 0
    return NewMatrix

#the transpose of a matrix
def transMatrix(M):
    newMatrix = [[0]*len(M[0]) for i in range(len(M))]
    for c in range(len(M[0])):
        for r in range(len(M)):
            newMatrix[c][r] = M[r][c]
    return newMatrix

###############
#The Controller
###############
#http://stackoverflow.com/questions/11488877/periodically-execute-function-in-thread-in-real-time-every-n-seconds


def do_every (interval, worker_func, iterations = 0):
    if iterations != 1:
        threading.Timer (interval, do_every, [interval, worker_func, 0 if iterations == 0 else iterations-1]).start ()
    for f in worker_func:
      f()

    
####################################
# init
####################################

def init(data):
    # There is only one init, not one-per-mode
    data.spinningCube = Framework("cube")
    data.cube = Framework("cube")
    data.pyramid = Framework("pyramid")
    data.octahedron = Framework("octahedron")
    data.objectlist = ["pyramid", "cube", "octahedron"]
    data.rotate_speed = 0.01
    data.index = 0
    data.height = 640
    data.width = 640
    data.win = False
    data.curr = 0
    data.curc = 0
    data.type = "pyramid"
    data.object = "cube"
    data.mode = "Intro"
    data.playobject = None
    data.dir = None
    data.w = 0
    data.h = 0
    data.margin = 20
    data.maze2d = False
    data.maze3d = True
    data.leng = (data.height - data.margin*2)/8
    data.wid = (data.width - data.margin*2)/8
    data.maze = [[0,1,0,1,1,0,1,0],
    [0,1,1,0,0,0,0,1],
    [0,0,0,0,1,1,0,0],
    [1,0,1,0,1,0,0,1],
    [0,0,0,1,0,0,1,0],
    [1,1,0,1,1,0,0,1],
    [0,1,0,0,0,1,0,1],
    [0,0,0,1,0,1,0,0]]

####################################
# mode dispatcher
####################################

def mousePressed(event, data):
    if (data.mode == "Intro"): 
        data.spinningCube.on_mouse_clicked()
        data.spinningCube.on_mouse_motion()
    elif(data.mode == "Initialize"):
        print("Changed")
        initializeMousePressed(event,data)
        
    #elif (data.mode == "playGame"):   playGameMousePressed(event, data)
    #elif (data.mode == "help"):       helpMousePressed(event, data)
    pass

def keyPressed(event, data):
    if (data.mode == "Intro"): IntroKeyPressed(event, data)
    elif (data.mode == "Initialize"):   initializeKeyPressed(event, data)
    elif (data.mode == "help"):       helpKeyPressed(event, data)
    elif(data.mode == "win"): winPressed(event,data)

def timerFired(data):
    if (data.mode == "Intro"): data.spinningCube.onTimerFired(data)
    elif(data.mode == "Initialize"): 
        if(data.type == "cube"):
            data.cube.onTimerFired(data)
        elif(data.type == "pyramid"):
            data.pyramid.onTimerFired(data)
        elif(data.type == "octahedron"):
            data.octahedron.onTimerFired(data)
        #elif(data.type == "dodecahedron"):
         #   data.dodecahedron.onTimerFired(data)            
    elif (data.mode == "play"): 
        if(data.playobject == "cube"):
            data.cube.onTimerFired(data)           
        elif(data.playobject == "pyramid"):
            data.pyramid.onTimerFired(data) 
        elif(data.playobject == "octahedron"):
            data.octahedron.onTimerFired(data)
        playGameTimerFired(data)
    #elif (data.mode == "help"):       helpTimerFired(data)

def redrawAll(canvas, data):
    if (data.mode == "Intro"): 
        data.spinningCube.draw_object(canvas,data)
        drawCover(canvas, data)
    elif (data.mode == "Initialize"):
        if(data.type == "cube"):
            data.cube.draw_object(canvas,data)
        elif(data.type == "pyramid"):
            data.pyramid.draw_object(canvas,data)
        elif(data.type == "octahedron"):
            data.octahedron.draw_object(canvas,data)
        intializeRedrawAll(canvas,data)
    elif (data.mode == "play"):   
        if(data.playobject == "cube"):
            data.cube.draw_object(canvas,data)
        elif(data.playobject == "pyramid"):
            data.pyramid.draw_object(canvas,data)
        elif(data.playobject == "octahedron"):
            data.octahedron.draw_object(canvas,data)
        playGameRedrawAll(canvas, data)
    elif (data.mode == "help"):       helpRedrawAll(canvas, data)
    elif(data.mode == "win"): winRedrawAll(canvas,data)

####################################
# Intro mode
####################################

def drawCover(canvas, data):
    canvas.create_text(data.width/2, data.height/2-40, text = "Interactive Animation", font = "Arial 26 bold")
    canvas.create_text(data.width/2, data.height/2-10, text = "and", font = "Arial 26 bold")
    canvas.create_text(data.width/2, data.height/2+20, text = "Trajectory Tracking Without Navigation", font = "Arial 26 bold")
    #canvas.create_rectangle(data.width/12, data.height/12, data.width/10, data.height/10)
    
def IntroTimerFired(data):
    pass
    
def IntroKeyPressed(event,data):
    if(event.keysym == "h"):
        data.mode = "help"
    if(event.keysym == "i"):
        data.mode = "Initialize"
####################################
# help mode
####################################

def helpMousePressed(event, data):
    pass

def helpKeyPressed(event, data):
    if(event.keysym == "i"): data.mode = "Initialize"

def helpTimerFired(data):
    pass

def helpRedrawAll(canvas, data):
    canvas.create_text(data.width/2, data.height/2-40,
                       text="This is help mode!", font="Arial 26 bold")
    canvas.create_text(data.width/2, data.height/2-10,
                       text="How to play:", font="Arial 20")
    canvas.create_text(data.width/2, data.height/2+15,
                       text="Pick your 3D object and solve maze with your joystick!!!", font="Arial 20")
    canvas.create_text(data.width/2, data.height/2+40,
                       text="Press \"p\" to keep playing!", font="Arial 26 bold")
    canvas.create_text(data.width/2, data.height/2+70,
                       text="Press \"i\" to pick your object!", font="Arial 26 bold")

####################################
# Initalize mode
####################################

def initializeMousePressed(event, data):
    pass

def initializeKeyPressed(event, data):
    if (event.keysym == 'h'):
        data.mode = "help"
    elif(event.keysym == "Right"):
        index = data.objectlist.index(data.type)
        if(index==2): index = -1
        data.type = data.objectlist[index+1]
    elif(event.keysym == "p"):
        data.playobject = data.type
        data.mode = "play"
            

def initializeTimerFired(data):
    pass

def intializeRedrawAll(canvas, data):
    canvas.create_text(data.width/2, data.height/2+70,
                       text="Pick an object to manipulate", font = "Arial 20")
        

####################################
# playGame mode
####################################

def playGameMousePressed(event, data):
    pass

def playGameKeyPressed(event, data):
    if(data.win == "True"):
        data.mode = "win"
    if (event.keysym == 'h'):
        data.mode = "help"

def playGameTimerFired(data):
    if(data.dir=="U"):
        data.curr -=1
    if(data.dir=="D"):
        data.curr += 1
    if(data.dir =="R"):
        data.curc += 1
    if(data.dir == "L"):
        data.curc -=1
    if(data.curr<0): data.curr += 1
    if(data.curr>7): data.curr -=1
    if(data.curc<0): data.curc += 1
    if(data.curc>7): data.curc -= 1 
    if(data.maze[data.curr][data.curc] == 1):
        if(data.dir=="U"):
            data.curr +=1
        if(data.dir=="D"):
            data.curr -= 1
        if(data.dir =="R"):
            data.curc -= 1
        if(data.dir == "L"):
            data.curc +=1
    if(data.curr == 7 and data.curc == 7):
        print("WWWin")
        data.win = True
        

def playGameRedrawAll(canvas, data):
    if(data.win == True):
        print("work")
        canvas.create_text(data.width/2, data.height/2-40,
                       text="Cong! Your win! Press any button to restart", font="Arial 26 bold")        
    else:
        margin = data.margin
        canvas.create_line(margin+data.wid,margin, data.width-margin, margin, fill = "black")
        canvas.create_line(margin,margin, margin, data.height - margin, fill = "black")
        canvas.create_line(margin,data.height - margin, data.width-margin, data.height - margin, fill = "black")
        canvas.create_line(data.width-margin,margin, data.width-margin, data.height-data.leng- margin, fill = "black")
        for r in range(len(data.maze)):
            for c in range(len(data.maze[0])):
                if(data.maze[r][c] == 1):
                    canvas.create_rectangle(margin+c*data.leng, margin+r*data.leng, margin+(c+1)*data.leng, margin+(r+1)*data.leng, fill = "black", width = 0)
                    
####################################
# Win mode
####################################

def winPressed(event, data):
    data.mode = "Intro"

def winTimerFired(data):
    pass
        

def winRedrawAll(canvas, data):
    canvas.create_text(data.width/2, data.height/2-40,
                       text="Cong! Your win! Press any button to restart", font="Arial 26 bold")        
####################################
# use the run function as-is
####################################

def run(width=640, height=640):
    def redrawAllWrapper(canvas, data):
        canvas.delete(ALL)
        canvas.create_rectangle(0, 0, data.width, data.height,
                                fill='white', width=0)
        redrawAll(canvas, data)
        canvas.update()    

    def mousePressedWrapper(event, canvas, data):
        mousePressed(event, data)
        redrawAllWrapper(canvas, data)

    def keyPressedWrapper(event, canvas, data):
        keyPressed(event, data)
        redrawAllWrapper(canvas, data)

    def timerFiredWrapper(canvas, data):
        timerFired(data)
        redrawAllWrapper(canvas, data)
        # pause, then call timerFired again
        canvas.after(data.timerDelay, timerFiredWrapper, canvas, data)
    # Set up data and call init
    class Struct(object): pass
    data = Struct()
    data.width = width
    data.height = height
    data.timerDelay = 100 # milliseconds
    init(data)
    # create the root and the canvas
    root = Tk()
    canvas = Canvas(root, width=data.width, height=data.height)
    canvas.pack()
    # set up events
    root.bind("<Button-1>", lambda event:
                            mousePressedWrapper(event, canvas, data))
    root.bind("<Key>", lambda event:
                            keyPressedWrapper(event, canvas, data))
    root.bind("<Button-1>", data.spinningCube.on_mouse_clicked)
    root.bind("<B1-Motion>", data.spinningCube.on_mouse_motion)
    timerFiredWrapper(canvas, data)
    root.configure(background='black')
    # and launch the app
    root.mainloop()  # blocks until window is closed
    print("bye!")
    

run(640,640)
FunctionList = [readValues,dataCom,doMath]
do_every(0.3, FunctionList)