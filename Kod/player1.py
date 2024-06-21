from ili934xnew import ILI9341, color565
from machine import Pin, SPI
from micropython import const
import os, glcdfont, tt14, tt24, tt32, time, random, network,ujson
from umqtt.robust import MQTTClient
from machine import Timer

# Dimenzije displeja
SCR_WIDTH = const(320)
SCR_HEIGHT = const(240)
SCR_ROT = const(3)
CENTER_Y = int(SCR_WIDTH / 2)
CENTER_X = int(SCR_HEIGHT / 2)

print(os.uname())

# Podešenja SPI komunikacije sa displejem
TFT_CLK_PIN = const(18)
TFT_MOSI_PIN = const(19)
TFT_MISO_PIN = const(16)
TFT_CS_PIN = const(17)
TFT_RST_PIN = const(20)
TFT_DC_PIN = const(15)
# Fontovi na raspolaganju
fonts = [glcdfont, tt14, tt24, tt32]

spi = SPI(
    0,
    baudrate=62500000,
    miso=Pin(TFT_MISO_PIN),
    mosi=Pin(TFT_MOSI_PIN),
    sck=Pin(TFT_CLK_PIN))
print(spi)
display = ILI9341(
    spi,
    cs=Pin(TFT_CS_PIN),
    dc=Pin(TFT_DC_PIN),
    rst=Pin(TFT_RST_PIN),
    w=SCR_WIDTH,
    h=SCR_HEIGHT,
    r=SCR_ROT)


rows = [Pin(21, Pin.IN, Pin.PULL_DOWN), Pin(22, Pin.IN, Pin.PULL_DOWN), Pin(26, Pin.IN, Pin.PULL_DOWN), Pin(27, Pin.IN, Pin.PULL_DOWN)]
cols = [Pin(0, Pin.OUT), Pin(1, Pin.OUT), Pin(2, Pin.OUT), Pin(3, Pin.OUT)]

# Mapa tastera
keys = [['1', '2', '3', 'A'],
        ['4', '5', '6', 'B'],
        ['7', '8', '9', 'C'],
        ['*', '0', '#', 'D']]

level = 1
randomNumbers = [0] * 10
rectW = 40  #sirina kvadratica
rectH = 45  #visina kvadratica
currentPlayer = 0
guessedNumbers = [0] * 10
inputString = ""


red=color565(255, 0, 0)
green=color565(0, 255, 0)
blue=color565(0, 0, 255)
yellow=color565(255, 255, 0)
cyan=color565(0, 255, 255)
magenta=color565(255, 0, 255)
white=color565(255, 255, 255)
colour1=white
colour2 = white
colors=[red,green,blue,yellow,cyan,magenta,white]

players = [{"name": "Player 1", "score": 0, "color": colour1}, {"name": "Player 2", "score": 0, "color": colour2}]

# Uspostavljanje WiFI konekcije
nic = network.WLAN(network.STA_IF)
nic.active(True)
nic.connect('Lab220', 'lab220lozinka')

while not nic.isconnected():
    print("Čekam konekciju ...")
    time.sleep(5)
print("WLAN konekcija uspostavljena")
ipaddr=nic.ifconfig()[0]
print("Mrežne postavke:")
print(nic.ifconfig())

#fja za prijem MQTT poruka
def subFun(topic, msg):
    global randomNumbers, inputString
    print("Received message on topic:", topic, "with message:", msg)  # Debugging statement
    if topic == b'aksk2/inputStr2': #za prikaz brojeva koje unosi player2
        key = ujson.loads(msg)
        print("Input key od P2:", inputString) 
        showOnDisplay(key)
    if topic == b'aksk2/selectedColor2': #boja avatara playera2
        key = ujson.loads(msg)
        players[1]['color'] = colors[int(key) - 1]
        generateRandomNumbers(level)
        gameLoop()
        
# Uspostavljanje konekcije sa MQTT brokerom
mqtt_conn = MQTTClient(client_id='aksk1', server='broker.hivemq.com',user='',password='',port=1883)
mqtt_conn.set_callback(subFun)
mqtt_conn.connect()
mqtt_conn.subscribe(b"aksk2/#")

print("Konekcija sa MQTT brokerom uspostavljena")

# Brisanje displeja i odabir pozicije (0,0)    
display.erase()
display.set_pos(0, 0)

