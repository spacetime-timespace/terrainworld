#@title Marching squares on Simplex Noise
import arcade
import matplotlib.pyplot as plt
from noiselib import rng, Simplex, np
msdict = {
    (0,0,0,0):[],
    (1,0,0,0):[(0,2)],
    (0,1,0,0):[(1,2)],
    (1,1,0,0):[(0,1)],
    (0,0,1,0):[(0,3)],
    (1,0,1,0):[(2,3)],
    (0,1,1,0):[(0,4),(1,4),(2,4),(3,4)],
    (1,1,1,0):[(1,3)],
    (0,0,0,1):[(1,3)],
    (1,0,0,1):[(0,4),(1,4),(2,4),(3,4)],
    (0,1,0,1):[(2,3)],
    (1,1,0,1):[(0,3)],
    (0,0,1,1):[(0,1)],
    (1,0,1,1):[(1,2)],
    (0,1,1,1):[(0,2)],
    (1,1,1,1):[],
}
def ms(thres,vces,offset):
  k = (0 if vces[0] < thres else 1, 0 if vces[1] < thres else 1, 0 if vces[2] < thres else 1, 0 if vces[3] < thres else 1)
  edges = msdict[k]
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
  return [[[i[0][0],i[1][0]],[i[0][1],i[1][1]]] for i in a]

THRESHOLD = 0
IMG_SIZE = 1024
sc = 16

r5 = rng(seed=4)
s5 = Simplex(2,r5)

'''grid = [[s5([i*sc/IMG_SIZE,j*sc/IMG_SIZE]) for j in range(IMG_SIZE)] for i in range(IMG_SIZE)]
for i in range(IMG_SIZE-1):
  for j in range(IMG_SIZE-1):
    vces = (grid[i][j],grid[i+1][j],grid[i][j+1],grid[i+1][j+1])
    out = ms(THRESHOLD,vces,[i,j])
    for k in out:
      plt.plot(k[0],k[1],c="blue")
plt.show()'''

class Terrainer(arcade.Window):
    def __init__(self,WIDTH=240, HEIGHT=180, FPS=60, PIX = 256, SIZE = 8, SPEED=1):
        super().__init__(WIDTH, HEIGHT, "RGB Animation", update_rate=1/FPS,resizable=True)
        self.h = HEIGHT
        self.w = WIDTH
        self.p = PIX
        self.s = SIZE
        self.sc = None
        self.grid = None
        self.lines = None
        self.bh = None
        self.bw = None
        self.cmouse=[0,0,0]
        self.sp = SPEED
    def on_resize(self,width,height):
        self.w = width
        self.h = height
        self.sc = min(self.w,self.h)/(self.p-1)
        self.bw = 0 if self.w < self.h else (self.w-self.h)/2
        self.bh = 0 if self.h < self.w else (self.h-self.w)/2
    def setup(self):
        self.grid = [[s5([i*self.s/self.p,j*self.s/self.p]) for j in range(self.p)] for i in range(self.p)]
        self.lines = [[ms(0,(self.grid[i][j],self.grid[i+1][j],self.grid[i][j+1],self.grid[i+1][j+1]),[i,j]) for j in range(self.p-1)] for i in range(self.p-1)]
        self.sc = min(self.w,self.h)/(self.p-1)
        self.bw = 0 if self.w < self.h else (self.w-self.h)/2
        self.bh = 0 if self.h < self.w else (self.h-self.w)/2
        print(self.lines,self.sc,self.bw,self.bh)
    def on_draw(self):
        self.clear()
        for i in self.lines:
            for j in i:
                for k in j:
                    arcade.draw_line(k[0][0]*self.sc+self.bw,k[1][0]*self.sc+self.bh,
                                     k[0][1]*self.sc+self.bw,k[1][1]*self.sc+self.bh,
                                     (255,255,255,255))
    def on_update(self,delta):
        if self.cmouse[2]!=0:
            try:
                k = self.cmouse[0]
                l = self.cmouse[1]
                if self.cmouse[2] == 1:
                    self.grid[k][l] -= delta*self.sp
                if self.cmouse[2] == 2:
                    self.grid[k][l] += delta*self.sp
                for (i,j) in [(k-1,l-1),(k,l-1),(k-1,l),(k,l)]:
                    try:
                        self.lines[i][j] = ms(0,(self.grid[i][j],self.grid[i+1][j],self.grid[i][j+1],self.grid[i+1][j+1]),[i,j])
                    except IndexError:
                        0
            except IndexError:
                0
    def on_mouse_press(self,x,y,buttons,modifiers):
        ux = (x-self.bw)/self.sc
        uy = (y-self.bh)/self.sc
        self.cmouse = [round(ux),round(uy),(1 if modifiers == 0 else 2)]
    def on_mouse_drag(self,x,y,dx,dy,buttons,modifiers):
        ux = (x-self.bw)/self.sc
        uy = (y-self.bh)/self.sc
        self.cmouse = [round(ux),round(uy),(1 if modifiers == 0 else 2)]
    def on_mouse_release(self,x,y,button,modifiers):
        self.cmouse = [0,0,0]

def main():
    window = Terrainer(PIX=64)
    window.setup()
    arcade.run()

main()
