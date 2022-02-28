from os import environ
environ['PYGAME_HIDE_SUPPORT_PROMPT'] = '1'

import time, os, numpy as np, math, random, cv2, sys, copy, pygame
from PIL import Image, ImageDraw, ImageFont
from struct import unpack



#* Body class on init loads the STL and calculates some variables, such as center and body size. 
class Body:
    def __init__(self, path=os.path.join(os.getcwd(), "Body.stl")):
        self.body = self.load_body(path)    #* Loading body from STL file
        self.move_by_offset()
        self.rotated_body = copy.deepcopy(self.body)   #* Creating a copy of the body so that the original body remains unchanged
        
        self.size = self.find_size()    #* Finding size of the body
        self.center = (self.size[0]/2, self.size[1]/2, self.size[2]/2)    #* Finding center of the body
    
    
    #* Move the body so that the body is next to point (0,0,0)
    def move_by_offset(self):
        x_offset = min([vertex[0] for facet in self.body for vertex in facet[1:]])
        y_offset = min([vertex[1] for facet in self.body for vertex in facet[1:]])
        z_offset = min([vertex[2] for facet in self.body for vertex in facet[1:]])
        
        for facet in self.body:
            for vertex in facet[1:]:
                vertex[0] = vertex[0] - x_offset
                vertex[1] = vertex[1] - y_offset
                vertex[2] = vertex[2] - z_offset
        return self.body
        
    
    #! Currently not in use, left for later
    #* Calculates body center.
    def find_center(self):
        max_x = max([vertex[0] for facet in self.body for vertex in facet[1:]])
        min_x = min([vertex[0] for facet in self.body for vertex in facet[1:]])
        
        max_y = max([vertex[1] for facet in self.body for vertex in facet[1:]])
        min_y = min([vertex[1] for facet in self.body for vertex in facet[1:]])
        
        max_z = max([vertex[2] for facet in self.body for vertex in facet[1:]])
        min_z = min([vertex[2] for facet in self.body for vertex in facet[1:]])
        
        center_x = (max_x + min_x) / 2
        center_y = (max_y + min_y) / 2
        center_z = (max_z + min_z) / 2
        center = (center_x, center_y, center_z)        
        return center
        
    
    #* Calculates body size.
    def find_size(self):
        size = (abs(max([vertex[0] for facet in self.body for vertex in facet[1:]]) - min([vertex[0] for facet in self.body for vertex in facet[1:]])),
                abs(max([vertex[1] for facet in self.body for vertex in facet[1:]]) - min([vertex[1] for facet in self.body for vertex in facet[1:]])),
                abs(max([vertex[2] for facet in self.body for vertex in facet[1:]]) - min([vertex[2] for facet in self.body for vertex in facet[1:]])))
        return size
        
    
    #* Loads body from file.
    def load_body(self, path):
        body = []
        with open(path, "rb") as f:
            #* Loading body if ascii coded
            if f.read(5) == b"solid":             #TODO: Reading normal from ascii STL
                print("This version does not support ascii coded STL files. Try using binary coded STL")
                exit()
                # raw_data = f.readlines()
                # f.close()
                
                # c = 0
                # for line in raw_data:
                #     if line[:6] == "      " and c < 3:
                #         if c == 0:
                #             body.append([])
                #         c = c + 1
                #         vertex = line[15:].split(" ")
                #         body[-1].append([float(vertex[0]), float(vertex[1]), float(vertex[2])])
                #     else:
                #         c = 0
            
            else:
                #* Loading body if binary coded
                f.seek(80) #* Skipping header
                facets_count = unpack("<i", f.read(4))[0]
                facets = []
                for _ in range(facets_count):
                    facets.append(unpack("<ffffffffffffH", f.read(50)))
                
                for facet in facets:
                    body.append([[facet[0], facet[1], facet[2]], [facet[3], facet[4], facet[5]], [facet[6], facet[7], facet[8]], [facet[9], facet[10], facet[11]]])
        return body     
    
    
    #* Rotates the original body (including facets normal) by given angle.
    def rotate(self, angle):
        rotated_body = []
        for facet in self.body:     #* Iterating through every facet in the body
            rotated_body.append([])
            
            point = facet[0]        #* Rotating facet normal vector
            #* Some boring math ⬇
            a = np.deg2rad(angle[2])
            x = point[0]
            y = point[1]
            rx = x * np.cos(a) - y * np.sin(a)
            ry = x * np.sin(a) + y * np.cos(a)

            a = np.deg2rad(angle[1])
            x = rx
            z = point[2]
            rx = x * np.cos(a) - z * np.sin(a)
            rz = x * np.sin(a) + z * np.cos(a)
            
            a = np.deg2rad(angle[0])
            y = ry
            z = rz
            ry = y * np.cos(a) - z * np.sin(a)
            rz = y * np.sin(a) + z * np.cos(a)
            
            rotated_body[-1].append([rx, ry, rz])
            
            for point in facet[1:]:     #* Iterating through every point of the facet
                #* Some boring math ⬇
                a = np.deg2rad(angle[2])
                x = point[0] - self.center[0]
                y = point[1] - self.center[1]
                rx = x * np.cos(a) - y * np.sin(a)
                ry = x * np.sin(a) + y * np.cos(a)
                rx = rx + self.center[0]
                ry = ry + self.center[1]
                
                a = np.deg2rad(angle[1])
                x = rx - self.center[0]
                z = point[2] - self.center[2]
                rx = x * np.cos(a) - z * np.sin(a)
                rz = x * np.sin(a) + z * np.cos(a)
                rx = rx + self.center[0]
                rz = rz + self.center[2]
                
                a = np.deg2rad(angle[0])
                y = ry - self.center[1]
                z = rz - self.center[2]
                ry = y * np.cos(a) - z * np.sin(a)
                rz = y * np.sin(a) + z * np.cos(a)
                ry = ry + self.center[1]
                rz = rz + self.center[2]

                rotated_body[-1].append([rx, ry, rz])
            
        self.rotated_body = rotated_body
        return rotated_body
       
        

