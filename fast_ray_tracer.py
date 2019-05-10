from PIL import Image
import numpy as np
import cv2
import time
import numbers
from functools import reduce

def extract(cond, x):
    if isinstance(x, numbers.Number):
        return x
    else:
        return np.extract(cond, x)

class vec2():
    def __init__(self, x, y):
        (self.x, self.y) = (x, y)
    def __mul__(self, other):
        return vec2(self.x * other, self.y * other)
    def __add__(self, other):
        return vec2(self.x + other.x, self.y + other.y)
    def __sub__(self, other):
        return vec2(self.x - other.x, self.y - other.y)
    def dot(self, other):
        return (self.x * other.x) + (self.y * other.y)
    def __abs__(self):
        return self.dot(self)
    def max(self, num):
        return vec2(max(self.x, num), max(self.y, num))
    def norm(self):
        mag = np.sqrt(abs(self))
        return self * (1.0 / np.where(mag == 0, 1, mag))

class vec3():
    def __init__(self, x, y, z):
        (self.x, self.y, self.z) = (x, y, z)
    def __mul__(self, other):
        return vec3(self.x * other, self.y * other, self.z * other)
    def __add__(self, other):
        return vec3(self.x + other.x, self.y + other.y, self.z + other.z)
    def __sub__(self, other):
        return vec3(self.x - other.x, self.y - other.y, self.z - other.z)
    def dot(self, other):
        return (self.x * other.x) + (self.y * other.y) + (self.z * other.z)
    def __abs__(self):
        return self.dot(self)
    def max(self, num):
        return vec3(max(self.x, num), max(self.y, num), max(self.z, num))
    def __repr__(self):
        return str(self.components())
    def norm(self):
        mag = np.sqrt(abs(self))
        return self * (1.0 / np.where(mag == 0, 1, mag))
    def components(self):
        return (self.x, self.y, self.z)
    def extract(self, cond):
        return vec3(extract(cond, self.x),
                    extract(cond, self.y),
                    extract(cond, self.z))
    def place(self, cond):
        r = vec3(np.zeros(cond.shape), np.zeros(cond.shape), np.zeros(cond.shape))
        np.place(r.x, cond, self.x)
        np.place(r.y, cond, self.y)
        np.place(r.z, cond, self.z)
        return r
rgb = vec3

(w, h) = (400, 300)         # Screen size
L = vec3(5, 5., -10)        # Point light position
E = vec3(0., 0.35, -1.)     # Eye position
FARAWAY = 1.0e39            # an implausibly huge distance

def raytrace(O, D, scene, bounce = 0):
    # O is the ray origin, D is the normalized ray direction
    # scene is a list of Sphere objects (see below)
    # bounce is the number of the bounce, starting at zero for camera rays

    distances = [s.intersect(O, D) for s in scene]
    nearest = reduce(np.minimum, distances)
    color = rgb(0, 0, 0)
    for (s, d) in zip(scene, distances):
        hit = (nearest != FARAWAY) & (d == nearest)
        if np.any(hit):
            dc = extract(hit, d)
            Oc = O.extract(hit)
            Dc = D.extract(hit)
            cc = s.light(Oc, Dc, dc, scene, bounce)
            color += cc.place(hit)
    return color

class Sphere:
    def __init__(self, center, r, diffuse, mirror = 0.5):
        self.c = center
        self.r = r
        self.diffuse = diffuse
        self.mirror = mirror

    def intersect(self, O, D):
        b = 2 * D.dot(O - self.c)
        c = abs(self.c) + abs(O) - 2 * self.c.dot(O) - (self.r * self.r)
        disc = (b ** 2) - (4 * c)
        sq = np.sqrt(np.maximum(0, disc))
        h0 = (-b - sq) / 2
        h1 = (-b + sq) / 2
        h = np.where((h0 > 0) & (h0 < h1), h0, h1)
        pred = (disc > 0) & (h > 0)
        return np.where(pred, h, FARAWAY)

    def diffusecolor(self, M):
        return self.diffuse

    def light(self, O, D, d, scene, bounce):
        M = (O + D * d)                         # intersection point
        N = (M - self.c) * (1. / self.r)        # normal
        toL = (L - M).norm()                    # direction to light
        toO = (E - M).norm()                    # direction to ray origin
        nudged = M + N * .0001                  # M nudged to avoid itself

        # Shadow: find if the point is shadowed or not.
        # This amounts to finding out if M can see the light
        light_distances = [s.intersect(nudged, toL) for s in scene]
        light_nearest = reduce(np.minimum, light_distances)
        seelight = light_distances[scene.index(self)] == light_nearest

        # Ambient
        color = rgb(0.05, 0.05, 0.05)

        # Lambert shading (diffuse)
        lv = np.maximum(N.dot(toL), 0)
        color += self.diffusecolor(M) * lv * seelight

        # Reflection
        if bounce < 2:
            rayD = (D - N * 2 * D.dot(N)).norm()
            color += raytrace(nudged, rayD, scene, bounce + 1) * self.mirror

        # Blinn-Phong shading (specular)
        phong = N.dot((toL + toO).norm())
        color += rgb(1, 1, 1) * np.power(np.clip(phong, 0, 1), 50) * seelight
        return color

