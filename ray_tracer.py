"""
MIT License
Copyright (c) 2017 Cyrille Rossant
Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:
The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.
THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
"""

import numpy as np
import matplotlib.pyplot as plt

w = 400
h = 300

def normalize(x):
    x /= np.linalg.norm(x)
    return x
STEP_SIZE = 0.01

def step_ray(O, D):
    new_o = O + D * STEP_SIZE
    # import ipdb; ipdb.set_trace()

    # print(type(O))
    new_d = normalize(D - np.array([0, 0.0, 0.01])) # * np.array([0, 0.005, 0])
    return new_o, new_d

def ray_at_time(O, D, i, d):
    # print("called")
    for _ in range(i):
        O, D = step_ray(O, D)
    return O + D*d

def intersect_plane(O, D, P, N, portal=False):
    # Return the distance from O to the intersection of the ray (O, D) with the
    # plane (P, N), or +inf if there is no intersection.
    # O and P are 3D points, D and N (normal) are normalized vectors.

    if portal:
        # do some non-euclidean ray march here
        # original_d = d
        for i in range(1000):
            denom = np.dot(D, N)
            if np.abs(denom) < 1e-6:
                return np.inf
            d = np.dot(P - O, N) / denom
            if d < 0:
                return np.inf, np.inf
            if d < STEP_SIZE:
                return i, d
            O, D = step_ray(O, D)# O + D * STEP_SIZE
        return np.inf, np.inf
        # return d

    denom = np.dot(D, N)
    if np.abs(denom) < 1e-6:
        return np.inf
    d = np.dot(P - O, N) / denom
    if d < 0:
        return np.inf
    # print(d)
    return d

def intersect_sphere(O, D, S, R, portal=False):
    # Return the distance from O to the intersection of the ray (O, D) with the
    # sphere (S, R), or +inf if there is no intersection.
    # O and S are 3D points, D (direction) is a normalized vector, R is a scalar.
    if portal:
        for i in range(2000):
            a = np.dot(D, D)
            OS = O - S
            b = 2 * np.dot(D, OS)
            c = np.dot(OS, OS) - R * R
            disc = b * b - 4 * a * c
            if disc > 0:
                distSqrt = np.sqrt(disc)
                q = (-b - distSqrt) / 2.0 if b < 0 else (-b + distSqrt) / 2.0
                t0 = q / a
                t1 = c / q
                t0, t1 = min(t0, t1), max(t0, t1)
                if t1 >= 0:
                    if t0 < STEP_SIZE and t0 > 0:
                        return i, t0
                    elif t1 < STEP_SIZE:
                        return i, t1
                    # print(t1, t0)
                    # return t1 if (t0 < 0  else t0
            else:
                return np.inf, np.inf
            O, D = step_ray(O, D)# O + D * STEP_SIZE
        return np.inf, np.inf
    a = np.dot(D, D)
    OS = O - S
    b = 2 * np.dot(D, OS)
    c = np.dot(OS, OS) - R * R
    disc = b * b - 4 * a * c
    if disc > 0:
        distSqrt = np.sqrt(disc)
        q = (-b - distSqrt) / 2.0 if b < 0 else (-b + distSqrt) / 2.0
        t0 = q / a
        t1 = c / q
        t0, t1 = min(t0, t1), max(t0, t1)
        if t1 >= 0:
            # print(t1, t0)
            return t1 if t0 < 0 else t0
    return np.inf

# SIGNED DISTANCE FUNCTION PRIMITIVES
def sdBox(p, b):
    d = np.absolute(p) - b
    return min(np.max(d), 0.0) + np.linalg.norm(np.fmax(d, 0.0))

def sdCylH(p, h):
    d = np.absolute(np.array([np.linalg.norm(p[1:]), p[0]])) - h
    return min(np.max(d), 0.0) + np.linalg.norm(np.fmax(d, 0.0))

def sdCylX(p, h):
    d = np.absolute(np.array([np.linalg.norm(p[:2]), p[2]])) - h
    return min(np.max(d), 0.0) + np.linalg.norm(np.fmax(d, 0.0))

def sdRoundBox(p, b, r):
    d = np.absolute(p) - b
    return np.linalg.norm(np.fmax(d, 0.0)) - r + min(np.max(d), 0.0)

# SIGNED DISTANCE FUNCTION OPERATORS
def opU(d1, d2):
    return min(d1, d2)

def opS(d1, d2):
    return max(-1 * d1, d2)