#* Camera class.
class Cam:
    def __init__(self, body_center, y_distance_multiplier):
        self.pos = [body_center[0], body_center[1]*y_distance_multiplier, body_center[2]]      #* Setting camera position
        


#* Screen is an object between the body and the camera onto which body points are projected.
class Screen:
    def __init__(self, body_center, body_size, resolution, window_size, screen_to_body_ratio, line_size, background_color, body_color, brightness, y_distance_multiplier):
        self.resolution = resolution        #* Rendering resolution
        self.window_size = window_size      #* Window size
        self.screen_to_body_ratio = screen_to_body_ratio     #* Body-to-screen width ratio
        self.line_size = line_size                  #* Linewidth (only in mesh mode)
        self.background_color = background_color   #* Background color
        self.body_color = body_color          #* Body color
        self.brightness = brightness             #* How dark the darkest elements should be (0 - black, 1 - Body color)
        self.y_distance_multiplier = y_distance_multiplier      #* Where the "screen" should be between the body and the camera, it must be smaller than camera_y_distance_multiplier (the bigger the smaller the rendered object will be)
        
        self.size = [body_size[0]/self.screen_to_body_ratio, body_size[0]/self.screen_to_body_ratio * 9/16]
        self.pos = [body_center[0] - self.size[0]/2, body_center[1]*self.y_distance_multiplier, body_center[2] - self.size[1]/2]
        
    
    #* Calculates where body point should be displayed.
    def project_point(self, point, cam):
        pixel_x = (point[0] - cam.pos[0]) * (cam.pos[1] - self.pos[1]) / (cam.pos[1] - point[1]) + cam.pos[0] - self.pos[0]
        pixel_y = self.size[1] - ((point[2] - cam.pos[2]) * (cam.pos[1] - self.pos[1]) / (cam.pos[1] - point[1]) + cam.pos[2] - self.pos[2])
        
        pixel_x = pixel_x * self.resolution[0] / self.size[0]
        pixel_y = pixel_y * self.resolution[1] / self.size[1]
        
        return (int(pixel_x), int(pixel_y))
    
    #* Generates 2D body image by projecting(referring to "project_point") body surfaces onto the screen.
    def generate_img(self, body, cam, mesh=False):
        img = Image.new("RGB", self.resolution, self.background_color)
        draw = ImageDraw.Draw(img)
        
        sorted_body = sorted(body.rotated_body, reverse=True, key=lambda x: (x[1][1] + x[2][1] + x[3][1]) / 3)  #* Sorting Body facets by distance from the camera
        
        for facet in sorted_body:       #* Iterating through every facet in the body
            corners = []
            for vertex in facet[1:]:    #* Iterating through every vertex(skipping facet normal)
                pixel = self.project_point(vertex, cam)     #* Projecting point onto screen
                if pixel[0] < self.resolution[0] and pixel[1] < self.resolution[1]:     #* If the pixel fits on the screen, add it to the list to be drawn.
                    corners.append(pixel)
            
            
            if not mesh:
                #* Some boring math ⬇
                normal_to_camera_angle = np.arccos((1 * -facet[0][1]) / ((1)**0.5 * (facet[0][0]**2 + facet[0][1]**2 + facet[0][2]**2)**0.5))       #* Calculating angle of the current triangle to the camera
                
                if normal_to_camera_angle > np.pi / 2:      #* Saving computing power 
                    continue
                
                brightness = (1 - normal_to_camera_angle / np.pi) * self.brightness     #* Setting the brightness of the current triangle
                
                color = (int(self.body_color[0] * brightness), int(self.body_color[1] * brightness), int(self.body_color[2] * brightness))     #* Calculating color of the current triangle

            else:
                color = (self.body_color[0], self.body_color[1], self.body_color[2])
            
            
            #* If mesh mode is enabled, draw mesh
            if mesh:
                #* If triangle data is valid
                if len(corners) == 3:
                    draw.line([corners[0], corners[1]], fill=color, width=self.line_size)
                    draw.line([corners[1], corners[2]], fill=color, width=self.line_size)
                    draw.line([corners[2], corners[0]], fill=color, width=self.line_size)
                    
            #* If mesh mode is disabled, draw solid triangle
            else:
                #* If triangle data is valid
                if len(corners) == 3:
                    draw.polygon([corners[0], corners[1], corners[2]], fill=color)
            
        
        img = img.resize((self.window_size[0], self.window_size[1]))    #* Resizing the image to the given window size
        return img
        