def showInitalScreen():
    #pocetni meni
    display.set_pos(60, 20)
    display.set_font(tt32)
    display.set_color(yellow, color565(0, 0, 0))
    display.rotation = 2
    display.print("Crack the code")
    display.set_color(white, color565(0, 0, 0))
    display.set_font(tt24)
    display.set_pos(25, 70)
    display.print("Rules:")
    display.set_font(tt14)
    display.set_pos(35, 100)
    display.print("1. Two players and 10 levels")
    display.print("2. You need to guess all the digits ")
    display.set_pos(50, 130)
    display.print("of a number to get 5 extra points")
    display.set_pos(35, 145)
    display.print("3. You get 1 point for each guessed number ")
    display.print("4. The maximum number of points is 100")
    display.print("5. The winner is the one with more points")
    display.set_pos(50, 190)
    display.print(" at the end of the 10th level")
    time.sleep(3)

    #drugi dio
    display.erase()
    display.set_font(tt24)
    display.set_pos(33, 20)
    display.print("How to manage number")
    display.set_pos(130, 50)
    display.print("entry?")
    display.set_font(tt14)
    display.set_pos(65, 100)
    display.print("Select digits using the keyboard")
    display.print("Press # to confirm")
    display.print("Press D to delete last digit")
    display.set_pos(15, 190)
    display.set_color(yellow, color565(0, 0, 0))
    display.print("To start the game, please select color for your avatar")
    time.sleep(3)

def avatarSelection(): #odabir boje avatara
    global players,colors
    display.erase()
    display.set_font(tt24)
    display.set_pos(15, 20)
    display.set_color(color565(255, 255, 255), color565(0, 0, 0))
    display.rotation = 2
    display.print(f"{players[0]['name']}, choose the color of")
    display.set_pos(100, 50)
    display.print("your avatar!")
    display.set_pos(15, 80)
    display.set_color(yellow, color565(0, 0, 0))
    display.set_font(tt14)
    display.print("To select a color, press the number of the row")
    display.set_pos(50, 95)
    display.print("where your chosen color is located.")

    display.set_color(red, color565(0, 0, 0))
    display.set_pos(140, 120)
    display.print("1. Red")
    display.set_color(green, color565(0, 0, 0))
    display.print("2. Green")
    display.set_color(blue, color565(0, 0, 0))
    display.print("3. Blue")
    display.set_color(yellow, color565(0, 0, 0))
    display.print("4. Yellow")
    display.set_color(cyan, color565(0, 0, 0))
    display.print("5. Cyan")
    display.set_color(magenta, color565(0, 0, 0))
    display.print("6. Magenta")
    display.set_color(white, color565(0, 0, 0))
    display.print("7. White")
    time.sleep(1)

def readKeypad():#citanje sa tastature
    while True:
        key = None
        for i in range(4):
            cols[i].on()
            for j in range(4):
                if rows[j].value() == 1:
                    key = keys[j][i]
                    time.sleep(0.2)
                    break
            cols[i].off()
            if key is not None:
                break
        if key is not None:
            while any(rows[j].value() == 1 for j in range(4)):  #cekamo dok taster nije otpusten
                pass
            return key
        
def generateRandomNumbers(lvl):  # generisanje rendom br zavisno od lvla
    global randomNumbers   
    for i in range(lvl):
        randomNumbers[i] = random.randrange(10)
    print("Generated numbers for level", lvl, ":", randomNumbers[:lvl])
    msg = ujson.dumps(randomNumbers[:lvl]) #saljemo msg playeru 2 o rand generisanom broju
    mqtt_conn.publish(b'aksk1/randNumP1',msg)
    
def checkGuess(guess):  #provj unesenih br
    global randomNumbers, level
    result = []
    for i in range(level):
        if guess[i] == str(randomNumbers[i]):
            result.append('correct')
        else:
            result.append('incorrect')
    return result

def drawRectangle(display, x, y, w, h, color):#crta kvadratic liniju po liniju
    for i in range(w):#gornja linija
        display.pixel(x + i, y, color)
    for i in range(w):#donja linija
        display.pixel(x + i, y + h, color)
    for i in range(h):#lijevo 
        display.pixel(x, y + i, color)
    for i in range(h):#desno 
        display.pixel(x + w, y + i, color)

