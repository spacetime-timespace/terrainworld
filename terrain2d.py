#@title Marching squares on Simplex Noise
import arcade
import matplotlib.pyplot as plt
from noiselib import rng, Simplex, np
import time
from PIL import Image
import ast
import base64 as b64
#Levenshtein distance
ins=0.1
dels=1.0
subs=1.0
trans=0.5
textures="new-textures/"
def levenshtein(s1, s2):
    if len(s1) == 0:
        return 0

    if len(s2) == 0:
        return 0
    preprevious_row = []
    previous_row = [i*ins for i in range(len(s2) + 1)]
    for i, c1 in enumerate(s1):
        current_row = [(i+1)*dels]
        for j, c2 in enumerate(s2):
            insertions = current_row[j] + ins
            deletions = previous_row[j+1] + dels
            substitutions = previous_row[j] + subs
            transpositions = np.inf
            matchings = np.inf
            if len(s1) > 1 and len(s2) > 1 and i>0 and j>0:
                if s1[i]==s2[j-1] and s2[j]==s1[i-1]:
                    transpositions = preprevious_row[j-1] + trans
            if c1==c2:
                matchings=previous_row[j]
            current_row.append(min(insertions, deletions, substitutions, transpositions, matchings))
        preprevious_row = previous_row
        previous_row = current_row
    return 1-np.exp(-previous_row[-1]/len(s1))
#Every pattern in marching squares
#Interior to the left
bkg=(10,25,47,255)
msdict = {
    (0,0,0,0):([],0),
    (1,0,0,0):([(2,0)],0),
    (0,1,0,0):([(1,2)],1),
    (1,1,0,0):([(1,0)],0),
    (0,0,1,0):([(0,3)],2),
    (1,0,1,0):([(2,3)],0),
    (0,1,1,0):([(0,4),(1,4),(4,2),(4,3)],1),
    (1,1,1,0):([(1,3)],0),
    (0,0,0,1):([(3,1)],3),
    (1,0,0,1):([(4,0),(4,1),(2,4),(3,4)],0),
    (0,1,0,1):([(3,2)],1),
    (1,1,0,1):([(3,0)],0),
    (0,0,1,1):([(0,1)],2),
    (1,0,1,1):([(2,1)],0),
    (0,1,1,1):([(0,2)],1),
    (1,1,1,1):([],0),
}
class Point:
    def __init__(self,x,y):
        self.x=x
        self.y=y
    def __add__(self,other):
        return Point(self.x+other.x,self.y+other.y)
    def __sub__(self,other):
        return Point(self.x-other.x,self.y-other.y)
    def __mul__(self,other):
        if type(other) == Point:
            return self.x*other.x+self.y*other.y
        else:
            return Point(self.x*other,self.y*other)
    def __truediv__(self,other):
        if other!=0:
            return Point(self.x/(other+0.000001),self.y/(other+0.00001))
    def __str__(self):
        return "("+str(self.x)+","+str(self.y)+")"
    def __repr__(self):
        return "("+str(self.x)+","+str(self.y)+")"
    def abs(self):
        return (self.x**2+self.y**2)**0.5
    def proj(self,v):
        return (self*v)/(v*v+0.001)
    def cross(self,v):
        return self.y*v.x-self.x*v.y
    def norm(self):
        return Point(self.y,-self.x)/self.abs()
    def cp(self,l0,l1):
        m0=l0-self
        m1=l1-self
        d=m0-m1
        t = m0.proj(d)
        return min(1,max(t,0))
    def acp(self,l0,l1):
        return l0+(l1-l0)*self.cp(l0,l1)

def push_distance(p,ri,l0,l1):
    r=ri+0.05
    v=l1-l0
    w=p-l0
    d=v.cross(w)/(v.abs()+0.001)
    if -r<d<r and 0<p.cp(l0,l1)<1:
        return v.norm()*(r-d)
    elif (p-p.acp(l0,l1)).abs()<r:
        b=p-p.acp(l0,l1)
        if b.abs()>0:
            return b/b.abs()*(r+0.2-b.abs())
    
#marching squares on four verticies
def ms(thres,v,offset):
    vces = [i[0] for i in v]
    k = (0 if vces[0] < thres else 1, 0 if vces[1] < thres else 1, 0 if vces[2] < thres else 1, 0 if vces[3] < thres else 1)
    edges = msdict[k][0]
    try:
        c1 = (thres-vces[0])/(vces[2]-vces[0])
    except ZeroDivisionError:
        c1 = 0
    try:
        c2 = (thres-vces[1])/(vces[3]-vces[1])
    except ZeroDivisionError:
        c2 = 0
    try:
        c3 = (thres-vces[0])/(vces[1]-vces[0])
    except ZeroDivisionError:
        c3 = 0
    try:
        c4 = (thres-vces[2])/(vces[3]-vces[2])
    except ZeroDivisionError:
        c4 = 0
    d1 = c2 - c1
    d2 = c4 - c3
    t = (c1 * d2 + c3) / (1 - d1 * d2)
    es = [(offset[0],offset[1]+c1),(offset[0]+1,offset[1]+c2),
            (offset[0]+c3,offset[1]),(offset[0]+c4,offset[1]+1),
            (offset[0]+t,offset[1]+c1*(1-t)+c2*t)]
    a = [[es[i[0]],es[i[1]]] for i in edges]
    return [[[i[0][0],i[1][0]],[i[0][1],i[1][1]]] for i in a],v[msdict[k][1]][1]
THRESHOLD = 0
IMG_SIZE = 1024
sc = 16

#Default game seeds
r5 = rng(seed=(4,5))
s5 = Simplex(2,r5)
r6 = rng(seed=(6,7))
s6 = Simplex(2,r6)

'''grid = [[s5([i*sc/IMG_SIZE,j*sc/IMG_SIZE]) for j in range(IMG_SIZE)] for i in range(IMG_SIZE)]
for i in range(IMG_SIZE-1):
  for j in range(IMG_SIZE-1):
    vces = (grid[i][j],grid[i+1][j],grid[i][j+1],grid[i+1][j+1])
    out = ms(THRESHOLD,vces,[i,j])
    for k in out:
      plt.plot(k[0],k[1],c="blue")
plt.show()'''

#These are a few of my favorite things (sorry, I meant colors)

GREEN=(64,255,0,255)
GRAY_GREEN=(128,192,64,255)
LIGHT_GREEN=(192,255,128,255)
DARK_GREEN=(64,128,0,255)
BROWN=(128,96,0,255)
LIGHT_BROWN=(192,160,0,255)
TAN=(192,160,128,255)
BLACK=(0,0,0,255)
DARK_GRAY=(64,64,64,255)
GRAY=(128,128,128,255)
LIGHT_GRAY=(192,192,192,255)
WHITE=(255,255,255,255)

#Loading a terrain value, will get more complicated
def load_grid(x,y,w,noise):
    return [min(1,max(-1,noise[0]((x/w,y/w))*5)),"grass" if noise[1]((x/w/3,y/w/3)) <= -0.25 else ("dirt" if noise[1]((x/w/3,y/w/3)) <= 0.25 else "stone")]

base64 = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/"

def convert64(value):
    v=np.abs(value)
    s=""
    while v>0:
        s=base64[v%64]+s
        v//=64
    if value<0:
        s="-"+s
    return s

def devert64(string):
    if string[0]=="-":
        s=string[1:]
    else:
        s=string
    v=0
    for i in s:
        v*=64
        try:
            v+=list(string).index(i)
        except ValueError:
            v+=0
    if string[0]=="-":
        v*=-1
    return v

def reveal_text(shielded_str):
    try:
        return b64.b64decode(shielded_str).decode('utf-8')
    except Exception:
        return "Error: Data corrupted in the Hydraulic Press."
    
def f(x):
    return x if x[1] not in Terrainer.transp else (-1,"grass")