#* Settings
resolution=(1600, 900)      #* Rendering resolution
window_size=(1200, 675)     #* Window size
screen_to_body_ratio=0.8    #* Body-to-screen width ratio
line_size=1                 #* Linewidth (only in mesh mode)
background_color=(0,0,0)    #* Window background color
body_color=(0,255,255)    #* Color of the body
brightness=0.9              #* Brightness multiplier

#* Where the "screen" should be between the body and the camera, it must be smaller than camera_y_distance_multiplier
#* (the bigger, the smaller the rendered object will be)
screen_y_distance_multiplier=100

#* Where the "camera" should be located, must be greater than the screen_y_distance_multiplier
camera_y_distance_multiplier = 200



#* Find STL file path
if len(sys.argv) > 1:
    path = os.path.join(os.getcwd(), sys.argv[1])
else:
    path = os.path.join(os.getcwd(), "Body.stl")
    
#* Initializing scene elements
body = Body(path)
cam = Cam(body.center, camera_y_distance_multiplier)
screen = Screen(body.center, body.size, resolution, window_size, screen_to_body_ratio, line_size, background_color, body_color, brightness, screen_y_distance_multiplier)

# print(body.center, body.size, cam.pos)

mesh=False  #* Render mode

pygame.font.init()
display = pygame.display.set_mode(window_size)
clock = pygame.time.Clock()
myfont = pygame.font.SysFont("Arial", 20)


#* Main loop
while True:
    for a in range(360):
        for event in pygame.event.get():
            
            #* Terminate program
            if event.type == pygame.QUIT:
                pygame.quit()
                quit()
                
            elif event.type == pygame.KEYDOWN:
                
                #* Terminate program
                if event.key == pygame.K_ESCAPE or event.key == pygame.K_q:
                    pygame.quit()
                    quit()
                
                #* Chane render mode
                elif event.key == pygame.K_m:
                    if mesh == True:
                        mesh = False
                    else:
                        mesh = True
        
        
        body.rotate((a, a, a))  #* Rotating body

        img = screen.generate_img(body, cam, mesh)  #* Rendering frame
        
        frame = pygame.image.fromstring(img.tobytes(), img.size, img.mode)   #* Converting img from PIL image to pygame surface
        frame_rect = frame.get_rect()
        frame_rect.center = window_size[0]//2, window_size[1]//2
        
        FPS_text = myfont.render(("FPS: " + str(int(clock.get_fps()))), False, (255, 255, 255))     #* Creating FPS text
        
        display.blit(frame, frame_rect)     #* Displaying rendered body
        display.blit(FPS_text, (10,10))     #* Displaying FPS value
        
        clock.tick(1000)        #* Updating clock (FPS countng)
        pygame.display.update()     #* Apply changes to the screen