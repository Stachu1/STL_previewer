import time, os, numpy as np, math, random, cv2, sys
from PIL import Image, ImageDraw
from struct import unpack



class Body:
    def __init__(self):
        if len(sys.argv) > 1:
            self.path = os.path.join(os.getcwd(), sys.argv[1])
        else:
            self.path = os.path.join(os.getcwd(), "Body.stl")  
        
        self.body = self.load_body()
        self.rotated_body = self.body
        
        self.center = ((max([vertex[0] for facet in self.body for vertex in facet]) + min([vertex[0] for facet in self.body for vertex in facet])) / 2,
                       (max([vertex[1] for facet in self.body for vertex in facet]) + min([vertex[1] for facet in self.body for vertex in facet])) / 2,
                       (max([vertex[2] for facet in self.body for vertex in facet]) + min([vertex[2] for facet in self.body for vertex in facet])) / 2)
        
        self.size = ((max([vertex[0] for facet in self.body for vertex in facet]) - min([vertex[0] for facet in self.body for vertex in facet])),
                       (max([vertex[1] for facet in self.body for vertex in facet]) - min([vertex[1] for facet in self.body for vertex in facet])),
                       (max([vertex[2] for facet in self.body for vertex in facet]) - min([vertex[2] for facet in self.body for vertex in facet])))
    
    
    def load_body(self):
        body = []
        with open(self.path, "rb") as f:
            if f.read(5) == b"solid":
                raw_data = f.readlines()
                f.close()
                
                c = 0
                for line in raw_data:
                    if line[:6] == "      " and c < 3:
                        if c == 0:
                            body.append([])
                        c = c + 1
                        vertex = line[15:].split(" ")
                        body[-1].append([float(vertex[0]), float(vertex[1]), float(vertex[2])])
                    else:
                        c = 0
            
            else:
                f.seek(80) # Skipping header

                facets_count = unpack("<i", f.read(4))[0] # Triangle count
                
                facets = []
                for _ in range(facets_count):
                    facets.append(unpack("<ffffffffffffH", f.read(50))) # Decoding triangles
                
                for facet in facets:
                    body.append([[facet[3], facet[4], facet[5]], [facet[6], facet[7], facet[8]], [facet[9], facet[10], facet[11]]])
        return body
                
    
    
    def rotate(self, angle):
        rotated_body = []
        for facet in self.body:
            rotated_body.append([])
            for point in facet:
                a = np.deg2rad(angle[2])
                x = point[0] - self.center[0]
                y = point[1] - self.center[1]
                rx = x * np.cos(a) - y * np.sin(a)
                ry = x * np.sin(a) + y * np.cos(a)
                rx = rx + self.center[0]
                ry = ry + self.center[1]
                
                a = np.deg2rad(angle[1])
                x = rx - self.center[0]
                z = point[2] - self.center[1]
                rx = x * np.cos(a) - z * np.sin(a)
                rz = x * np.sin(a) + z * np.cos(a)
                rx = rx + self.center[0]
                rz = rz + self.center[1]
                
                a = np.deg2rad(angle[0])
                y = ry - self.center[0]
                z = rz - self.center[1]
                ry = y * np.cos(a) - z * np.sin(a)
                rz = y * np.sin(a) + z * np.cos(a)
                ry = ry + self.center[0]
                rz = rz + self.center[1]

                rotated_body[-1].append([rx, ry, rz])
        return rotated_body
       
        
        
class Cam:
    def __init__(self, body_center):
        self.pos = [body_center[0], body_center[1]*10, body_center[2]]
        


class Screen:
    def __init__(self, body_center, body_size):
        self.resolution = [1280, 720]
        self.screen_to_body_ratio = 0.8
        self.size = [body_size[0]/self.screen_to_body_ratio, body_size[0]/self.screen_to_body_ratio * 9/16]
        self.display_size = [800, 450]
        self.pos = [body_center[0] - self.size[0]/2, body_center[1]*5, body_center[2] - self.size[1]/2]
        
    
    def project_point(self, point, cam):
        pixel_x = (point[0] - cam.pos[0]) * (cam.pos[1] - self.pos[1]) / (cam.pos[1] - point[1]) + cam.pos[0] - self.pos[0]
        pixel_y = self.size[1] - ((point[2] - cam.pos[2]) * (cam.pos[1] - self.pos[1]) / (cam.pos[1] - point[1]) + cam.pos[2] - self.pos[2])
        
        pixel_x = pixel_x * self.resolution[0] / self.size[0]
        pixel_y = pixel_y * self.resolution[1] / self.size[1]
        
        return (int(pixel_x), int(pixel_y))
    
    
    def generate_img(self, body, cam):
        img = Image.new("RGB", tuple(self.resolution), (0,0,0))
        draw = ImageDraw.Draw(img)
        
        for facet in body.rotated_body:
            corners = []
            for vertex in facet:
                pixel = self.project_point(vertex, cam)
                if pixel[0] < self.resolution[0] and pixel[1] < self.resolution[1]:
                    corners.append(pixel)
            if len(corners) == 3:
                draw.line([corners[0], corners[1]], fill=(255,255,255), width=2)
                draw.line([corners[1], corners[2]], fill=(255,255,255), width=2)
                draw.line([corners[2], corners[0]], fill=(255,255,255), width=2)
        
        # for facet in body.body:     #* Create list with all vertexes
        #     for vertex in facet:
        #         vertexes.append(vertex)
        
        # filtered_vertexes = []      #* Filter all internal vertexes
        # for vertex in vertexes:
        #     if vertex not in filtered_vertexes:
        #         filtered_vertexes.append(vertex)
        
        # corners = []                #* Project points on screen
        # for vertex in filtered_vertexes:
        #     pixel = self.project_point(vertex, cam)
        #     if pixel[0] < self.size[0] and pixel[1] < self.size[1]:
        #         corners.append(pixel)
        
        img = img.resize((self.display_size[0], self.display_size[1]))
        return img
        


body = Body()
cam = Cam(body.center)
screen = Screen(body.center, body.size)

print(body.center, body.size, cam.pos)

# body.rotated_body = body.rotate((0,0,0))
# img = screen.generate_img(body, cam)
# img.show()

# input("")

r = 0
while True:
    for r in range(360):
        body.rotated_body = body.rotate((0, 0, r))
        img = screen.generate_img(body, cam)
        open_cv_image = np.array(img) 
        
        cv2.imshow("ELO", open_cv_image)
    
        if cv2.waitKey(1) & 0xFF == ord('q'):
            cv2.destroyAllWindows()
            exit()