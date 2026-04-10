#@title Marching squares on Simplex Noise
import arcade
import matplotlib.pyplot as plt
from noiselib import rng, Simplex, np
#Every pattern in marching squares
#Interior to the left
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
r5 = rng(seed=4)
s5 = Simplex(2,r5)
r6 = rng(seed=5)
s6 = Simplex(2,r6)

'''grid = [[s5([i*sc/IMG_SIZE,j*sc/IMG_SIZE]) for j in range(IMG_SIZE)] for i in range(IMG_SIZE)]
for i in range(IMG_SIZE-1):
  for j in range(IMG_SIZE-1):
    vces = (grid[i][j],grid[i+1][j],grid[i][j+1],grid[i+1][j+1])
    out = ms(THRESHOLD,vces,[i,j])
    for k in out:
      plt.plot(k[0],k[1],c="blue")
plt.show()'''

#Loading a terrain value, will get more complicated
def load_grid(x,y,w,noise):
    return [min(1,max(-1,noise[0]((x/w,y/w))*5)),0 if noise[1]((x/w/3,y/w/3)) <= -0.25 else (1 if noise[1]((x/w/3,y/w/3)) <= 0.25 else 2)]

#The game!
class Terrainer(arcade.Window):
    colors = [(192,255,128,255),(128,80,0,255),(128,128,128,255)]
    names = ["grass","dirt","stone"]
    def __init__(self,WIDTH=240, HEIGHT=180, FPS=60, PIX = 256, WSIZE = 32, SPEED=1,seed=[s5,s6],MSPEED=16,name="terrainer"):
        super().__init__(WIDTH, HEIGHT, "Terrainer", update_rate=1/FPS,resizable=True)
        #Initializing variables...
        self.h = HEIGHT
        self.w = WIDTH
        self.p = PIX
        self.z = WSIZE
        self.sc = None
        self.grid = None
        self.lines = None
        self.bh = None
        self.bw = None
        self.cmouse=[0,0,0]
        self.sp = SPEED
        self.ch = []
        self.pos = np.array([0.0,0.0])
        self.nx=0
        self.ny=0
        self.n = seed
        self.vel = np.array([0.0,0.0])
        self.m = MSPEED
        self.lb = name
        self.inv = [[0,0],[0,0],[0,0],[0,0],[0,0],[0,0],[0,0],[0,0],[0,0],[0,0],[0,0],[0,0]]
        self.invslot = 0
        self.creative = 0
        self.cthing = 0
        self.mthing = 0
        self.mqty = 0
        self.delt = 0
        self.st = 0
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
        self.sc = min(self.w,self.h)/self.p
        self.bw = 0 if self.w < self.h else (self.w-self.h)/2
        self.bh = 0 if self.h < self.w else (self.h-self.w)/2
    def on_draw(self):
        self.clear()
        #Draws all segments
        for i in range(int(self.pos[0]-self.p/2-1),int(self.pos[0]+self.p/2+1)):
            for j in range(int(self.pos[1]-self.p/2-1),int(self.pos[1]+self.p/2+1)):
                try:
                    m = self.lines[(i,j)][1]
                    for k in self.lines[(i,j)][0]:
                        arcade.draw_line((k[0][0]-self.pos[0]+self.p/2)*self.sc+self.bw,(k[1][0]-self.pos[1]+self.p/2)*self.sc+self.bh,
                                        (k[0][1]-self.pos[0]+self.p/2)*self.sc+self.bw,(k[1][1]-self.pos[1]+self.p/2)*self.sc+self.bh,
                                        Terrainer.colors[m])
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
            z.texture = arcade.load_texture("itembox.png")
            z.scale = 2
            z.center_x = self.w-16
            z.center_y = self.h/2+16*len(self.inv)-16-32*i
            arcade.draw_sprite(z)
            if self.inv[i][0] == 0:
                continue
            z = arcade.Sprite()
            z.texture = arcade.load_texture("tiles/"+Terrainer.names[self.inv[i][1]]+".png")
            z.scale = 1
            z.center_x = self.w-16
            z.center_y = self.h/2+16*len(self.inv)-16-32*i
            arcade.draw_sprite(z)
            c = len(str(int(self.inv[i][0])))
            for j in range(c):
                x = str(int(self.inv[i][0]))[j]
                z.texture = arcade.load_texture("font/tile"+x+".png")
                z.scale = 0.5
                z.center_x = self.w-16-c*2+2+4*j
                z.center_y = self.h/2+16*len(self.inv)-16-32*i
                arcade.draw_sprite(z)
        z = arcade.Sprite()
        z.texture = arcade.load_texture("selector.png")
        z.scale = 2
        if self.mqty == 0:
            z.center_x = self.w-48
        else:
            z.center_x = self.w-80
        z.center_y = self.h/2+16*len(self.inv)-16-32*self.invslot
        arcade.draw_sprite(z)
        #Coordinates
        arcade.draw_rect_filled(arcade.rect.XYWH(self.w/2, 96, self.w-192, 192),(192,192,192,255))
        arcade.draw_circle_filled(96,96,96,(192,192,192,255))
        arcade.draw_circle_filled(self.w-96,96,96,(192,192,192,255))
        s=f"({self.pos[0]:+.2f},{self.pos[1]:+.2f})"
        c=len(s)
        for j in range(c):
                x = s[j]
                z.texture = arcade.load_texture("font/tile"+x+".png")
                z.scale = 4
                z.center_x = self.w/2-c*24+16+48*j
                z.center_y = 96
                arcade.draw_sprite(z)
        for j in range(len(str(int(self.inv[i][0])))):
            x = str(int(self.inv[i][0]))[j]
            z.texture = arcade.load_texture("font/tile"+x+".png")
            z.scale = 0.5
            z.center_x = self.w-16-c*2+2+4*j
            z.center_y = self.h/2+16*len(self.inv)-16-32*i
            arcade.draw_sprite(z)
        #Notice box
        if self.st != 0:
            arcade.draw_rect_filled(arcade.rect.XYWH(self.w/2, self.h/2, self.w-192, self.h-384),(128,128,128,255))
            arcade.draw_rect_filled(arcade.rect.XYWH(self.w/2, self.h/2, self.w-384, self.h-192),(128,128,128,255))
            arcade.draw_circle_filled(192,192,96,(128,128,128,255))
            arcade.draw_circle_filled(self.w-192,192,96,(128,128,128,255))
            arcade.draw_circle_filled(192,self.h-192,96,(128,128,128,255))
            arcade.draw_circle_filled(self.w-192,self.h-192,96,(128,128,128,255))
        if self.st == 1:
            for i in range(12):
                z = arcade.Sprite()
                z.texture = arcade.load_texture("itembox.png")
                z.scale = 4
                z.center_x = 192
                z.center_y = self.h/2+32*len(self.inv)-32-64*i
                arcade.draw_sprite(z)
                if self.inv[i][0] == 0:
                    continue
                z = arcade.Sprite()
                z.texture = arcade.load_texture("tiles/"+Terrainer.names[self.inv[i][1]]+".png")
                z.scale = 2
                z.center_x = 192
                z.center_y = self.h/2+32*len(self.inv)-32-64*i
                arcade.draw_sprite(z)
                t = "{:6} ".format("{:.3f}".format(self.inv[i][0]))
                t += Terrainer.names[self.inv[i][1]]
                for j in range(len(t)):
                    if t[j] != " ":
                        z = arcade.Sprite()
                        z.texture = arcade.load_texture("font/tile"+t[j]+".png")
                        z.scale = 2
                        z.center_x = 256 + j*32
                        z.center_y = self.h/2+32*len(self.inv)-32-64*i
                        arcade.draw_sprite(z)
    def on_update(self,delta):
        self.nx=int(round(self.pos[0]))
        self.ny=int(round(self.pos[1]))
        opos=self.pos
        #Loading chunks
        if self.st == 0:
            if self.delt:
                self.inv[self.invslot][0] = max(0,self.inv[self.invslot][0]-self.sp*delta)
            if self.creative:
                self.inv[0][0] = 64
                self.inv[0][1] = self.cthing
            for i in range(int(self.pos[0]//self.p-2),int(self.pos[0]//self.p)+2):
                for j in range(int(self.pos[1]//self.p-2),int(self.pos[1]//self.p)+2):
                    if (i,j) not in self.ch:
                        self.ch.append((i,j))
                        #Calculating terrain
                        for k in range(self.p+1):
                            for l in range(self.p+1):
                                self.grid[(i*self.p+k,j*self.p+l)] = load_grid(i*self.p+k,j*self.p+l,self.z,self.n)
                        #Initializing segments
                        for k in range(self.p):
                            for l in range(self.p):
                                try:
                                    self.lines[(i*self.p+k,j*self.p+l)] = ms(0,(self.grid[(i*self.p+k,j*self.p+l)],self.grid[(i*self.p+k+1,j*self.p+l)],self.grid[(i*self.p+k,j*self.p+l+1)],self.grid[(i*self.p+k+1,j*self.p+l+1)]),[i*self.p+k,j*self.p+l])
                                except KeyError:
                                    0
            #Colliding
            ploc = Point(float(self.pos[0]), float(self.pos[1]))
            pvel = Point(float(self.vel[0]), float(self.vel[1]))
            for _ in range(5):
                ploc += pvel*delta*self.m/5
                if not self.creative:
                    for _ in range(5): #multiplicity to (hopefully) fully resolve
                        iloc = Point(int(np.floor(ploc.x)),int(np.floor(ploc.y)))
                        lloc = ploc-iloc
                        #ploc is my current position, iloc is the reference point, lloc is the local position
                        collide = []
                        for i in range(-1, 2):
                            for j in range(-1, 2):
                                for l0 in self.lines[(i+iloc.x,j+iloc.y)][0]:
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
                                if self.inv[i][1]==self.grid[(k,l)][1] and 0<self.inv[i][0]<64 and not(i==0 and self.creative):
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
                        except KeyError:
                            0
                except KeyError:
                    0
        
    def on_mouse_press(self,x,y,buttons,modifiers):
        #Calculating click position
        ux = (x-self.w/2)/self.sc+self.pos[0]
        uy = (y-self.h/2)/self.sc+self.pos[1]
        self.cmouse = [round(ux),round(uy),(1 if modifiers == 0 else 2)]
    def on_mouse_drag(self,x,y,dx,dy,buttons,modifiers):
        #Re-setting click position
        ux = (x-self.w/2)/self.sc+self.pos[0]
        uy = (y-self.h/2)/self.sc+self.pos[1]
        self.cmouse = [round(ux),round(uy),(1 if modifiers == 0 else 2)]
    def on_mouse_release(self,x,y,button,modifiers):
        #Unsetting mouse data
        self.cmouse = [0,0,0]
    def on_key_press(self,button,modifiers):
        #Checking movement
        if button == arcade.key.LEFT:
            self.vel[0]-=1
        if button == arcade.key.RIGHT:
            self.vel[0]+=1
        if button == arcade.key.DOWN:
            self.vel[1]-=1
        if button == arcade.key.UP:
            self.vel[1]+=1
        #Inventory stuff
        if button == arcade.key.F:
            self.creative = 1 - self.creative
        if button == arcade.key.S:
            self.cthing = (self.cthing - 1)%len(Terrainer.colors)
        if button == arcade.key.D:
            self.cthing = (self.cthing + 1)%len(Terrainer.colors)
        if button == arcade.key.Z:
            self.delt = 1
        if button == arcade.key.X:
            self.inv[self.invslot][0] = 0
        #2 - craft, 1 - view inventory, 0 - play
        if button == arcade.key.C:
            self.st = 2
        if button == arcade.key.V:
            self.st = 1
        if button == arcade.key.B:
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
    def on_key_release(self,button,modifiers):
        #Un-moving
        if button == arcade.key.LEFT:
            self.vel[0]+=1
        if button == arcade.key.RIGHT:
            self.vel[0]-=1
        if button == arcade.key.DOWN:
            self.vel[1]+=1
        if button == arcade.key.UP:
            self.vel[1]-=1
        if button == arcade.key.Z:
            self.delt = 0
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