def sdBox(p, b):
    d = vec3(abs(p) - b.x, abs(p) - b.y, abs(p) - b.z)
    return min(max(d.x, max(d.y, d.z)), 0.0) + np.sqrt(abs(d.max(0.0)))

def sdCylH(p, h):
    intermed = abs(vec2(np.sqrt(abs(vec2(p.y, p.z))), p.x))
    d = vec2(intermed - h.x, intermed - h.y)
    return min(max(d.x, d.y), 0.0) + np.sqrt(abs(d.max(0.0)))

def sdCylX(p, h):
    intermed = abs(vec2(np.sqrt(abs(vec2(p.x, p.y))), p.z))
    d = vec2(intermed - h.x, intermed - h.y)
    return min(max(d.x, d.y), 0.0) + np.sqrt(abs(d.max(0.0)))

def sdRoundBox(p, b, r):
    d = vec3(abs(p) - b.x, abs(p) - b.y, abs(p) - b.z)
    return np.sqrt(abs(d.max(0.0))) - r + min(max(d.x, max(d.y, d.z)), 0.0)

def opU(d1, d2):
    return min(d1, d2)

def opS(d1, d2):
    return max(-1 * d1, d2)

def carMap(pos):
    res = 0;

    res = opU(res, sdRoundBox(pos - vec3(0, 0.3, 0), vec3(0.7, 0.07, 0.3), 0.2)); # body
    res = opU(res, sdRoundBox(pos - vec3(0.2, 0.5, 0.0), vec3(0.5, 0.3, 0.3), 0.1));
    res = opS(sdBox(pos - vec3(0.2, 0.67, 0.0), vec3(0.7, 0.11, 0.35)), res); # windows
    res = opS(sdBox(pos - vec3(0.45, 0.67, 0.0), vec3(0.2, 0.11, 0.5)), res);
    res = opS(sdBox(pos - vec3(-0.1, 0.67, 0.0), vec3(0.2, 0.11, 0.5)), res);
    res = opS(sdCylH(pos - vec3(-0.8, 0.45, 0.35), vec2(0.07, 0.1)), res); # headlights
    res = opS(sdCylH(pos - vec3(-0.8, 0.45, -0.35), vec2(0.07, 0.1)), res);
    res = opU(res, sdCylX(pos - vec3(-0.5, 0.21, 0), vec2(0.2, 0.55))); # wheels
    res = opU(res, sdCylX(pos - vec3(0.45, 0.21, 0), vec2(0.2, 0.55)));
    res = opS(sdBox(pos - vec3(0.2, 0.63, 0.0), vec3(0.65, 0.11, 0.35)), res); # interior
    res = opS(sdBox(pos - vec3(-0.8, 0.41, 0.0), vec3(0.2, 0.02, 0.22)), res); # front vent
    res = opS(sdBox(pos - vec3(-0.8, 0.37, 0.0), vec3(0.2, 0.02, 0.24)), res);
    res = opS(sdBox(pos - vec3(-0.8, 0.33, 0.0), vec3(0.2, 0.02, 0.24)), res);
    res = opS(sdBox(pos - vec3(-0.8, 0.29, 0.0), vec3(0.2, 0.02, 0.22)), res);
    res = opU(res, sdBox(pos - vec3(-0.26, 0.57, 0.5), vec3(0.02, 0.05, 0.07))); # mirrors
    res = opU(res, sdBox(pos - vec3(-0.26, 0.57, -0.5), vec3(0.02, 0.05, 0.07)));

    return res

class Car:
    def __init__(self, center):
        self.c = center

    def intersect(self, O, D):
        print(D.x)
        intersections = np.zeros(len(D.x))
        for row in range(D.x.shape[0]):
            d = vec3(D.x[row], D.y[row], D.z[row])
            for i in range(10000):
                if carMap(O + d * (i * 0.0001)) >= 0.0:
                    intersections[row] = i * 0.0001
                    break;
        return intersections

    def light(self, O, D, d, scene, bounce):
        color = rgb(0.5, 0.05, 0.05)
        return color


