#@title Simplex Noise!

import numpy as np
import matplotlib.pyplot as plt

def hash0(n):
    n=int(n)
    h = (n & 0xFFFFFFFFFFFFFFFF) + 0x9E3779B97F4A7C15
    h = (h ^ (h >> 30)) * 0xBF58476D1CE4E5B9
    h = (h ^ (h >> 27)) * 0x94D049BB133111EB
    h = h ^ (h >> 31)
    return h & 0xFFFFFFFFFFFFFFFF

def rng(seed=(0,1)):
    def hash(*args):
        combined = 0
        for i,val in enumerate(args):
            combined^=hash0(int(val)+i*(1618033989+seed[0]))
        v1 = hash0(combined) / 0xFFFFFFFFFFFFFFFF
        combined = 0
        for i,val in enumerate(args):
            combined^=hash0(int(val)+i*(1618033989+seed[1]))
        v2 = hash0(combined) / 0xFFFFFFFFFFFFFFFF
        mag = np.sqrt(-2.0 * np.log(max(1e-10, v1)))
        z0 = mag * np.cos(2.0 * np.pi * v2)
        return z0
    return hash

def get_gradient(gradient_grid, coords):
    """
    Gets a gradient vector from the grid at integer coordinates.
    """
    try:
      return gradient_grid[tuple(coords)]
    except KeyError:
      return tuple(coords)

def _simplex(dims, gradient_grid, inp):
    """
    Calculates simplex noise for a given input point.
    """
    # Skewing and unskewing factors for 2D
    F2 = ((dims + 1)**0.5 - 1) / dims  # Skew factor
    G2 = (1 - (dims + 1)**-0.5) / dims # Unskew factor
    
    # 1. Skew the input point to find its base simplex cell
    s = np.sum(inp) * F2
    inp_skewed = np.array(inp) + s
    base_coords_skewed = np.floor(inp_skewed)
    
    # 2. Determine the simplex traversal order
    # This depends on the fractional part of the SKEWED coordinates
    inp_skewed_frac = inp_skewed - base_coords_skewed
    offsets = [[0 for _ in range(dims)] for _ in range(dims+1)]
    a = sorted(range(dims),key = lambda x: inp_skewed_frac[x], reverse = True)
    for i in range(dims):
      for j in range(i+1,dims+1):
        offsets[j][a[i]] = 1
    total_noise = 0.0
    
    # 3. Calculate the contribution from each of the three simplex vertices
    for offset in offsets:
        # Get the integer coordinates of the vertex in skewed space
        vertex_skewed = base_coords_skewed + offset
        
        # Unskew the vertex to get its position in real coordinate space
        t = np.sum(vertex_skewed) * G2
        vertex_unskewed = vertex_skewed - t
        
        # Calculate the distance vector from the input point to this vertex
        dist_vec = np.array(inp) - vertex_unskewed
        
        # Calculate distance squared
        d2 = np.dot(dist_vec, dist_vec)
        
        # If the point is within the contribution radius (0.5 for 2D), add its contribution
        if d2 < 0.5:
            # Get the pre-defined gradient vector for this vertex
            a = get_gradient(gradient_grid, vertex_skewed)
            if type(a) == tuple:
              return a
              break
            else:
              gradient = np.array(get_gradient(gradient_grid, vertex_skewed))
            
            # Calculate the falloff term: (0.5 - d^2)^4
            falloff = (0.5 - d2)**4
            
            # Add the contribution: falloff * dot(gradient, distance_vector)
            total_noise += falloff * np.dot(gradient, dist_vec)
            
    # The final value is scaled to be roughly in the [-1, 1] range.
    # 100.0 is a common scaling factor for 2D simplex noise.
    return total_noise * 100.00

def generate_unit_vector(dims,r,inp):
    """Generates a random unit vector."""
    l=[]
    for i in range(dims):
       l.append(r(i,*inp))
    vec=np.array(l)
    norm = np.linalg.norm(vec)
    return vec / norm if norm != 0 else np.zeros(dims)

class Simplex:
  """This class makes a custom simplex noise from an rng (random.default_rng(seed=0))
  if you load the same chunks in the same order, the result will be the same"""
  def __init__(self,dims,rng):
    self.dims = dims
    self.rng = rng
    self.data = dict()
  def __call__(self,inp):
    a = _simplex(self.dims,self.data,inp)
    if type(a) == tuple:
      self.data[a] = generate_unit_vector(self.dims,self.rng,a)
      print("Loading chunk: "+str(a))
      return self(inp)
    else:
      return a
  def __str__(self):
    return str(self.dims)+"d noise generator ("+str(len(self.data.keys()))+" chunks loaded)"
  def __repr__(self):
    return str(self.dims)+"d noise generator ("+str(len(self.data.keys()))+" chunks loaded)"
  
def fractal(simplex,decay,scale,iters,inp):
  return sum([simplex([j*scale**i for j in inp])*decay**i for i in range(iters)])/sum([decay**i for i in range(iters)])