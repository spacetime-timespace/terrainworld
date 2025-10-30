#@title Marching squares on Simplex Noise
import arcade
import matplotlib.pyplot as plt
from noiselib import rng, Simplex, np
msdict = {
    (0,0,0,0):([],0),
    (1,0,0,0):([(0,2)],0),
    (0,1,0,0):([(1,2)],1),
    (1,1,0,0):([(0,1)],0),
    (0,0,1,0):([(0,3)],2),
    (1,0,1,0):([(2,3)],0),
    (0,1,1,0):([(0,4),(1,4),(2,4),(3,4)],1),
    (1,1,1,0):([(1,3)],0),
    (0,0,0,1):([(1,3)],3),
    (1,0,0,1):([(0,4),(1,4),(2,4),(3,4)],0),
    (0,1,0,1):([(2,3)],1),
    (1,1,0,1):([(0,3)],0),
    (0,0,1,1):([(0,1)],2),
    (1,0,1,1):([(1,2)],0),
    (0,1,1,1):([(0,2)],1),
    (1,1,1,1):([],0),
}
def ms(thres,v,offset):
  vces = [i[0] for i in v]
  k = (0 if vces[0] < thres else 1, 0 if vces[1] < thres else 1, 0 if vces[2] < thres else 1, 0 if vces[3] < thres else 1)
  edges = msdict[k][0]
  c1 = (thres-vces[0])/(vces[2]-vces[0])
  c2 = (thres-vces[1])/(vces[3]-vces[1])
  c3 = (thres-vces[0])/(vces[1]-vces[0])
  c4 = (thres-vces[2])/(vces[3]-vces[2])
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

r5 = rng(seed=4)
s5 = Simplex(2,r5,"2dnoise")

'''grid = [[s5([i*sc/IMG_SIZE,j*sc/IMG_SIZE]) for j in range(IMG_SIZE)] for i in range(IMG_SIZE)]
for i in range(IMG_SIZE-1):
  for j in range(IMG_SIZE-1):
    vces = (grid[i][j],grid[i+1][j],grid[i][j+1],grid[i+1][j+1])
    out = ms(THRESHOLD,vces,[i,j])
    for k in out:
      plt.plot(k[0],k[1],c="blue")
plt.show()'''

def load_grid(x,y,w,noise):
    return noise((x/w,y/w))