class Portal:
    def __init__(self, center, r, diffuse, offset, mirror = 0.5):
        self.c = center
        self.r = r
        self.offset = offset
        self.diffuse = diffuse
        self.mirror = mirror

    def intersect(self, O, D):
        b = 2 * D.dot(O - self.c)
        c = abs(self.c) + abs(O) - 2 * self.c.dot(O) - (self.r * self.r)
        disc = (b ** 2) - (4 * c)
        sq = np.sqrt(np.maximum(0, disc))
        h0 = (-b - sq) / 2
        h1 = (-b + sq) / 2
        h = np.where((h0 > 0) & (h0 < h1), h0, h1)
        pred = (disc > 0) & (h > 0)
        return np.where(pred, h, FARAWAY)

    def diffusecolor(self, M):
        return self.diffuse

    def light(self, O, D, d, scene, bounce):
        O = (O + self.offset) + D*d
        distances = [s.intersect(O, D) for s in scene]
        nearest = reduce(np.minimum, distances)
        color = rgb(0, 0, 0)
        for (s, d) in zip(scene, distances):
            hit = (nearest != FARAWAY) & (d == nearest)
            if np.any(hit):
                dc = extract(hit, d)
                Oc = O.extract(hit)
                Dc = D.extract(hit)
                cc = s.light(Oc, Dc, dc, scene, bounce)
                color += cc.place(hit)
        #M = (O + D * d)                         # intersection point
        #N = (M - self.c) * (1. / self.r)        # normal
        #toL = (L - M).norm()                    # direction to light
        #toO = (E - M).norm()                    # direction to ray origin
        #nudged = M + N * .0001                  # M nudged to avoid itself

        ## Shadow: find if the point is shadowed or not.
        ## This amounts to finding out if M can see the light
        #light_distances = [s.intersect(nudged, toL) for s in scene]
        #light_nearest = reduce(np.minimum, light_distances)
        #seelight = light_distances[scene.index(self)] == light_nearest

        ## Ambient
        #color = rgb(0.05, 0.05, 0.05)

        ## Lambert shading (diffuse)
        #lv = np.maximum(N.dot(toL), 0)
        #color += self.diffusecolor(M) * lv * seelight

        ## Reflection
        #if bounce < 2:
        #    rayD = (D - N * 2 * D.dot(N)).norm()
        #    color += raytrace(nudged, rayD, scene, bounce + 1) * self.mirror

        ## Blinn-Phong shading (specular)
        #phong = N.dot((toL + toO).norm())
        #color += rgb(1, 1, 1) * np.power(np.clip(phong, 0, 1), 50) * seelight
        return color

class CheckeredSphere(Sphere):
    def diffusecolor(self, M):
        checker = ((M.x * 2).astype(int) % 2) == ((M.z * 2).astype(int) % 2)
        return self.diffuse * checker

scene = [
    Portal(vec3(.75, .1, 1.), .8, rgb(0, 0, 1), offset=vec3(-4, 0.1, -2)),
    #Car(vec3(-0.75, .1, 2.25)),
    Sphere(vec3(-.75, .1, 2.25), .6, rgb(.5, .223, .5)),
    Sphere(vec3(-2.75, .1, 3.5), .6, rgb(1., .572, .184)),
    CheckeredSphere(vec3(0,-99999.5, 0), 99999, rgb(.75, .75, .75), 0.25),
    ]

r = float(w) / h
# Screen coordinates: x0, y0, x1, y1.
S = (-1., 1. / r + .25, 1., -1. / r + .25)
x = np.tile(np.linspace(S[0], S[2], w), h)
y = np.repeat(np.linspace(S[1], S[3], h), w)

t0 = time.time()
Q = vec3(x, y, 0)
color = raytrace(E, (Q - E).norm(), scene)

#rgb = [Image.fromarray((255 * np.clip(c, 0, 1).reshape((h, w))).astype(np.uint8), "L") for c in color.components()]
#Image.merge("RGB", rgb).save("fig.png")
r, g, b = ((255 * np.clip(c, 0, 1).reshape((h, w))).astype(np.uint8) for c in color.components())
rgbArray = np.zeros((h,w,3), 'uint8')
rgbArray[..., 0] = r
rgbArray[..., 1] = g
rgbArray[..., 2] = b
print("Took", time.time() - t0)
#plt.imshow(rgbArray)
#plt.show()
while(1):
    cv2.imshow('img',rgbArray)
    k = cv2.waitKey(0)
    if k==27:    # Esc key to stop
        break
    elif k==119: # w
        E = E + vec3(0, 0, 0.2)
    elif k==97: # a
        E = E + vec3(-0.5, 0, 0)
    elif k==115: # s
        E = E + vec3(0, 0, -0.2)
    elif k==100: # d
        E = E + vec3(0.5, 0, 0)
    elif k==-1:  # normally -1 returned,so don't print it
        continue
    else:
        print(k) # else print its valueimg = np.array([255 * np.clip(c, 0, 1).reshape((h, w)).astype(np.uint8) for c in color.components()])
    color = raytrace(E, (Q - E).norm(), scene)
    r, g, b = ((255 * np.clip(c, 0, 1).reshape((h, w))).astype(np.uint8) for c in color.components())
    rgbArray = np.zeros((h,w,3), 'uint8')
    rgbArray[..., 0] = r
    rgbArray[..., 1] = g
    rgbArray[..., 2] = b

cv2.destroyAllWindows()
