import time, os, numpy as np, math, random, cv2, sys, copy
from PIL import Image, ImageDraw, ImageFont
from struct import unpack



#* Body class on init loads the STL and calculates some variables, such as center and body size. 
class Body:
    def __init__(self):
        #* Find STL file path
        if len(sys.argv) > 1:
            self.path = os.path.join(os.getcwd(), sys.argv[1])
        else:
            self.path = os.path.join(os.getcwd(), "Body.stl")  
        
        self.body = self.load_body()    #* Loading body from STL file
        self.rotated_body = copy.deepcopy(self.body)   #* Creating a copy of the body so that the original body remains unchanged
        
        self.center = self.find_center()    #* Finding center of the body
        self.size = self.find_size()    #* Finding size of the body
        
        
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
    def load_body(self):
        body = []
        with open(self.path, "rb") as f:
            #* Loading body if ascii coded
            # if f.read(5) == b"solid":             #TODO: Reading normal from ascii STL
            #     raw_data = f.readlines()
            #     f.close()
                
            #     c = 0
            #     for line in raw_data:
            #         if line[:6] == "      " and c < 3:
            #             if c == 0:
            #                 body.append([])
            #             c = c + 1
            #             vertex = line[15:].split(" ")
            #             body[-1].append([float(vertex[0]), float(vertex[1]), float(vertex[2])])
            #         else:
            #             c = 0
            
            # else:
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
            for point in facet:     #* Iterating through every point(facet normal included) of the facet
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
        return rotated_body
       
        

#* Camera class.
class Cam:
    def __init__(self, body_center):
        self.y_distance_multiplier = 100     #* Where camera should be in reference to Body (recomended - 10)
        self.pos = [body_center[0], body_center[1]*self.y_distance_multiplier, body_center[2]]      #* Setting camera position
        


#* Screen is an object between the body and the camera onto which body points are projected.
class Screen:
    def __init__(self, body_center, body_size):
        self.resolution = [1600, 900]       #* Rendering resolution
        self.window_size = [1200, 675]      #* Window size
        self.screen_to_body_ratio = 0.8     #* Screen-to-body width ratio
        self.line_size = 1                  #* Linewidth (only in mesh mode)
        self.background_color = (0, 0, 0)   #* Background color
        self.color = (255, 255, 0)          #* Body color
        self.min_brightness = 0             #* How dark the darkest elements should be (0 - black, 1 - Body color)
        self.y_distance_multiplier = 50      #* Where screen should be between Body and camera, it needs to be smaller than camera y_distance_multiplier (the bigger the smaller the rendered object will be)
        
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
        img = Image.new("RGB", tuple(self.resolution), self.background_color)
        draw = ImageDraw.Draw(img)
        
        sorted_body = sorted(body.rotated_body, reverse=True, key=lambda x: abs(x[1][1] + x[2][1] + x[3][1]) / 3)  #* Sorting Body facets by distance from the camera
        min_y = abs(sorted_body[0][1][1] + sorted_body[0][2][1] + sorted_body[0][3][1]) / 3        #* Calculation of the distance from the camera to the farthest facet
        max_y = abs(sorted_body[-1][1][1] + sorted_body[-1][2][1] + sorted_body[-1][3][1]) / 3      #* Calculating the distance from the camera to the nearest facet
        
        for facet in sorted_body:       #* Iterating through every facet in the body
            corners = []
            for vertex in facet[1:]:    #* Iterating through every vertex(skipping facet normal)
                pixel = self.project_point(vertex, cam)     #* Projecting point onto screen
                if pixel[0] < self.resolution[0] and pixel[1] < self.resolution[1]:     #* If the pixel fits on the screen, add it to the list to be drawn.
                    corners.append(pixel)
            
            
            avg_y = (facet[1][1] + facet[2][1] + facet[3][1]) / 3       #* Calculating the distance from the camera to the current facet
            brightness = (avg_y - min_y) * (1 - self.min_brightness) / (max_y - min_y) + self.min_brightness        #* Setting the brightness of the current triangle
            color = (int(self.color[0] * brightness), int(self.color[1] * brightness), int(self.color[2] * brightness))     #* Calculating color of the current triangle
            
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
        



#* Initializing scene elements
body = Body()
cam = Cam(body.center)
screen = Screen(body.center, body.size)

# print(body.center, body.size, cam.pos)


last_frame = time.time()    #* Used for calculating FPS
mesh=False  #* Render mode

#* Main loop
while True:
    for a in range(360):
        body.rotated_body = body.rotate((a, a, a))  #* Rotating body

        img = screen.generate_img(body, cam, mesh)  #* Rendering frame
        
        frame = np.array(img)   #* Converting img from PIL image to np.array
        
        fps = 1/(time.time() - last_frame)      #* Calculating FPS
        last_frame = time.time()
        if fps < 10:
            fps = round(fps, 2)
        else:
            fps = int(fps)
        
        cv2.putText(frame, ("FPS: " + str(fps)), (10, 20), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1, cv2.LINE_AA)   #* Add FPS to frame
        
        cv2.imshow("ELO", frame)    #* Update frame
        
        #* Chane render mode
        if cv2.waitKey(1) & 0xFF == ord('m'):
            if mesh == True:
                mesh = False
            else:
                mesh = True
        
        #* Terminate program
        if cv2.waitKey(1) & 0xFF == ord('q'):
            cv2.destroyAllWindows()
            exit()