class Terrainer(arcade.Window):
    colors = [(255,255,255,255)]
    def __init__(self,WIDTH=240, HEIGHT=180, FPS=60, PIX = 256, WSIZE = 32, SPEED=1,seed=s5,MSPEED=16,name="terrainer"):
        super().__init__(WIDTH, HEIGHT, "RGB Animation", update_rate=1/FPS,resizable=True)
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
        self.pos = [0,0]
        self.n = seed
        self.vel = [0,0]
        self.m = MSPEED
        self.lb = name
    def on_resize(self,width,height):
        self.w = width
        self.h = height
        self.sc = min(self.w,self.h)/self.p
        self.bw = 0 if self.w < self.h else (self.w-self.h)/2
        self.bh = 0 if self.h < self.w else (self.h-self.w)/2
    def setup(self):
        self.grid = dict()
        self.lines = dict()
        self.sc = min(self.w,self.h)/self.p
        self.bw = 0 if self.w < self.h else (self.w-self.h)/2
        self.bh = 0 if self.h < self.w else (self.h-self.w)/2
    def on_draw(self):
        self.clear()
        for i in range(int(self.pos[0]),int(self.pos[0])+self.p+2):
            for j in range(int(self.pos[1]),int(self.pos[1])+self.p+2):
                try:
                    for k in self.lines[(i,j)][0]:
                        arcade.draw_line((k[0][0]-self.pos[0])*self.sc+self.bw,(k[1][0]-self.pos[1])*self.sc+self.bh,
                                        (k[0][1]-self.pos[0])*self.sc+self.bw,(k[1][1]-self.pos[1])*self.sc+self.bh,
                                        (255,255,255,255))
                except KeyError:
                    0
        for i in range(1):
            z = arcade.Sprite()
            z.texture = arcade.load_texture("itembox.png")
            z.scale = 2
            z.center_x = self.w-16
            z.center_y = self.h/2-16*0+32*i
            arcade.draw_sprite(z)
            arcade.draw_circle_filled(self.w-16,self.h/2-16*0+32*i,8,(255,255,255,255),0,16)
    def on_update(self,delta):
        for i in range(int(self.pos[0]//self.p)-1,int(self.pos[0]//self.p)+2):
            for j in range(int(self.pos[1]//self.p-1),int(self.pos[1]//self.p)+2):
                if (i,j) not in self.ch:
                    print(str(self.lb)+" LOADING CHUNK: "+str((i,j)))
                    self.ch.append((i,j))
                    for k in range(self.p+1):
                        for l in range(self.p+1):
                            self.grid[(i*self.p+k,j*self.p+l)] = [load_grid(i*self.p+k,j*self.p+l,self.z,self.n),0]
                    for k in range(self.p):
                        for l in range(self.p):
                            try:
                                self.lines[(i*self.p+k,j*self.p+l)] = ms(0,(self.grid[(i*self.p+k,j*self.p+l)],self.grid[(i*self.p+k+1,j*self.p+l)],self.grid[(i*self.p+k,j*self.p+l+1)],self.grid[(i*self.p+k+1,j*self.p+l+1)]),[i*self.p+k,j*self.p+l])
                            except KeyError:
                                0
        self.pos[0]+=delta*self.m*self.vel[0]
        self.pos[1]+=delta*self.m*self.vel[1]
        self.cmouse[0]+=delta*self.m*self.vel[0]
        self.cmouse[1]+=delta*self.m*self.vel[1]
        if self.cmouse[2]!=0:
            try:
                k = self.cmouse[0]
                l = self.cmouse[1]
                if self.cmouse[2] == 1 and self.grid[(k,l)][0]-delta*self.sp>=-1:
                    self.grid[(k,l)][0] -= delta*self.sp
                if self.cmouse[2] == 2 and self.grid[(k,l)][0]+delta*self.sp<=1:
                    self.grid[(k,l)][0] += delta*self.sp
                for (i,j) in [(k-1,l-1),(k,l-1),(k-1,l),(k,l)]:
                    try:
                        self.lines[(i,j)] = ms(0,(self.grid[(i,j)],self.grid[(i+1,j)],self.grid[(i,j+1)],self.grid[(i+1,j+1)]),[i,j])
                    except KeyError:
                        0
            except KeyError:
                0
    def on_mouse_press(self,x,y,buttons,modifiers):
        ux = (x-self.bw)/self.sc+self.pos[0]
        uy = (y-self.bh)/self.sc+self.pos[1]
        self.cmouse = [round(ux),round(uy),(1 if modifiers == 0 else 2)]
    def on_mouse_drag(self,x,y,dx,dy,buttons,modifiers):
        ux = (x-self.bw)/self.sc+self.pos[0]
        uy = (y-self.bh)/self.sc+self.pos[1]
        self.cmouse = [round(ux),round(uy),(1 if modifiers == 0 else 2)]
    def on_mouse_release(self,x,y,button,modifiers):
        self.cmouse = [0,0,0]
    def on_key_press(self,button,modifiers):
        if button == arcade.key.LEFT:
            self.vel[0]-=1
        if button == arcade.key.RIGHT:
            self.vel[0]+=1
        if button == arcade.key.DOWN:
            self.vel[1]-=1
        if button == arcade.key.UP:
            self.vel[1]+=1
    def on_key_release(self,button,modifiers):
        if button == arcade.key.LEFT:
            self.vel[0]+=1
        if button == arcade.key.RIGHT:
            self.vel[0]-=1
        if button == arcade.key.DOWN:
            self.vel[1]+=1
        if button == arcade.key.UP:
            self.vel[1]-=1
def main():
    window = Terrainer(PIX=64,WSIZE=8)
    window.setup()
    arcade.run()

main()