def drawRectangles():#racuna pozicije kvadratica pa se koristi drawRectangle fjom
    global level, rectW, rectH, display, CENTER_X, CENTER_Y
    max_rects_per_row = 5
    display.set_font(tt32)
    if level >= 6:#iscrtavanje kad imamo 2 reda
        nmRows = 2
        firstRow = level // 2
        secondRow = level - firstRow
        firstRowX = CENTER_X - (firstRow * rectW // 2) + 40
        secondRowX = CENTER_X - (secondRow * rectW // 2) + 40
        firstRowY = CENTER_Y - ((rectH * nmRows) // 2) - 15
        secondRowY = firstRowY + rectH
        for i in range(firstRow):
            x = firstRowX + i * rectW
            y = firstRowY
            drawRectangle(display, x, y, rectW, rectH, color565(255, 255, 255))
        for i in range(secondRow):
            x = secondRowX + i * rectW
            y = secondRowY
            drawRectangle(display, x, y, rectW, rectH, color565(255, 255, 255))
    else:#iscrtavanje kada imamo 1 red
        nmRows = 1
        startX = (SCR_WIDTH - (rectW * level)) // 2 
        startY = CENTER_Y - (rectH // 2) - 25
        for i in range(level):
            x = startX + i * rectW
            y = startY
            drawRectangle(display, x, y, rectW, rectH, color565(255, 255, 255))

def showScore():#prikaz bodovanja
    display.set_font(tt14)
    display.set_pos(240, 10)
    display.print("P1: {} P2: {}".format(players[0]["score"], players[1]["score"]))

def setupDisplay(level): #iscrtavanje kvadratica na osnovu nivoa
    max_rects_per_row = 5
    positions = {}
    if level >= 6:  #kada imamo 2 reda
        positions['nmRows'] = 2
        positions['firstRow'] = level // 2
        positions['secondRow'] = level - positions['firstRow']
        positions['firstRowX'] = CENTER_X - (positions['firstRow'] * rectW // 2) + 33
        positions['secondRowX'] = CENTER_X - (positions['secondRow'] * rectW // 2) + 33
        positions['firstRowY'] = CENTER_Y - ((rectH * positions['nmRows']) // 2) - 40
        positions['secondRowY'] = positions['firstRowY'] + rectH
    else:  #1 red
        positions['nmRows'] = 1
        positions['startX'] = (SCR_WIDTH - (rectW * level)) // 2 - 12
        positions['startY'] = CENTER_Y - (rectH // 2) - 40
    return positions

def updateScore(results, level): #dodjela bodova
    global guessedNumbers
    correct_count = results.count('correct')
    for i in range(level): #provj da li je neka od cifara pogođena
        if results[i] == "correct" and guessedNumbers[i] == 0:
            players[currentPlayer]["score"] += 1
            guessedNumbers[i] = 1
    if level == 1:
        guessedNumbers = [0] * 10
    if correct_count == level and level > 1:  #ako je cijeli broj pogodjen
        players[currentPlayer]["score"] += 5
        guessedNumbers = [0] * 10
        
def displayInput(key, level, inputString, positions): #prikaz brojeva na ekranu 
    index = len(inputString) - 1
    if level >= 6:
        if index < positions['firstRow']:
            row = 0
            col = index
            display.set_pos(positions['firstRowX'] + col * rectW + 20, positions['firstRowY'] + 32)
        else:
            row = 1
            col = index - positions['firstRow']
            display.set_pos(positions['secondRowX'] + col * rectW + 20, positions['secondRowY'] + 32)
    else:
        row = 0
        col = index
        display.set_pos(positions['startX'] + col * rectW + 25, positions['startY'] + 24)
    display.print(key)

def checkGuessAndUpdate(inputString, level, positions): #provj ispravnost unosa i mijenja boju kvadratica 
    results = checkGuess(inputString)
    correct_count = results.count('correct')
    for i in range(level):
        if level >= 6:
            if i < positions['firstRow']:
                x = positions['firstRowX'] + i * rectW - 5
                y = positions['firstRowY'] + 10
            else:
                x = positions['secondRowX'] + (i - positions['firstRow']) * rectW - 5
                y = positions['secondRowY'] + 10
        else:
            x = positions['startX'] + i * rectW
            y = positions['startY']
        if results[i] == 'correct':  #tacan br -  green border
            drawRectangle(display, x + 12 , y + 15, rectW, rectH, color565(0, 255, 0))
        else:  #netacan br -  red border
            drawRectangle(display, x + 12, y + 15, rectW, rectH, color565(255, 0, 0))
    time.sleep(1)
    updateScore(results, level)
    return correct_count == level

def deleteLastDigit(level, index, positions): #brisanje posljednjeg broja
    if level >= 6:
        if index < positions['firstRow']:
            x = positions['firstRowX'] + index * rectW + 20
            y = positions['firstRowY'] + 32
        else:
            x = positions['secondRowX'] + (index - positions['firstRow']) * rectW + 20
            y = positions['secondRowY'] + 32
    else:
        x = positions['startX'] + index * rectW + 25
        y = positions['startY'] + 24
    for i in range(x - 8, x + rectW - 16):
        for j in range(y + 3, y + rectH - 10):
            display.pixel(i, j, color565(0, 0, 0))
            
def handleGameEnd(): #zavrsetak igre, ispisuje rezultat
    display.erase()
    display.set_font(tt32)
    display.set_pos(30, 90)
    if players[0]["score"] > players[1]["score"]:
        display.print("Winner: Player 1!")
    elif players[0]["score"] < players[1]["score"]:
        display.print("Winner: Player 2!")
    else:
        display.print("It's a tie!")
    display.set_pos(30, 120)
    display.print("Scores: P1={} P2={}".format(players[0]["score"], players[1]["score"]))
    time.sleep(3)
    playAgain()
        
def handleKeyInput(key, positions): #provj unos sa tastature, poziva odgovarajuce funkcije 
    global inputString, level, currentPlayer
    if key.isdigit() and len(inputString) < level:
        inputString += key
        displayInput(key, level, inputString, positions)
    elif key == "#":  #potvrda unosa
        print(str(inputString))
        if len(inputString) == level:
            full_correct = checkGuessAndUpdate(inputString, level, positions)
            inputString = ""
            if full_correct:
                level += 1
                guessedNumbers = [0] * 10
                if level < 11:
                    generateRandomNumbers(level)
                if level > 10:  #kraj igre
                    handleGameEnd()
                else:
                    gameLoop()
            else:
                currentPlayer = 1 - currentPlayer  #switch player
                gameLoop()
    elif key == "D":  #brisanje posljednje cifre
        if len(inputString) > 0:
            inputString = inputString[:-1]
            deleteLastDigit(level, len(inputString), positions)

def showOnDisplay(key):  #prikaz unosa sa tastature
    global inputString, level, score, currentPlayer, guessedNumbers
    display.set_font(tt32)
    positions = setupDisplay(level)
    handleKeyInput(key, positions)

def avatarSelected(avatar): #odabir boje za igraca 1
    global colour1, colors, currentPlayer
    drawRectangle(display, 135, 117+(int(avatar)-1)*15, 75, 15, color565(255, 255, 255))
    players[0]['color'] = colors[int(avatar)-1]
    print("Player1 selected color:", colors[int(avatar)-1])
    time.sleep(0.2)

showInitalScreen()

def gameLoop(): #glavna petlja 
    global level, currentPlayer, colour1
    display.erase()
    display.set_font(tt24)
    display.set_pos(10, 15)
    drawRectangle(display, 0, 0, 319, 239, players[currentPlayer]['color'])
    display.print("Level: {}".format(level))
    display.set_pos(10, 40)
    display.print("Turn: {}".format(players[currentPlayer]["name"]))
    showScore()
    drawRectangles()
    time.sleep(1)

def playAgain(): #ponovno pokretanje igre 
    global level, randomNumbers, currentPlayer, guessedNumbers, inputString, players
    display.erase()
    display.set_pos(30,90)
    display.set_font(tt24)
    display.print("To play again, Player1 should press A")
    while True:
        key = readKeypad()
        if (key == 'A'):
            msg = ujson.dumps(key)
            mqtt_conn.publish(b'aksk1/pAgain',msg)
            level = 1
            randomNumbers = [0] * 10
            currentPlayer = 0
            guessedNumbers = [0] * 10
            inputString = ""
            players = [{"name": "Player 1", "score": 0, "color": colour1}, {"name": "Player 2", "score": 0, "color": colour2}]
            break
        time.sleep(0.5)
    avatarSelection()
    while True:
        key = readKeypad()
        print("Player 1 selected number:", key)
        if key in ['1', '2', '3', '4', '5', '6', '7']:
            avatarSelected(key)
            msg = ujson.dumps(key)
            mqtt_conn.publish(b'aksk1/selectedColor1',msg)
            break
 
def checkMQTTmsg(timer): #provjera dolaznih MQTT poruka
    mqtt_conn.check_msg()
    
mqtt_timer = Timer(-1)
mqtt_timer.init(period=50, mode=Timer.PERIODIC, callback=checkMQTTmsg)

while True:
    avatarSelection()
    key = readKeypad()
    print("Player 1 selected number:", key)
    if key in ['1', '2', '3', '4', '5', '6', '7']:
        avatarSelected(key)
        msg = ujson.dumps(key)
        mqtt_conn.publish(b'aksk1/selectedColor1',msg)
        break

while True: #provj da li je unesen key sa tastature
    key = readKeypad()
    if key and currentPlayer == 0:
        msg = ujson.dumps(key)
        mqtt_conn.publish(b'aksk1/inputStr1',msg)
        showOnDisplay(key)
    time.sleep(0.1)