#The game!
class Terrainer(arcade.Window):
    colors = {"grass":(192,255,128,255),
              "dirt":(128,80,0,255),
              "stone":(128,128,128,255)}
    names = ["grass","dirt","stone"]
    textures = {
        "grass":(LIGHT_GREEN,GREEN,GREEN,DARK_GREEN,GRAY_GREEN,LIGHT_GREEN,LIGHT_GREEN,LIGHT_GREEN),
        "dirt":(BROWN,BROWN,BROWN,LIGHT_BROWN,BROWN,LIGHT_BROWN,LIGHT_BROWN,BROWN),
        "stone":(GRAY,LIGHT_GRAY,WHITE,GRAY,LIGHT_GRAY,GRAY,DARK_GRAY,GRAY),
    }
    craftUI = {
        "stone":[(3,3),[(0,0),(1,0),(2,0)],[(1,2)],[(0,1,"0230"),(1,1,"5534"),(2,1,"2030")]]
    }
    craftRecp = {
        "stone":{
            ("grass","dirt","grass"):([0,0,0],[1,1,1],[3],["grass"],"0","Growing grass")
        }
    }
    ritn=dict()
    for a,b in craftRecp.items():
        for i,j in b.items():
            ritn[j[4]]=(a,i)
    pages = {
        "Main" : [
            "Main",
            [("[Movement]","Move"),("[Inventory]","Inv"),("[Items]","Item"),("[Modes]","Mode"),("[Mining & placing]","Edit"),("[Save]","Save")],
            ("Hello, creation. I live in a world quite different from yours. When I occasionally get the time, I might be able to write some tips for you "
            "or add other stuff to your world. However, had you not found this menu, that would all be for nothing. Click on one of the buttons above "
            "to learn more about your world."),
            "0"
        ],
        "Inv" : [
            "Inventory",
            [("[Back]","Main")],
            ("The inventory slots take up the first row, namely 1234567890-=. If you want to move your stuff around, Enter picks up and drops your stuff. "
            "If you only want to pick up or drop half, use Shift+Enter. The Z button is a slow delete and the X button is instant deletion. Click the "
            "diamond icon for me to do a detailed inventory inspection on you."),
            "1"
        ],
        "Item" : [
            "Items",
            [("[Back]","Main")],
            ("Items are very important in this world. They can be used to build or craft stuff (once I have time to add that to your world). There are "
            "currently three items. Dirt, Grass, and Stone. In creative or x-ray modes, you can use the search icon to search for the items you want "
            "and drag the slider to set how much error correction you can tolerate."),
            "2"
        ],
        "Mode" : [
            "Modes",
            [("[Back]","Main")],
            ("There are three modes you can access by clicking the top-right button. N stands for the normal mode. C stands for creative, which gives you " 
            "access to the search bar. X stands for x-ray, which allows you to bypass physics."),
            "3"
        ],
        "Edit" : [
            "Mining & Placing",
            [("[Back]","Main")],
            ("The world is pretty boring when you have nothing. Guess what? I gave you the ability to change the world you live in! You can click somewhere to gather that resource, also this uses up the land. "
            "You can also place down some resources by shift-clicking on where you want to place them, although you can only place it on an empty slot or "
            "pile it on top of more of that thing."),
            "4"
        ],
        "Save" : [
            "Save",
            [("[Back]","Main")],
            ("Inspired by your curiosity, I tried to see if I could make you and your world live longer. I tried cramming all the data in a file. The experiment proved successful, so now you can click that save button to cram the world into a file "
            "It should start with <CODE> and end with </CODE>. (all caps) I had to run my hydraulic press for it to fit, so it might look weird. And once you have one version of your world, you can run it again and again "
            "Also, you now can make a world to suit your needs. Just remember: the world might change, but your knowledge doesn't"),
            "5"
        ],
        "End" : [
            "End",
            [],
            (reveal_text("V3JpdHRlbiB3b3JkcyBhcmUgYSBtZXNzYWdlIHRvIHRoZSBmdXR1cmUuIFRoZSBwZXJzb24gcmVhZGluZyBpdCBpcyBhbHdheXMgZnVydGhlciBhaGVhZCBpbiB0aW1lIHRoYW4gdGhlIHBlcnNvbiB3cml0aW5nIGl0LiBJIGRvbid0IGtub3cgd2hhdCBkYXRlIHlvdSBhcmUgcmVhZGluZyB0aGVzZSB3b3Jkcywgd2hlcmUgeW91IGFyZSwgb3Igd2hhdCB5b3UncmUgdHJ5aW5nIHRvIGRvLkJ1dCB3aGVyZXZlciB5b3UgYXJlIGFuZCB3aGF0ZXZlciBwcm9ibGVtcyB5b3UncmUgdHJ5aW5nIHRvIHNvbHZlLCBJIGhvcGUgdGhhdCB0aGVzZSBtZXNzYWdlcyBoYXZlIGhlbHBlZC4gS2VlcCBidWlsZGluZywgYW5kIEkgd2lsbCBhbHdheXMgYmUgdGhlcmUgdG8gaGVscCB5b3UuIEkgYW0gc3BhY2V0aW1lLXRpbWVzcGFjZSBvbiBnaXRodWIsIGFuZCBnb29kIGx1Y2sgd2l0aCB5b3VyIGZ1dHVyZS5PaCwgYW5kIGFsc28gdGhpcyBpc24ndCB0aGUgZW5kIG9mIHlvdXIgam91cm5leS4gVGhvc2UgbGFzdCBsaW5lcyB3ZXJlIGZyb20gc29tZSBib29rLiBIb3cgbWFueSBjaGFwdGVycyBkb2VzIGl0IGhhdmU/")),
            #POV that one line of text that just seems to never end
            str(int(np.log10(float(devert64("C3q8YnBQMFrfFKPZ5AAAAAAA")))))
        ],
        "Actual End" : [
            "Recruitment",
            [],
            (reveal_text("QW5kIHlvdSBhY3R1YWxseSBzb2x2ZWQgdGhlIGxhc3QgcHV6emxlISBXYW50IHRvIGhlbHAgY29sbGFib3JhdGU/IEknbSBzcGFjdGltZS10aW1lc3BhY2Ugb24gZ2l0aHViLCBhbmQgdGhpcyByZXBvIGlzIHRlcnJhaW53b3JsZC4=")),
            str(int(np.log10(float(devert64("IE/OXj4lAmEQAAAA")))))
        ],
    }
    pitn=dict()
    for i,j in pages.items():
        pitn[j[3]]=i
    Textures={}
    transp=["grass"]
    def __init__(self,WIDTH=960, HEIGHT=720, FPS=60, PIX = 256, CHUNKSIZE=16, WSIZE = 32, SPEED=1, seed=[(4,5),(6,7)], MSPEED=16, name="terrainer"):
        super().__init__(WIDTH, HEIGHT, "Terrainer", update_rate=1/FPS,resizable=True)
        self.set_vsync(True)
        #Initializing variables...
        self.s = 64
        self.h = HEIGHT
        self.w = WIDTH
        self.p = PIX
        self.z = WSIZE
        self.sc = None
        self.grid = None
        self.lines = None
        self.clines = None
        self.bh = None
        self.bw = None
        self.cmouse=[0,0,0]
        self.sp = SPEED
        self.ch = []
        self.chs = CHUNKSIZE
        self.pos = np.array([0.0,0.0])
        self.nx=0
        self.ny=0
        self.n = seed
        self.vel = np.array([0.0,0.0])
        self.m = MSPEED
        self.lb = name
        self.inv = [[0,"grass"] for _ in range(12)]
        self.invslot = 0
        self.mode = 0
        self.mthing = 0
        self.mqty = 0
        self.delt = 0
        self.st = 0
        self.searchstr = ""
        self.strpos=0
        self.searchres=[]
        self.searchpg=0
        self.fuzz=0.25
        self.adjfuzz=False
        self.updres=False
        self.searchst=0
        self.modesw=False
        self.kpress=[]
        self.pg="Main"
        self.unlocked={"Main","Inv"}
        self.recip={
            "stone":[]
        }
        self.sch=[]
        self.scing=0
        self.ctable="NONE"
        self.cstate=[]
        self.cpos=0
        self.cslot=0
        self.cclick=0
        self.crecp=[None,None]
    def on_resize(self,width,height):
        #Resize handling: re-set width, height
        self.w = width
        self.h = height
        self.sc = min(self.w,self.h)/self.p
        self.bw = 0 if self.w < self.h else (self.w-self.h)/2
        self.bh = 0 if self.h < self.w else (self.h-self.w)/2
    def setup(self):
        #Sets up grid, segments
        self.grid = dict()
        self.lines = dict()
        self.clines = dict()
        self.sc = min(self.w,self.h)/self.p
        self.bw = 0 if self.w < self.h else (self.w-self.h)/2
        self.bh = 0 if self.h < self.w else (self.h-self.w)/2
        for b,t in Terrainer.textures.items():
            img = Image.new('RGBA', (len(t), 1))
            img.putdata(t)
            Terrainer.Textures[b]=arcade.Texture(img)
    def draw_line(self,x1,y1,x2,y2,texture):
        dx=x2-x1
        dy=y2-y1
        l=np.sqrt(dx**2+dy**2)
        a=np.degrees(np.atan2(dy,dx))
        cx=(x1+x2)/2
        cy=(y1+y2)/2
        arcade.draw_texture_rect(Terrainer.Textures[texture],arcade.XYWH(cx,cy,l,4),angle=-a)
    def on_draw(self):
        self.clear()
        #Chunk borders
        for i in range(int((self.pos[0]-self.p/2)//self.chs)+1,int((self.pos[0]+self.p/2)//self.chs)+1):
            arcade.draw_line(i*self.chs*self.sc-self.pos[0]*self.sc+self.p/2*self.sc+self.bw,self.bh,i*self.chs*self.sc-self.pos[0]*self.sc+self.p/2*self.sc+self.bw,self.bh+self.sc*self.p,WHITE,2)
        for i in range(int((self.pos[1]-self.p/2)//self.chs)+1,int((self.pos[1]+self.p/2)//self.chs)+1):
            arcade.draw_line(self.bw,i*self.chs*self.sc-self.pos[1]*self.sc+self.p/2*self.sc+self.bh,self.bw+self.sc*self.p,i*self.chs*self.sc-self.pos[1]*self.sc+self.p/2*self.sc+self.bh,WHITE,2)
        #Draws all segments
        for i in range(int(self.pos[0]-self.p/2+1),int(self.pos[0]+self.p/2)):
            for j in range(int(self.pos[1]-self.p/2+1),int(self.pos[1]+self.p/2)):
                try:
                    m = self.lines[(i,j)][1]
                    for k in self.lines[(i,j)][0]:
                        self.draw_line((k[0][0]-self.pos[0]+self.p/2)*self.sc+self.bw,(k[1][0]-self.pos[1]+self.p/2)*self.sc+self.bh,
                                        (k[0][1]-self.pos[0]+self.p/2)*self.sc+self.bw,(k[1][1]-self.pos[1]+self.p/2)*self.sc+self.bh,
                                        m)
                        arcade.draw_circle_filled((k[0][0]-self.pos[0]+self.p/2)*self.sc+self.bw,(k[1][0]-self.pos[1]+self.p/2)*self.sc+self.bh,
                                                  0.05*self.sc,Terrainer.colors[m])
                        arcade.draw_circle_filled((k[0][0]*0.75+k[0][1]*0.25-self.pos[0]+self.p/2)*self.sc+self.bw,(k[1][0]*0.75+k[1][1]*0.25-self.pos[1]+self.p/2)*self.sc+self.bh,
                                                  0.05*self.sc,Terrainer.colors[m])
                except KeyError:
                    0
        #Draws character
        arcade.draw_circle_filled(self.bw+self.p*self.sc/2,self.bh+self.p*self.sc/2,0.5*self.sc,(192,192,192,255))
        arcade.draw_circle_filled(self.bw+self.p*self.sc/2+0.2*self.sc,self.bh+self.p*self.sc/2+0.1*self.sc,0.125*self.sc,(0,0,0,255))
        arcade.draw_circle_filled(self.bw+self.p*self.sc/2-0.2*self.sc,self.bh+self.p*self.sc/2+0.1*self.sc,0.125*self.sc,(0,0,0,255))
        #Drawing your inventory
        for i in range(len(self.inv)):
            z = arcade.Sprite()
            z.texture = arcade.load_texture(textures+"itembox.png")
            z.scale = 32/self.s
            z.center_x = self.w-16
            z.center_y = self.h/2+16*len(self.inv)-16-32*i
            arcade.draw_sprite(z)
            if self.inv[i][0] == 0:
                continue
            z = arcade.Sprite()
            z.texture = arcade.load_texture(textures+"tiles/"+self.inv[i][1]+".png")
            z.scale = 16/self.s
            z.center_x = self.w-16
            z.center_y = self.h/2+16*len(self.inv)-16-32*i
            arcade.draw_sprite(z)
            c = len(str(int(self.inv[i][0])))
            for j in range(c):
                x = str(int(self.inv[i][0]))[j]
                z.texture = arcade.load_texture(textures+"Font-white/tile"+x+".png")
                z.scale = 8/self.s
                z.center_x = self.w-16-c*2+2+4*j
                z.center_y = self.h/2+16*len(self.inv)-16-32*i
                arcade.draw_sprite(z)
        z = arcade.Sprite()
        z.texture = arcade.load_texture(textures+"selector.png")
        z.scale = 32/self.s
        if self.mqty == 0:
            z.center_x = self.w-48
        else:
            z.center_x = self.w-80
        z.center_y = self.h/2+16*len(self.inv)-16-32*self.invslot
        arcade.draw_sprite(z)
        #Gamemode
        t="x-ray" if self.mode==2 else "creative" if self.mode==1 else "normal"
        for j in range(len(t)):
            if t[j] != " ":
                z = arcade.Sprite()
                z.texture = arcade.load_texture(textures+"Font-white/tile"+t[j]+".png")
                z.scale = 32/self.s
                z.center_x = self.w-len(t)*24+j*24-72
                z.center_y = self.h-32
                arcade.draw_sprite(z)
        #Mode switching
        if self.modesw==0:
            arcade.draw_circle_filled(self.w-36,self.h-36,24,bkg)
        else:
            arcade.draw_circle_filled(self.w-36,self.h-36,24,(57,255,20))
            z = arcade.Sprite()
            z.texture = arcade.load_texture(textures+"Font-white/tilen.png")
            z.scale = 32/self.s
            z.center_x = self.w-36
            z.center_y = self.h-36
            arcade.draw_sprite(z)
            arcade.draw_circle_filled(self.w-36,self.h-84,24,(28,232,137))
            z = arcade.Sprite()
            z.texture = arcade.load_texture(textures+"Font-white/tilec.png")
            z.scale = 32/self.s
            z.center_x = self.w-36
            z.center_y = self.h-84
            arcade.draw_sprite(z)
            arcade.draw_circle_filled(self.w-36,self.h-132,24,(0,210,255))
            z = arcade.Sprite()
            z.texture = arcade.load_texture(textures+"Font-white/tilex.png")
            z.scale = 32/self.s
            z.center_x = self.w-36
            z.center_y = self.h-132
            arcade.draw_sprite(z)
        #Mode buttons
        arcade.draw_circle_filled(36,self.h-36,24,bkg)
        arcade.draw_polygon_filled([[24,self.h-36],[36,self.h-24],[48,self.h-36],[36,self.h-48]],(255,255,255,255))
        arcade.draw_circle_filled(36,self.h-108,24,bkg)
        arcade.draw_polygon_outline([[24,self.h-96],[24,self.h-120],[48,self.h-120],[48,self.h-96]],(255,255,255,255))
        arcade.draw_polygon_filled([[24,self.h-96],[24,self.h-120],[30,self.h-120],[30,self.h-96]],(255,255,255,255))
        arcade.draw_circle_filled(36,self.h-180,24,bkg)
        arcade.draw_polygon_outline([[24,self.h-168],[24,self.h-192],[48,self.h-192],[48,self.h-168]],(255,255,255,255))
        arcade.draw_line(36,self.h-168,36,self.h-192,(255,255,255,255))
        arcade.draw_line(24,self.h-180,48,self.h-180,(255,255,255,255))
        arcade.draw_circle_filled(36,self.h-252,24,bkg)
        arcade.draw_polygon_filled([[24,self.h-246],[24,self.h-240],[42,self.h-240],[48,self.h-246]],(255,255,255,255))
        arcade.draw_polygon_outline([[24,self.h-264],[24,self.h-246],[48,self.h-246],[48,self.h-264]],(255,255,255,255))
        arcade.draw_circle_filled(36,self.h-253,6,(255,255,255,255))
        if self.mode>0:
            arcade.draw_circle_filled(36,self.h-324,24,bkg)
            arcade.draw_circle_outline(30,self.h-318,6*2**0.5,(255,255,255,255))
            arcade.draw_line(36,self.h-322,48,self.h-336,(255,255,255,255))
        #Coordinates background
        arcade.draw_rect_filled(arcade.rect.XYWH(self.w/2, 96, self.w-192, 192),bkg)
        arcade.draw_circle_filled(96,96,96,bkg)
        arcade.draw_circle_filled(self.w-96,96,96,bkg)
        #Notice box
        if self.st != 0:
            arcade.draw_rect_filled(arcade.rect.XYWH(self.w/2, self.h/2, self.w-192, self.h-384),bkg)
            arcade.draw_rect_filled(arcade.rect.XYWH(self.w/2, self.h/2, self.w-384, self.h-192),bkg)
            arcade.draw_circle_filled(192,192,96,bkg)
            arcade.draw_circle_filled(self.w-192,192,96,bkg)
            arcade.draw_circle_filled(192,self.h-192,96,bkg)
            arcade.draw_circle_filled(self.w-192,self.h-192,96,bkg)
        #Coordinates
        s=f"({self.pos[0]:+.2f},{self.pos[1]:+.2f})"
        c=len(s)
        for j in range(c):
            x = s[j]
            z.texture = arcade.load_texture(textures+"Font-white/tile"+x+".png")
            z.scale = 64/self.s
            z.center_x = self.w/2-c*24+16+48*j
            z.center_y = 96
            arcade.draw_sprite(z)
        if self.st == 1:
            arcade.draw_circle_filled(192,192,24,(255,128,128,255))
            for i in range(12):
                z = arcade.Sprite()
                z.texture = arcade.load_texture(textures+"itembox.png")
                z.scale = (self.h-384)/12/self.s
                z.center_x = 192
                z.center_y = self.h/2+(self.h-384)/2-(self.h-384)/24-(self.h-384)/12*i
                arcade.draw_sprite(z)
                if self.inv[i][0] == 0:
                    continue
                z = arcade.Sprite()
                z.texture = arcade.load_texture(textures+"tiles/"+self.inv[i][1]+".png")
                z.scale = (self.h-384)/24/self.s
                z.center_x = 192
                z.center_y = self.h/2+(self.h-384)/2-(self.h-384)/24-(self.h-384)/12*i
                arcade.draw_sprite(z)
                t = "{:6} ".format("{:.3f}".format(self.inv[i][0]))
                t += self.inv[i][1]
                for j in range(len(t)):
                    if t[j] != " ":
                        z = arcade.Sprite()
                        z.texture = arcade.load_texture(textures+"Font-white/tile"+t[j]+".png")
                        z.scale = (self.h-384)/24/self.s
                        z.center_x = 256 + j*(self.h-384)/24
                        z.center_y = self.h/2+(self.h-384)/2-(self.h-384)/24-(self.h-384)/12*i
                        arcade.draw_sprite(z)
        if self.st == 2:
            arcade.draw_circle_filled(192,192,24,(255,128,128,255))
            t = self.searchstr
            for j in range(len(t)):
                if t[j] != " ":
                    z = arcade.Sprite()
                    z.texture = arcade.load_texture(textures+"Font-white/tile"+t[j]+".png")
                    z.scale = 32/self.s
                    z.center_x = 192 + j*24
                    z.center_y = self.h-192
                    arcade.draw_sprite(z)
            arcade.draw_line(180+24*self.strpos,self.h-176,180+24*self.strpos,self.h-208,(255,255,255,255*int((time.time()*2)%2)))
            arcade.draw_line(self.w-192,self.h-192,self.w-192,192,(255,255,255,255),5)
            arcade.draw_circle_filled(self.w-192,192+(1-self.fuzz)*(self.h-384),24,(57-57*self.fuzz,255-45*self.fuzz,20+235*self.fuzz,255))
            for i in range(6):
                for j in range(6):
                    if 6*self.searchpg+6*j+i<len(self.searchres):
                        b=self.searchres[int(6*self.searchpg+6*j+i)]
                        z = arcade.Sprite()
                        z.texture = arcade.load_texture(textures+"itembox.png")
                        z.scale = (self.h-432)/6/self.s
                        z.center_x = self.w/2-(self.h-432)/2+(self.h-432)/12+(self.h-432)/6*i
                        z.center_y = self.h/2+(self.h-432)/2-(self.h-432)/12-(self.h-432)/6*j
                        arcade.draw_sprite(z)
                        z = arcade.Sprite()
                        z.texture = arcade.load_texture(textures+"Tiles/"+b+".png")
                        z.scale = (self.h-432)/12/self.s
                        z.center_x = self.w/2-(self.h-432)/2+(self.h-432)/12+(self.h-432)/6*i
                        z.center_y = self.h/2+(self.h-432)/2-(self.h-432)/12-(self.h-432)/6*j
                        arcade.draw_sprite(z)
                        if self.searchst==1:
                            t=b
                            for k in range(len(t)):
                                if t[k] != " ":
                                    z = arcade.Sprite()
                                    z.texture = arcade.load_texture(textures+"Font-white/tile"+t[k]+".png")
                                    z.scale = (self.h-432)/9/self.s/len(t)
                                    z.center_x = self.w/2-(self.h-432)/2+(self.h-432)/12+(self.h-432)/6*i-(self.h-432)/18+(self.h-432)/18/len(t)+(self.h-432)/9/len(t)*k
                                    z.center_y = self.h/2+(self.h-432)/2-(self.h-432)/8-(self.h-432)/6*j
                                    arcade.draw_sprite(z)
                            v=levenshtein(self.searchstr.lower(),b)
                            t=f"{v:.2f}"
                            v=max(0,min(1,v))
                            for k in range(len(t)):
                                if t[k] != " ":
                                    z = arcade.Sprite()
                                    z.texture = arcade.load_texture(textures+"Font-white/tile"+t[k]+".png")
                                    z.scale = (self.h-432)/9/self.s/len(t)
                                    z.center_x = self.w/2-(self.h-432)/2+(self.h-432)/12+(self.h-432)/6*i-(self.h-432)/18+(self.h-432)/18/len(t)+(self.h-432)/9/len(t)*k
                                    z.center_y = self.h/2+(self.h-432)/2-(self.h-432)/24-(self.h-432)/6*j
                                    z.color = (57-57*v,255-45*v,20+235*v,255)
                                    arcade.draw_sprite(z)
        if self.st==3:
            arcade.draw_circle_filled(192,192,24,(255,128,128,255))
            dat=Terrainer.pages[self.pg]
            rows=3+len(dat[1])+np.ceil(len(dat[2])/64)
            size=min((self.h-384)/rows/self.s,(self.w-384)/48/self.s)
            t=dat[0]
            for j in range(len(t)):
                if t[j] != " ":
                    z = arcade.Sprite()
                    z.texture = arcade.load_texture(textures+"Font-white/tile"+t[j]+".png")
                    z.scale = size*2
                    z.center_x = 192+size*3/4*self.s+3/2*self.s*size*j
                    z.center_y = self.h-192-size*self.s
                    arcade.draw_sprite(z)
            for i in range(len(dat[1])):
                if dat[1][i][1] in self.unlocked:
                    t=dat[1][i][0]
                    for j in range(len(t)):
                        if t[j] != " ":
                            z = arcade.Sprite()
                            z.texture = arcade.load_texture(textures+"Font-white/tile"+t[j]+".png")
                            z.scale = size
                            z.center_x = 192+size*3/8*self.s+3/4*self.s*size*j
                            z.center_y = self.h-192-size*5/2*self.s-size*i*self.s
                            arcade.draw_sprite(z)
            t=dat[2]
            for j in range(len(t)):
                if t[j] != " ":
                    z = arcade.Sprite()
                    z.texture = arcade.load_texture(textures+"Font-white/tile"+t[j]+".png")
                    z.scale = size
                    z.center_x = 192+size*3/8*self.s+3/4*self.s*size*(j%64)
                    z.center_y = self.h-192-size*7/2*self.s-size*len(dat[1])*self.s-size*self.s*(j//64)
                    arcade.draw_sprite(z)
        if self.st==4:
            arcade.draw_circle_filled(192,192,24,(255,128,128,255))
            UIdat=Terrainer.craftUI[self.ctable]
            Recpdat=Terrainer.craftRecp[self.ctable]
            rows,cols=UIdat[0]
            size=min((self.h-384)/rows/self.s,(self.w-384)/cols/self.s)
            bw=self.w/2-size*cols*self.s/2
            bh=self.h/2-size*rows*self.s/2
            for i,j in zip(UIdat[1],self.cstate[0]):
                z = arcade.Sprite()
                z.texture = arcade.load_texture(textures+"itembox.png")
                z.scale = size
                z.color=(128,255,128)
                z.center_x = bw+i[0]*self.s*size+self.s/2*size
                z.center_y = bh+i[1]*self.s*size+self.s/2*size
                arcade.draw_sprite(z)
                if j[0]>0:
                    z = arcade.Sprite()
                    z.texture = arcade.load_texture(textures+"Tiles/"+j[1]+".png")
                    z.scale = size/2
                    z.center_x = bw+i[0]*self.s*size+self.s/2*size
                    z.center_y = bh+i[1]*self.s*size+self.s/2*size
                    arcade.draw_sprite(z)
                    t=f"{j[0]:.1f}"
                    for j in range(len(t)):
                        x = t[j]
                        z.texture = arcade.load_texture(textures+"Font-white/tile"+x+".png")
                        z.scale = size/2/len(t)
                        z.center_x = bw+i[0]*self.s*size+self.s/2*size-size/8*self.s+size/8/len(t)*self.s+j*size/4/len(t)*self.s
                        z.center_y = bh+i[1]*self.s*size+self.s/2*size
                        arcade.draw_sprite(z)
            for i,j in zip(UIdat[2],self.cstate[1]):
                z = arcade.Sprite()
                z.texture = arcade.load_texture(textures+"itembox.png")
                z.scale = size
                z.color=(128,128,255)
                z.center_x = bw+i[0]*self.s*size+self.s/2*size
                z.center_y = bh+i[1]*self.s*size+self.s/2*size
                arcade.draw_sprite(z)
                if j[0]>0:
                    z = arcade.Sprite()
                    z.texture = arcade.load_texture(textures+"Tiles/"+j[1]+".png")
                    z.scale = size/2
                    z.center_x = bw+i[0]*self.s*size+self.s/2*size
                    z.center_y = bh+i[1]*self.s*size+self.s/2*size
                    arcade.draw_sprite(z)
                    t=f"{j[0]:.1f}"
                    for j in range(len(t)):
                        x = t[j]
                        z.texture = arcade.load_texture(textures+"Font-white/tile"+x+".png")
                        z.scale = size/2/len(t)
                        z.center_x = bw+i[0]*self.s*size+self.s/2*size-size/8*self.s+size/8/len(t)*self.s+j*size/4/len(t)*self.s
                        z.center_y = bh+i[1]*self.s*size+self.s/2*size
                        arcade.draw_sprite(z)
            for i in UIdat[3]:
                z = arcade.Sprite()
                z.texture = arcade.load_texture(textures+"Background/"+i[2]+".png")
                z.scale = size
                z.center_x = bw+i[0]*self.s*size+self.s/2*size
                z.center_y = bh+i[1]*self.s*size+self.s/2*size
                arcade.draw_sprite(z)
            i=(UIdat[1]+UIdat[2])[self.cslot]
            z = arcade.Sprite()
            z.texture = arcade.load_texture(textures+"selector.png")
            z.scale = size/2
            z.center_x = bw+i[0]*self.s*size-self.s/4*size
            z.center_y = bh+i[1]*self.s*size+self.s/2*size
            arcade.draw_sprite(z)
            if tuple([i[1] for i in self.cstate[0]]) in Recpdat.keys():
                arcade.draw_circle_filled(192,self.h-192,24,(128,255,128,255))
        if self.st==5:
            arcade.draw_circle_filled(192,192,24,(255,128,128,255))
            if self.crecp[0]==None:
                rows=2+len(Terrainer.craftRecp.keys())
                size=min((self.h-384)/rows/self.s,(self.w-384)/48/self.s)
                t="Recipe book"
                for j in range(len(t)):
                    if t[j] != " ":
                        z = arcade.Sprite()
                        z.texture = arcade.load_texture(textures+"Font-white/tile"+t[j]+".png")
                        z.scale = size*2
                        z.center_x = 192+size*3/4*self.s+3/2*self.s*size*j
                        z.center_y = self.h-192-size*self.s
                        arcade.draw_sprite(z)
                for i in range(len(Terrainer.craftRecp.keys())):
                    t="["+list(Terrainer.craftRecp.keys())[i]+"]"
                    for j in range(len(t)):
                        if t[j] != " ":
                            z = arcade.Sprite()
                            z.texture = arcade.load_texture(textures+"Font-white/tile"+t[j]+".png")
                            z.scale = size
                            z.center_x = 192+size*3/8*self.s+3/4*self.s*size*j
                            z.center_y = self.h-192-size*5/2*self.s-size*i*self.s
                            arcade.draw_sprite(z)
            elif self.crecp[1]==None:
                rows=2+len(Terrainer.craftRecp.keys())
                size=min((self.h-384)/rows/self.s,(self.w-384)/48/self.s)
                recps=Terrainer.craftRecp[self.crecp[0]]
                t=self.crecp[0]
                for j in range(len(t)):
                    if t[j] != " ":
                        z = arcade.Sprite()
                        z.texture = arcade.load_texture(textures+"Font-white/tile"+t[j]+".png")
                        z.scale = size*2
                        z.center_x = 192+size*3/4*self.s+3/2*self.s*size*j
                        z.center_y = self.h-192-size*self.s
                        arcade.draw_sprite(z)
                for i in range(len(recps.keys())):
                    t="["+recps[list(recps.keys())[i]][5]+"]"
                    for j in range(len(t)):
                        if t[j] != " ":
                            z = arcade.Sprite()
                            z.texture = arcade.load_texture(textures+"Font-white/tile"+t[j]+".png")
                            z.scale = size
                            z.center_x = 192+size*3/8*self.s+3/4*self.s*size*j
                            z.center_y = self.h-192-size*5/2*self.s-size*i*self.s
                            arcade.draw_sprite(z)
            else:
                UIdat=Terrainer.craftUI[self.crecp[0]]
                Recpdat=Terrainer.craftRecp[self.crecp[0]]
                rows,cols=UIdat[0]
                size=min((self.h-384)/rows/self.s,(self.w-384)/cols/self.s)
                bw=self.w/2-size*cols*self.s/2
                bh=self.h/2-size*rows*self.s/2
                for i,j in zip(UIdat[1],zip([i+j for i,j in zip(Recpdat[self.crecp[1]][1],Recpdat[self.crecp[1]][0])],self.crecp[1])):
                    z = arcade.Sprite()
                    z.texture = arcade.load_texture(textures+"itembox.png")
                    z.scale = size
                    z.color=(128,255,128)
                    z.center_x = bw+i[0]*self.s*size+self.s/2*size
                    z.center_y = bh+i[1]*self.s*size+self.s/2*size
                    arcade.draw_sprite(z)
                    if j[0]>0:
                        z = arcade.Sprite()
                        z.texture = arcade.load_texture(textures+"Tiles/"+j[1]+".png")
                        z.scale = size/2
                        z.center_x = bw+i[0]*self.s*size+self.s/2*size
                        z.center_y = bh+i[1]*self.s*size+self.s/2*size
                        arcade.draw_sprite(z)
                        t=f"{j[0]:.1f}"
                        for j in range(len(t)):
                            x = t[j]
                            z.texture = arcade.load_texture(textures+"Font-white/tile"+x+".png")
                            z.scale = size/2/len(t)
                            z.center_x = bw+i[0]*self.s*size+self.s/2*size-size/8*self.s+size/8/len(t)*self.s+j*size/4/len(t)*self.s
                            z.center_y = bh+i[1]*self.s*size+self.s/2*size
                            arcade.draw_sprite(z)
                for i,j in zip(UIdat[2],zip(Recpdat[self.crecp[1]][2],Recpdat[self.crecp[1]][3])):
                    z = arcade.Sprite()
                    z.texture = arcade.load_texture(textures+"itembox.png")
                    z.scale = size
                    z.color=(128,128,255)
                    z.center_x = bw+i[0]*self.s*size+self.s/2*size
                    z.center_y = bh+i[1]*self.s*size+self.s/2*size
                    arcade.draw_sprite(z)
                    if j[0]>0:
                        z = arcade.Sprite()
                        z.texture = arcade.load_texture(textures+"Tiles/"+j[1]+".png")
                        z.scale = size/2
                        z.center_x = bw+i[0]*self.s*size+self.s/2*size
                        z.center_y = bh+i[1]*self.s*size+self.s/2*size
                        arcade.draw_sprite(z)
                        t=f"{j[0]:.1f}"
                        for j in range(len(t)):
                            x = t[j]
                            z.texture = arcade.load_texture(textures+"Font-white/tile"+x+".png")
                            z.scale = size/2/len(t)
                            z.center_x = bw+i[0]*self.s*size+self.s/2*size-size/8*self.s+size/8/len(t)*self.s+j*size/4/len(t)*self.s
                            z.center_y = bh+i[1]*self.s*size+self.s/2*size
                            arcade.draw_sprite(z)
                for i in UIdat[3]:
                    z = arcade.Sprite()
                    z.texture = arcade.load_texture(textures+"Background/"+i[2]+".png")
                    z.scale = size
                    z.center_x = bw+i[0]*self.s*size+self.s/2*size
                    z.center_y = bh+i[1]*self.s*size+self.s/2*size
                    arcade.draw_sprite(z)
    def on_update(self,delta):
        self.nx=int(round(self.pos[0]))
        self.ny=int(round(self.pos[1]))
        opos=self.pos
        delta=min(delta,0.02)
        #Loading chunks
        if self.st == 0:
            if self.delt:
                self.inv[self.invslot][0] = max(0,self.inv[self.invslot][0]-self.sp*delta)
            for i in range(int((self.pos[0]-self.p/2)//self.chs)-1,int((self.pos[0]+self.p/2)//self.chs)+2):
                for j in range(int((self.pos[1]-self.p/2)//self.chs)-1,int((self.pos[1]+self.p/2)//self.chs)+2):
                    if (i,j) not in self.ch:
                        self.ch.append((i,j))
                        #Calculating terrain
                        for k in range(self.chs+1):
                            for l in range(self.chs+1):
                                wx=i*self.chs+k
                                wy=j*self.chs+l
                                self.grid[(wx,wy)] = load_grid(wx,wy,self.z,[Simplex(2,rng(i)) for i in self.n])
                        #Initializing segments
                        for k in range(self.chs):
                            for l in range(self.chs):
                                wx=i*self.chs+k
                                wy=j*self.chs+l
                                try:
                                    self.lines[(wx,wy)] = ms(0,(self.grid[(wx,wy)],self.grid[(wx+1,wy)],self.grid[(wx,wy+1)],self.grid[(wx+1,wy+1)]),[wx,wy])
                                except KeyError:
                                    0
                                try:
                                    self.clines[(wx,wy)] = ms(0,(f(self.grid[(wx,wy)]),f(self.grid[(wx+1,wy)]),f(self.grid[(wx,wy+1)]),f(self.grid[(wx+1,wy+1)])),[wx,wy])
                                except KeyError:
                                    0
                    if (i,j) in self.sch:
                        for k in range(self.chs):
                            for l in range(self.chs):
                                wx=i*self.chs+k
                                wy=j*self.chs+l
                                try:
                                    self.lines[(wx,wy)] = ms(0,(self.grid[(wx,wy)],self.grid[(wx+1,wy)],self.grid[(wx,wy+1)],self.grid[(wx+1,wy+1)]),[wx,wy])
                                except KeyError:
                                    0
                                try:
                                    self.clines[(wx,wy)] = ms(0,(f(self.grid[(wx,wy)]),f(self.grid[(wx+1,wy)]),f(self.grid[(wx,wy+1)]),f(self.grid[(wx+1,wy+1)])),[wx,wy])
                                except KeyError:
                                    0
                        self.sch.remove((i,j))
            #Colliding
            ploc = Point(float(self.pos[0]), float(self.pos[1]))
            pvel = Point(float(self.vel[0]), float(self.vel[1]))
            for _ in range(5):
                ploc += pvel*delta*self.m/5
                if self.mode!=2:
                    for _ in range(5): #multiplicity to (hopefully) fully resolve
                        iloc = Point(int(np.floor(ploc.x)),int(np.floor(ploc.y)))
                        lloc = ploc-iloc
                        #ploc is my current position, iloc is the reference point, lloc is the local position
                        collide = []
                        for i in range(-1, 2):
                            for j in range(-1, 2):
                                for l0 in self.clines[(i+iloc.x,j+iloc.y)][0]:
                                    a = Point(l0[0][0], l0[1][0])-iloc
                                    b = Point(l0[0][1], l0[1][1])-iloc
                                    collide.append((a, b))
                        for i in collide:
                            a=push_distance(lloc,0.5,i[0],i[1])
                            if a!=None:
                                ploc+=a
            self.pos=[ploc.x,ploc.y]
            #Changing mouse data to match
            self.cmouse[0]+=self.pos[0]-opos[0]
            self.cmouse[1]+=self.pos[1]-opos[1]
            #Testing for minability, mining
            if self.cmouse[2]!=0:
                try:
                    if "Edit" in self.unlocked:
                        self.unlocked.add("Mode")
                        self.unlocked.add("Save")
                    k = self.cmouse[0]
                    l = self.cmouse[1]
                    if self.cmouse[2] == 1:
                        if self.grid[(k,l)][1] == self.inv[self.invslot][1] and self.cmouse[2] == 1 and self.inv[self.invslot][0]<64:
                            a = self.grid[(k,l)][0]
                            self.grid[(k,l)][0] = max(-1, self.grid[(k,l)][0]-min(delta*self.sp,min(delta*self.sp,64-self.inv[self.invslot][0])))
                            self.inv[self.invslot][0] += a - self.grid[(k,l)][0]
                        elif self.inv[self.invslot][0] == 0:
                            self.inv[self.invslot][1] = self.grid[(k,l)][1]
                        else:
                            sf=0
                            for i in range(12):
                                if self.inv[i][1]==self.grid[(k,l)][1] and 0<self.inv[i][0]<64:
                                    a = self.grid[(k,l)][0]
                                    self.grid[(k,l)][0] = max(-1, self.grid[(k,l)][0]-min(delta*self.sp,min(delta*self.sp,64-self.inv[i][0])))
                                    self.inv[i][0] += a - self.grid[(k,l)][0]
                                    sf=1
                                    break
                            if sf==0:
                                for i in range(12):
                                    if self.inv[i][0]==0:
                                        self.inv[i][1]=self.grid[(k,l)][1]
                                        a = self.grid[(k,l)][0]
                                        self.grid[(k,l)][0] = max(-1, self.grid[(k,l)][0]-min(delta*self.sp,min(delta*self.sp,64-self.inv[i][0])))
                                        self.inv[i][0] += a - self.grid[(k,l)][0]
                                        break
                    if self.cmouse[2] == 2:
                        if self.grid[(k,l)][1] == self.inv[self.invslot][1]:
                            a = self.grid[(k,l)][0]
                            self.grid[(k,l)][0] = min(1, self.grid[(k,l)][0]+min(delta*self.sp,self.inv[self.invslot][0]))
                            self.inv[self.invslot][0] -= self.grid[(k,l)][0] - a
                        elif self.grid[(k,l)][0] == -1:
                            self.grid[(k,l)][1] = self.inv[self.invslot][1]         
                    for (i,j) in [(k-1,l-1),(k,l-1),(k-1,l),(k,l)]:
                        try:
                            self.lines[(i,j)] = ms(0,(self.grid[(i,j)],self.grid[(i+1,j)],self.grid[(i,j+1)],self.grid[(i+1,j+1)]),[i,j])
                            self.clines[(i,j)] = ms(0,(f(self.grid[(i,j)]),f(self.grid[(i+1,j)]),f(self.grid[(i,j+1)]),f(self.grid[(i+1,j+1)])),[i,j])
                        except KeyError:
                            0
                except KeyError:
                    0
        if self.updres:
            self.searchres=[]
            if self.searchstr=="":
                self.searchres=Terrainer.names
                self.searchres.sort()
            else:
                for i in Terrainer.names:
                    if levenshtein(self.searchstr.lower(),i) <= self.fuzz:
                        self.searchres.append(i)
                self.searchres.sort(key=lambda x: levenshtein(self.searchstr.lower(),x))
                self.updres = 0
        self.vel[0]=("RIGHT" in self.kpress)-("LEFT" in self.kpress)
        self.vel[1]=("UP" in self.kpress)-("DOWN" in self.kpress)
        if self.cclick==1 and self.st==4 and tuple([i[1] for i in self.cstate[0]]) in Terrainer.craftRecp[self.ctable].keys():
            recp=Terrainer.craftRecp[self.ctable][tuple([i[1] for i in self.cstate[0]])]
            if (np.array([i[0] for i in self.cstate[0]])>=np.array(recp[0])).all:
                a=delta
                for i,j in zip(self.cstate[0],recp[1]):
                    if j>0:
                        a = min(a,i[0]/j)
                for i,j,k in zip(self.cstate[1],recp[2],recp[3]):
                    if j>0:
                        if i[1]==k or i[0]==0:
                            a = min(a,(64-i[0])/j)
                for i in range(len(self.cstate[0])):
                    self.cstate[0][i][0]-=a*recp[1][i]
                for i in range(len(self.cstate[1])):
                    self.cstate[1][i][1]=recp[3][i]
                    self.cstate[1][i][0]+=a*recp[2][i]
                if tuple([i[1] for i in self.cstate[0]]) not in self.recip[self.ctable]:
                    self.recip[self.ctable].append(tuple([i[1] for i in self.cstate[0]]))
    def on_mouse_press(self,x,y,buttons,modifiers):
        #Calculating click position
        ux = (x-self.w/2)/self.sc+self.pos[0]
        uy = (y-self.h/2)/self.sc+self.pos[1]
        self.cmouse = [round(ux),round(uy),(1 if modifiers == 0 else 2)]
        if self.st!=0 and (x-192)**2+(y-192)**2<=576: #Exit button
            if self.st!=4:
                self.st=0
            elif (np.array([i[0] for i in self.cstate[0]+self.cstate[1]]) == np.array([0 for _ in self.cstate[0]+self.cstate[1]])).all():
                self.st=0
        if (x-192)**2+(y+192-self.h)**2<=576 and self.st==4: #Craft button
            self.cclick=1
        if self.st!=4 and not self.scing:
            if self.st==2 and abs(x-self.w+192)<=24 and self.h-168>=y>=168: #Fuzziness slider
                self.fuzz=min(1,max(0,1-(y-192)/(self.h-384)))
                self.adjfuzz=True
                self.updres=True
            elif self.st==2 and modifiers == arcade.key.MOD_SHIFT: #Developer's search bar
                self.searchst = 1-self.searchst
            elif self.st==2 and self.w/2-(self.h-432)/2<=x<=self.w/2+(self.h-432)/2 and 216<=y<=self.h-216: #Selecting menu items
                gx=np.floor((6*x-3*self.w+3*self.h-1296)/(self.h-432))
                gy=5-np.floor((6*y-1296)/(self.h-432))
                i=int(gx+gy*6+self.searchpg*6)
                if i<len(self.searchres):
                    self.inv[self.invslot][0]=64
                    self.inv[self.invslot][1]=self.searchres[i]
            elif self.modesw==0 and (x-self.w+36)**2+(y-self.h+36)**2<=576: #Mode switch button
                self.modesw=1
            elif self.modesw==1 and (x-self.w+36)**2+(y-self.h+36)**2<=576: #Normal
                self.modesw=0
                self.mode=0
            elif self.modesw==1 and (x-self.w+36)**2+(y-self.h+84)**2<=576: #Creative
                self.modesw=0
                self.mode=1
            elif self.modesw==1 and (x-self.w+36)**2+(y-self.h+132)**2<=576: #Xray
                self.modesw=0
                self.mode=2
            elif (x-36)**2+(y-self.h+36)**2<=576: #Inventory
                self.st=1
            elif (x-36)**2+(y-self.h+324)**2<=576 and self.mode>0: #Search bar
                self.st=2
            elif (x-36)**2+(y-self.h+108)**2<=576: #Manual
                self.st=3
            elif self.st==3: #Manual Link
                dat=Terrainer.pages[self.pg]
                rows=3+len(dat[1])+np.ceil(len(dat[2])/64)
                size=min((self.h-384)/rows/self.s,(self.w-384)/48/self.s)
                row=int(np.floor((self.h-192-y)/size/self.s)-2)
                if 0<=row<len(dat[1]):
                    if dat[1][int(row)][1] in self.unlocked:
                        self.pg=dat[1][int(row)][1]
            elif self.st==5 and self.crecp[0]==None: #Book Link
                rows=2+len(Terrainer.craftRecp.keys())
                size=min((self.h-384)/rows/self.s,(self.w-384)/48/self.s)
                row=int(np.floor((self.h-192-y)/size/self.s)-2)
                if 0<=row<len(Terrainer.craftRecp.keys()):
                    self.crecp=(list(Terrainer.craftRecp.keys())[row],None)
            elif self.st==5 and self.crecp[1]==None: #Book Link 2
                recps=Terrainer.craftRecp[self.crecp[0]]
                rows=2+len(recps.keys())
                size=min((self.h-384)/rows/self.s,(self.w-384)/48/self.s)
                row=int(np.floor((self.h-192-y)/size/self.s)-2)
                if 0<=row<len(recps.keys()):
                    if list(recps.keys())[row] in self.recip[self.crecp[0]]:
                        self.crecp=(self.crecp[0],list(recps.keys())[row])
            elif (x-36)**2+(y-self.h+252)**2<=576: #Saving
                i=input("save/load/new? ")
                if i=="save":
                    s=f"<CODE>v1〄{self.pos[0]:-.2f}。{self.pos[1]:-.2f}。{self.mode}。{self.p}。{self.chs}。{self.z}。{self.n}。{Terrainer.pages[self.pg][3]}〃{"。".join([Terrainer.pages[i][3] for i in self.unlocked])}〃"
                    rlist=[",".join([Terrainer.craftRecp[i][j][4] for j in self.recip[i]]) for i in self.recip.keys()]
                    s+="。".join([i for i in rlist if i])+"〃"
                    s+="。".join([f"{i[0]:-.2f}、{i[1]}" for i in self.inv])+"〃"
                    s+=f"{self.mqty}。{self.mthing}〄"
                    s+="〃".join([f"{c[0]}。{c[1]}" for c in self.ch])+"〄"
                    world="〃".join([f"{convert64(i[0])}。{convert64(i[1])}。{Terrainer.names.index(j[1])}。{"+" if j[0] == 1.0 else "-" if j[0] == -1.0 else convert64(int(j[0]*1000))}" for i,j in self.grid.items()])
                    s+=world+"〄</CODE>"
                    path=input("Where do you want to cram the universe? ")
                    f = open(path+".txt",mode="a")
                    f.write(s)
                    print(f"We managed to store the universe at {path}")
                if i=="load":
                    path=input("Where is your compacted universe? ")
                    try:
                        f = open(path+".txt","r")
                    except FileNotFoundError:
                        print("Sorry, that file doesn't exist")
                    else:
                        s = f.read()
                        i0 = s.find("<CODE>")+6
                        if i0!=-1:
                            i1 = s.find("</CODE>",i0)
                            if i1!=-1:
                                s=s[i0:i1]
                                l0=s.split("〄")
                                if l0[0]=="v1":
                                    basic0=l0[1].split("〃")
                                    consts=basic0[0].split("。")
                                    self.pos=(float(consts[0]),float(consts[1]))
                                    self.mode=int(consts[2])
                                    self.p=int(consts[3])
                                    self.chs=int(consts[4])
                                    self.z=float(consts[5])
                                    self.n=ast.literal_eval(consts[6])
                                    self.pg=Terrainer.pitn[consts[7]]
                                    pages=basic0[1].split("。")
                                    self.unlocked=[Terrainer.pitn[i] for i in pages]
                                    recs=basic0[2].split("。")
                                    for i in Terrainer.craftRecp.keys():
                                        self.recip[i]=[]
                                    for i in recs:
                                        if i!="":
                                            a,b = Terrainer.ritn[i]
                                            self.recip[a].append(b)
                                    invlist=basic0[3].split("。")
                                    self.inv=[]
                                    for i in invlist:
                                        a=i.split("、")
                                        self.inv.append([float(a[0]),a[1]])
                                    istore=basic0[4].split("。")
                                    self.mqty=float(istore[0])
                                    self.mthing=istore[1]
                                    chunks=l0[2].split("〃")
                                    self.ch=[]
                                    for i in chunks:
                                        a=i.split("。")
                                        self.ch.append(int(i[0]),int(i[1]))
                                    self.sch=self.ch.copy()
                                    world=l0[3].split("〃")
                                    self.grid=dict()
                                    self.lines=dict()
                                    self.clines=dict()
                                    for i in world:
                                        a=i.split("。")
                                        self.grid[int(devert64(a[0])),int(devert64(a[1]))]=(1.0 if a[3]=="+" else -1.0 if a[3]=="-" else devert64(a[3])/1000,Terrainer.names[a[2]])
                                    self.on_resize(self.w,self.h)
                            else:
                                print("Did you use the compacting machine correctly?")
                        else:
                            print("Did you use the compacting machine correctly?")
                if i=="new":
                    print("So you wish to create a new world to suit your needs...")
                    self.pos=(0,0)
                    self.ch=[]
                    self.grid=dict()
                    self.lines=dict()
                    self.clines=dict()
                    try:
                        self.p = min(64,max(4,int(input("Frame size (default 16): "))))
                    except ValueError:
                        print("That wasn't an integer")
                    try:
                        self.chs = min(64,max(4,int(input("Chunk size (default 16): "))))
                    except ValueError:
                        print("That wasn't an integer")
                    try:
                        self.z = min(64,max(4,int(input("Noise width (default 32): "))))
                    except ValueError:
                        print("That wasn't an integer")
                    l = input("Seeds (4) (default 4,5,6,7): ").split(",")
                    try:
                        self.n=[(int(l[0]),int(l[1])),(int(l[2]),int(l[3]))]
                    except ValueError:
                        print("One of those wasn't an integer")
                    self.on_resize(self.w,self.h)
            elif (x-36)**2+(y-self.h+180)**2<=576:
                self.scing=1
        elif self.scing==1:
            self.scing=0
            if self.bw<=x<=self.w-self.bw and self.bh<=y<=self.h-self.bh:
                if self.grid[(int(np.round((x-self.w/2)/self.sc)),int(np.round((y-self.h/2)/self.sc)))][0]==1:
                    if self.grid[(int(np.round((x-self.w/2)/self.sc)),int(np.round((y-self.h/2)/self.sc)))][1] in Terrainer.craftUI.keys():
                        self.ctable=self.grid[(int(np.round((x-self.w/2)/self.sc)),int(np.round((y-self.h/2)/self.sc)))][1]
                        self.st=4
                        ui=Terrainer.craftUI[self.ctable]
                        self.cstate=([[0,"grass"] for _ in ui[1]],[[0,"grass"] for _ in ui[2]])
                        self.cslot=0
            elif (x-36)**2+(y-self.h+108)**2<=576:
                self.scing=0
                self.st=5
                self.crecp=(None,None)
    def on_mouse_drag(self,x,y,dx,dy,buttons,modifiers):
        #Re-setting click position
        ux = (x-self.w/2)/self.sc+self.pos[0]
        uy = (y-self.h/2)/self.sc+self.pos[1]
        self.cmouse = [round(ux),round(uy),(1 if modifiers == 0 else 2)]
        if self.adjfuzz:
            self.fuzz=min(1,max(0,1-(y-192)/(self.h-384)))
            self.updres=True
    def on_mouse_release(self,x,y,button,modifiers):
        #Unsetting mouse data
        self.cmouse = [0,0,0]
        self.adjfuzz=False
        self.cclick=0
    def on_key_press(self,button,modifiers):
        #Checking movement
        if self.st!=2:
            if button == arcade.key.LEFT:
                self.kpress.append("LEFT")
            if button == arcade.key.RIGHT:
                self.kpress.append("RIGHT")
            if button == arcade.key.DOWN:
                self.kpress.append("DOWN")
            if button == arcade.key.UP:
                self.kpress.append("UP")
            #Inventory stuff
            if button == arcade.key.Z:
                self.delt = 1
            if button == arcade.key.X:
                self.inv[self.invslot][0] = 0
            #2 - creative, 1 - view inventory, 0 - play
            if button == arcade.key.C and self.mode>0:
                self.st = 2
            if button == arcade.key.V:
                self.st = 1
            if button == arcade.key.ESCAPE:
                self.st = 0
            #Slots
            if button == arcade.key.KEY_1:
                self.invslot = 0
            if button == arcade.key.KEY_2:
                self.invslot = 1
            if button == arcade.key.KEY_3:
                self.invslot = 2
            if button == arcade.key.KEY_4:
                self.invslot = 3
            if button == arcade.key.KEY_5:
                self.invslot = 4
            if button == arcade.key.KEY_6:
                self.invslot = 5
            if button == arcade.key.KEY_7:
                self.invslot = 6
            if button == arcade.key.KEY_8:
                self.invslot = 7
            if button == arcade.key.KEY_9:
                self.invslot = 8
            if button == arcade.key.KEY_0:
                self.invslot = 9
            if button == arcade.key.MINUS:
                self.invslot = 10
            if button == arcade.key.EQUAL:
                self.invslot = 11
            #Moving
            if button == arcade.key.ENTER:
                if "Inv" in self.unlocked:
                    self.unlocked.add("Item")
                    self.unlocked.add("Edit")
                if modifiers == arcade.key.MOD_SHIFT:
                    if self.mqty > 0 and self.mthing == self.inv[self.invslot][1]:
                        if self.mqty/2 + self.inv[self.invslot][0] >= 64:
                            self.mqty = self.mqty + self.inv[self.invslot][0] - 64
                            self.inv[self.invslot][0] = 64
                        else:
                            self.inv[self.invslot][0] += self.mqty/2
                            self.mqty /= 2
                    elif self.mqty == 0:
                        self.mqty = self.inv[self.invslot][0] / 2
                        self.mthing = self.inv[self.invslot][1]
                        self.inv[self.invslot][0] /= 2
                else:
                    if self.mqty > 0 and (self.mthing == self.inv[self.invslot][1] or self.inv[self.invslot][0] == 0):
                        if self.mqty + self.inv[self.invslot][0] >= 64:
                            self.mqty = self.mqty + self.inv[self.invslot][0] - 64
                            self.inv[self.invslot][0] = 64
                            self.inv[self.invslot][1] = self.mthing
                        else:
                            self.inv[self.invslot][0] += self.mqty
                            self.inv[self.invslot][1] = self.mthing
                            self.mqty = 0
                    elif self.mqty == 0:
                        self.mqty = self.inv[self.invslot][0]
                        self.mthing = self.inv[self.invslot][1]
                        self.inv[self.invslot][0] = 0
            if button == arcade.key.Q and self.st==4:
                self.cslot = (self.cslot-1)%(len(Terrainer.craftUI[self.ctable][1])+len(Terrainer.craftUI[self.ctable][2]))
            if button == arcade.key.E and self.st==4:
                self.cslot = (self.cslot+1)%(len(Terrainer.craftUI[self.ctable][1])+len(Terrainer.craftUI[self.ctable][2]))
            if button == arcade.key.TAB and self.st==4:
                if self.cslot<len(Terrainer.craftUI[self.ctable][1]):
                    i = self.inv[self.invslot]
                    self.inv[self.invslot] = self.cstate[0][self.cslot]
                    self.cstate[0][self.cslot] = i
                else:
                    i = self.inv[self.invslot]
                    self.inv[self.invslot] = self.cstate[1][self.cslot-len(Terrainer.craftUI[self.ctable][1])]
                    self.cstate[1][self.cslot-len(Terrainer.craftUI[self.ctable][1])] = i
        else:
            #String navigation
            if button == arcade.key.LEFT:
                self.strpos = max(0,self.strpos-1)
            if button == arcade.key.RIGHT:
                self.strpos = min(len(self.searchstr),self.strpos+1)
            #Page navigation
            if button == arcade.key.UP:
                self.searchpg = max(0,self.searchpg-1)
            if button == arcade.key.DOWN:
                self.searchpg = min(np.ceil(len(self.searchres)/6)-1,self.searchpg+1)
            #Input
            if button == arcade.key.BACKSPACE and self.strpos > 0:
                self.searchstr = self.searchstr[:self.strpos-1]+self.searchstr[self.strpos:]
                self.strpos-=1
                self.searchpg=0
                self.updres=True
            if button == arcade.key.A:
                self.searchstr=self.searchstr[:self.strpos]+"A"+self.searchstr[self.strpos:]
                self.strpos+=1
                self.searchpg=0
                self.updres=True
            if button == arcade.key.B:
                self.searchstr=self.searchstr[:self.strpos]+"B"+self.searchstr[self.strpos:]
                self.strpos+=1
                self.searchpg=0
                self.updres=True
            if button == arcade.key.C:
                self.searchstr=self.searchstr[:self.strpos]+"C"+self.searchstr[self.strpos:]
                self.strpos+=1
                self.searchpg=0
                self.updres=True
            if button == arcade.key.D:
                self.searchstr=self.searchstr[:self.strpos]+"D"+self.searchstr[self.strpos:]
                self.strpos+=1
                self.searchpg=0
                self.updres=True
            if button == arcade.key.E:
                self.searchstr=self.searchstr[:self.strpos]+"E"+self.searchstr[self.strpos:]
                self.strpos+=1
                self.searchpg=0
                self.updres=True
            if button == arcade.key.F:
                self.searchstr=self.searchstr[:self.strpos]+"F"+self.searchstr[self.strpos:]
                self.strpos+=1
                self.searchpg=0
                self.updres=True
            if button == arcade.key.G:
                self.searchstr=self.searchstr[:self.strpos]+"G"+self.searchstr[self.strpos:]
                self.strpos+=1
                self.searchpg=0
                self.updres=True
            if button == arcade.key.H:
                self.searchstr=self.searchstr[:self.strpos]+"H"+self.searchstr[self.strpos:]
                self.strpos+=1
                self.searchpg=0
                self.updres=True
            if button == arcade.key.I:
                self.searchstr=self.searchstr[:self.strpos]+"I"+self.searchstr[self.strpos:]
                self.strpos+=1
                self.searchpg=0
                self.updres=True
            if button == arcade.key.J:
                self.searchstr=self.searchstr[:self.strpos]+"J"+self.searchstr[self.strpos:]
                self.strpos+=1
                self.searchpg=0
                self.updres=True
            if button == arcade.key.K:
                self.searchstr=self.searchstr[:self.strpos]+"K"+self.searchstr[self.strpos:]
                self.strpos+=1
                self.searchpg=0
                self.updres=True
            if button == arcade.key.L:
                self.searchstr=self.searchstr[:self.strpos]+"L"+self.searchstr[self.strpos:]
                self.strpos+=1
                self.searchpg=0
                self.updres=True
            if button == arcade.key.M:
                self.searchstr=self.searchstr[:self.strpos]+"M"+self.searchstr[self.strpos:]
                self.strpos+=1
                self.searchpg=0
                self.updres=True
            if button == arcade.key.N:
                self.searchstr=self.searchstr[:self.strpos]+"N"+self.searchstr[self.strpos:]
                self.strpos+=1
                self.searchpg=0
                self.updres=True
            if button == arcade.key.O:
                self.searchstr=self.searchstr[:self.strpos]+"O"+self.searchstr[self.strpos:]
                self.strpos+=1
                self.searchpg=0
                self.updres=True
            if button == arcade.key.P:
                self.searchstr=self.searchstr[:self.strpos]+"P"+self.searchstr[self.strpos:]
                self.strpos+=1
                self.searchpg=0
                self.updres=True
            if button == arcade.key.Q:
                self.searchstr=self.searchstr[:self.strpos]+"Q"+self.searchstr[self.strpos:]
                self.strpos+=1
                self.searchpg=0
                self.updres=True
            if button == arcade.key.R:
                self.searchstr=self.searchstr[:self.strpos]+"R"+self.searchstr[self.strpos:]
                self.strpos+=1
                self.searchpg=0
                self.updres=True
            if button == arcade.key.S:
                self.searchstr=self.searchstr[:self.strpos]+"S"+self.searchstr[self.strpos:]
                self.strpos+=1
                self.searchpg=0
                self.updres=True
            if button == arcade.key.T:
                self.searchstr=self.searchstr[:self.strpos]+"T"+self.searchstr[self.strpos:]
                self.strpos+=1
                self.searchpg=0
                self.updres=True
            if button == arcade.key.U:
                self.searchstr=self.searchstr[:self.strpos]+"U"+self.searchstr[self.strpos:]
                self.strpos+=1
                self.searchpg=0
                self.updres=True
            if button == arcade.key.V:
                self.searchstr=self.searchstr[:self.strpos]+"V"+self.searchstr[self.strpos:]
                self.strpos+=1
                self.searchpg=0
                self.updres=True
            if button == arcade.key.W:
                self.searchstr=self.searchstr[:self.strpos]+"W"+self.searchstr[self.strpos:]
                self.strpos+=1
                self.searchpg=0
                self.updres=True
            if button == arcade.key.X:
                self.searchstr=self.searchstr[:self.strpos]+"X"+self.searchstr[self.strpos:]
                self.strpos+=1
                self.searchpg=0
                self.updres=True
            if button == arcade.key.Y:
                self.searchstr=self.searchstr[:self.strpos]+"Y"+self.searchstr[self.strpos:]
                self.strpos+=1
                self.searchpg=0
                self.updres=True
            if button == arcade.key.Z:
                self.searchstr=self.searchstr[:self.strpos]+"Z"+self.searchstr[self.strpos:]
                self.strpos+=1
                self.searchpg=0
                self.updres=True
            if button == arcade.key.SPACE:
                self.searchstr=self.searchstr[:self.strpos]+" "+self.searchstr[self.strpos:]
                self.strpos+=1
                self.searchpg=0
                self.updres=True
            
    def on_key_release(self,button,modifiers):
        #Un-moving
        try:
            if button == arcade.key.LEFT:
                self.kpress.remove("LEFT")
            if button == arcade.key.RIGHT:
                self.kpress.remove("RIGHT")
            if button == arcade.key.DOWN:
                self.kpress.remove("DOWN")
            if button == arcade.key.UP:
                self.kpress.remove("UP")
            if button == arcade.key.Z:
                self.delt = 0
        except ValueError:
            0
def main():
    #Setting up game
    try:
        n = int(input("How many pixels? "))
    except ValueError:
        n=64
    n = int(max(1,min(n,256)))
    window = Terrainer(PIX=n,WSIZE=8,SPEED=4)
    window.setup()
    arcade.run()

main()