# CAR SIGNED DISTANCE FUNCTION
def carMap(pos):
    res = 0;

    res = opU(res, sdRoundBox(pos - np.array([0, 0.3, 0]), np.array([0.7, 0.07, 0.3]), 0.2)); # body
    res = opU(res, sdRoundBox(pos - np.array([0.2, 0.5, 0.0]), np.array([0.5, 0.3, 0.3]), 0.1));
    res = opS(sdBox(pos - np.array([0.2, 0.67, 0.0]), np.array([0.7, 0.11, 0.35])), res); # windows
    res = opS(sdBox(pos - np.array([0.45, 0.67, 0.0]), np.array([0.2, 0.11, 0.5])), res);
    res = opS(sdBox(pos - np.array([-0.1, 0.67, 0.0]), np.array([0.2, 0.11, 0.5])), res);
    res = opS(sdCylH(pos - np.array([-0.8, 0.45, 0.35]), np.array([0.07, 0.1])), res); # headlights
    res = opS(sdCylH(pos - np.array([-0.8, 0.45, -0.35]), np.array([0.07, 0.1])), res);
    res = opU(res, sdCylX(pos - np.array([-0.5, 0.21, 0]), np.array([0.2, 0.55]))); # wheels
    res = opU(res, sdCylX(pos - np.array([0.45, 0.21, 0]), np.array([0.2, 0.55])));
    res = opS(sdBox(pos - np.array([0.2, 0.63, 0.0]), np.array([0.65, 0.11, 0.35])), res); # interior
    res = opS(sdBox(pos - np.array([-0.8, 0.41, 0.0]), np.array([0.2, 0.02, 0.22])), res); # front vent
    res = opS(sdBox(pos - np.array([-0.8, 0.37, 0.0]), np.array([0.2, 0.02, 0.24])), res);
    res = opS(sdBox(pos - np.array([-0.8, 0.33, 0.0]), np.array([0.2, 0.02, 0.24])), res);
    res = opS(sdBox(pos - np.array([-0.8, 0.29, 0.0]), np.array([0.2, 0.02, 0.22])), res);
    res = opU(res, sdBox(pos - np.array([-0.26, 0.57, 0.5]), np.array([0.02, 0.05, 0.07]))); # mirrors
    res = opU(res, sdBox(pos - np.array([-0.26, 0.57, -0.5]), np.array([0.02, 0.05, 0.07])));

    return res

def intersect_car(O, D, S, portal=False):

    for i in range(100):
       if sdBox((O - S) + D * (i * 0.1), np.array([0.6] * 3)) <= 0.0:
           # print("uh", i * 0.1)
           return i * 0.1
    return np.inf


def intersect_portal(O, D, S, R, portal=False):
    # Return the distance from O to the intersection of the ray (O, D) with the
    # sphere (S, R), or +inf if there is no intersection.
    # O and S are 3D points, D (direction) is a normalized vector, R is a scalar.
    a = np.dot(D, D)
    OS = O - S
    b = 2 * np.dot(D, OS)
    c = np.dot(OS, OS) - R * R
    disc = b * b - 4 * a * c
    if disc > 0:
        distSqrt = np.sqrt(disc)
        q = (-b - distSqrt) / 2.0 if b < 0 else (-b + distSqrt) / 2.0
        t0 = q / a
        t1 = c / q
        t0, t1 = min(t0, t1), max(t0, t1)
        if t1 >= 0:
            return t1 if t0 < 0 else t0
    return np.inf

def intersect(O, D, obj, portal=False):
    if obj['type'] == 'plane':
        return intersect_plane(O, D, obj['position'], obj['normal'], portal=portal)
    elif obj['type'] == 'sphere':
        return intersect_sphere(O, D, obj['position'], obj['radius'], portal=portal)
    elif obj['type'] == 'portal':
        return intersect_sphere(O, D, obj['position'], obj['radius'], portal=portal)
    elif obj['type'] == 'car':
        return intersect_car(O, D, obj['position'], portal=portal)

def get_normal(obj, M):
    # Find normal.
    if obj['type'] == 'sphere' or obj['type'] == "portal" or obj['type'] == 'car':
        N = normalize(M - obj['position'])
    elif obj['type'] == 'plane':
        N = obj['normal']
    return N

def get_color(obj, M):
    color = obj['color']
    if not hasattr(color, '__len__'):
        color = color(M)
    return color

def trace_ray(rayO, rayD):
    # Find first point of intersection with the scene.
    t = np.inf
    portal = False
    for i, obj in enumerate(scene):
        t_obj = intersect(rayO, rayD, obj)
        if t_obj < t:
            t, obj_idx = t_obj, i
    # Return None if the ray does not intersect any object.
    if t == np.inf:
        return
    # Find the object.
    obj = scene[obj_idx]
    # if obj['type'] == "car": print("car")
    if obj['type'] == "portal":
        portal = obj
        rayO = rayO + rayD * t + obj['destination']
        t = np.inf
        num_steps = np.inf
        for i, obj in enumerate(scene):
            if obj['type'] == "portal": continue

            # print(obj["type"])

            try:
                i_obj, t_obj = intersect(rayO, rayD, obj, portal=True)
            except Exception:
                pass
            # print("iobj", i_obj)
            if i_obj < num_steps or (i_obj == num_steps and t_obj < t):
                t, obj_idx = t_obj, i
                num_steps = i_obj
        if t == np.inf:
            return
        # print("uh")
        M = ray_at_time(rayO, rayD, num_steps, t)
    else:
        M = rayO + rayD * t
    obj = scene[obj_idx]
    # Find the point of intersection on the object.

    # if obj["type"] == "car": print(t, M)
    # Find properties of the object.
    N = get_normal(obj, M)
    color = get_color(obj, M)
    #if portal:
    #    alpha = 0.7
    #    color = alpha * color + (1 - alpha) * portal['color']
    toL = normalize(L - M)
    toO = normalize(O - M)
    # Shadow: find if the point is shadowed or not.
    l = [intersect(M + N * .0001, toL, obj_sh)
            for k, obj_sh in enumerate(scene) if k != obj_idx]
    if l and min(l) < np.inf and obj["type"] != portal:
        return
    # Start computing the color.
    col_ray = ambient
    # if portal:
    #     alpha = 0.7
    #     col_ray = alpha * col_ray + (1 - alpha) * portal['color']

    # Lambert shading (diffuse).
    #if portal and obj['type'] == "sphere": color = np.array([.5, .223, .5])
    col_ray += obj.get('diffuse_c', diffuse_c) * max(np.dot(N, toL), 0) * color
    # Blinn-Phong shading (specular).
    col_ray += obj.get('specular_c', specular_c) * max(np.dot(N, normalize(toL + toO)), 0) ** specular_k * color_light
    #if portal: return obj, M_, N_, col_ray
    return obj, M, N, col_ray

def add_sphere(position, radius, color):
    return dict(type='sphere', position=np.array(position),
        radius=np.array(radius), color=np.array(color), reflection=.5)

def add_car(position, color):
    return dict(type='car', position=np.array(position), color=np.array(color))

def add_portal(position, radius, color, destination):
    # destination is the offset to the position of the ray
    return dict(type='portal', position=np.array(position),
        radius=np.array(radius), color=np.array(color), reflection=.5, destination=np.array(destination))

def add_plane(position, normal):
    return dict(type='plane', position=np.array(position),
        normal=np.array(normal),
        color=lambda M: (color_plane0
            if (int(M[0] * 2) % 2) == (int(M[2] * 2) % 2) else color_plane1),
        diffuse_c=.75, specular_c=.5, reflection=.25)

# List of objects.
color_plane0 = 1. * np.ones(3)
color_plane1 = 0. * np.ones(3)
scene = [add_portal([.75, .1, 1.], .8, [0., 0., 1.], [-4, 0.1, -2]),
         add_sphere([-.75, .1, 2.25], .6, [.5, .223, .5]),
         add_sphere([-2.75, .1, 3.5], .6, [1., .572, .184]),
         # add_car([-2.75, .1, 3.5], [1, 0, 0]),
         #add_portal([-.75, 1., 1.5], .6, [1., .572, .184], [-1, -1, 0]),
         add_plane([0., -.5, 0.], [0., 1., 0.]),
    ]

# Light position and color.
L = np.array([5., 5., -10.])
color_light = np.ones(3)

# Default light and material parameters.
ambient = .05
diffuse_c = 1.
specular_c = 1.
specular_k = 50

depth_max = 5  # Maximum number of light reflections.
col = np.zeros(3)  # Current color.
O = np.array([0., 0.35, -1.])  # Camera.
Q = np.array([0., 0., 0.])  # Camera pointing to.
img = np.zeros((h, w, 3))

r = float(w) / h
# Screen coordinates: x0, y0, x1, y1.
S = (-1., -1. / r + .25, 1., 1. / r + .25)

# Loop through all pixels.
for i, x in enumerate(np.linspace(S[0], S[2], w)):
    if i % 10 == 0:
        print(i / float(w) * 100, "%")
    for j, y in enumerate(np.linspace(S[1], S[3], h)):
        col[:] = 0
        Q[:2] = (x, y)
        D = normalize(Q - O)
        depth = 0
        rayO, rayD = O, D
        reflection = 1.
        # Loop through initial and secondary rays.
        while depth < depth_max:
            traced = trace_ray(rayO, rayD)
            if not traced:
                break
            obj, M, N, col_ray = traced
            # Reflection: create a new ray.
            rayO, rayD = M + N * .0001, normalize(rayD - 2 * np.dot(rayD, N) * N)
            depth += 1
            col += reflection * col_ray
            reflection *= obj.get('reflection', 1.)
        img[h - j - 1, i, :] = np.clip(col, 0, 1)

plt.imsave('fig.png', img)
