import pygame
import time
import math
from utils import scale_image, blit_rotate_center, blit_text_center, blit_text_subcenter, blit_text_abovecenter
pygame.font.init()

#Track Background:
GRASS = scale_image(pygame.image.load("images/grass.jpg"), 1.6)

TRACK = scale_image(pygame.image.load("images/my_track.png"), 0.9)
TRACK_BORDER = scale_image(pygame.image.load("images/my_track_border.png"), 0.9)
TRACK_BORDER_MASK = pygame.mask.from_surface(TRACK_BORDER)

FINISH_LINE = pygame.image.load("images/finish_line.png")
FINISH_LINE_MASK = pygame.mask.from_surface(FINISH_LINE)
FINISH_LINE_POSITION = (30, 300)
#Cars:
PLAYER_CAR = scale_image(pygame.image.load("images/convertable_car.png"), 0.75)
CPU_CAR = scale_image(pygame.image.load("images/cpu_convertable_car.png"), 0.75)



#Window: 
WIDTH, HEIGHT = TRACK.get_width(), TRACK.get_height()
WINDOW = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Racing Game!")

HEADER_FONT = pygame.font.SysFont("comicsans", 44)
SUBHEADER_FONT = pygame.font.SysFont("comicsans", 32)
BODY_FONT = pygame.font.SysFont("comicsans", 20)

#classes
class AbstractCar: 
    def __init__(self, max_velocity, rot_velocity):
        self.image = self.IMAGE
        self.max_velocity = max_velocity
        self.velocity = 0
        self.rot_velocity = rot_velocity
        self.angle = 0
        self.x, self.y = self.START_POSITION
        self.acceleration = 0.1
        self.mask = None
        self.cur_image = self.image
        self.cur_x, self.cur_y = self.x, self.y
        self.top_speed = 0

    def rotate(self, left=False, right=False): 
        if left: 
            self.angle += self.rot_velocity
        elif right: 
            self.angle -= self.rot_velocity

    def draw(self, window): 
        result = blit_rotate_center(window, self.image, (self.x, self.y), self.angle)
        self.cur_image = result[0]
        self.cur_x, self.cur_y = result[1]

    def move_forward(self): 
        self.velocity = min(self.velocity + self.acceleration, self.max_velocity)
        self.top_speed = max(self.top_speed, self.velocity)
        self.move()

    def move_backward(self): 
        self.velocity = max(self.velocity - self.acceleration, -self.max_velocity/2)
        self.move()

    def move(self): 
        radians = math.radians(self.angle)
        vertical_velocity = math.cos(radians) * self.velocity
        horizontal_velocity = math.sin(radians) * self.velocity
        self.y -= vertical_velocity
        self.x -= horizontal_velocity

    def collide(self, track_mask, x=0, y=0): 
        car_mask = pygame.mask.from_surface(self.cur_image)
        offset = (int(self.cur_x-x), int(self.cur_y-y))
        poi = track_mask.overlap(car_mask, offset)
        return poi
    
    def reset(self): 
        self.x, self.y = self.START_POSITION
        self.cur_x, self.cur_y = self.START_POSITION
        self.angle = 0
        self.velocity = 0
        self.top_speed = 0
    


class PlayerCar(AbstractCar): 
    IMAGE = PLAYER_CAR
    START_POSITION = (40, 250)
    SPEEDS = [(3, 3), (4, 4), (5, 4), (6, 4), (7,4)]
    def reset(self, level): 
        super().reset()
        self.max_velocity = self.SPEEDS[level][0]
        self.rot_velocity = self.SPEEDS[level][1]

    def reduce_speed(self): 
        if self.velocity > 0: 
            self.velocity = max(self.velocity - self.acceleration, 0)
        elif self.velocity < 0: 
            self.velocity = max(self.velocity+self.acceleration, -self.max_velocity)
        self.move()

    def bounce(self): 
        if self.velocity <= 0: 
            self.velocity = 2
        else: 
            self.velocity = -2
        self.move()

class CPUCar(AbstractCar): 
    IMAGE = CPU_CAR
    START_POSITION = (75, 250)
    SPEEDS = [(1, 2), (2, 3), (3, 6), (4, 8), (5, 10)]
    def __init__(self, max_velocity, rot_velocity, path=[]):
        super().__init__(max_velocity, rot_velocity)
        self.path = path 
        self.current_point = 0
        self.velocity = max_velocity

    def reset(self, level):
        super().reset()
        self.current_point = 0
        self.velocity = self.SPEEDS[level-1][0]
        self.rot_velocity = self.SPEEDS[level-1][1]

    def draw_points(self, window): 
        for point in self.path: 
            pygame.draw.circle(window, (255, 0, 0), point, 5)
    
    def draw(self, window): 
        super().draw(window)
        self.draw_points(window)

    def calculate_angle(self): 
        target_x, target_y = self.path[self.current_point]
        x_diff = target_x - self.x
        y_diff = target_y - self.y

        if y_diff == 0:
            desired_radian_angle = math.pi/2
        else: 
            desired_radian_angle = math.atan(x_diff/y_diff)

        if target_y > self.y: 
            desired_radian_angle += math.pi


        copy_self_angle = self.angle % 360
        copy_target_angle = math.degrees(desired_radian_angle)
        
        #Angles now positive
        copy_self_angle = (copy_self_angle + 360) % 360
        copy_target_angle = (copy_target_angle + 360) % 360
        angle_delta = ((copy_self_angle-copy_target_angle)%180)

        if copy_self_angle >= 180:
            if copy_target_angle > copy_self_angle or copy_target_angle < ((copy_self_angle + 180)%360): 
                self.angle += min(self.rot_velocity, angle_delta)
            else: 
                self.angle -= min(self.rot_velocity, angle_delta)
        else: 
            if copy_self_angle < copy_target_angle < ((copy_self_angle + 180)%360): 
                self.angle += min(self.rot_velocity, angle_delta)
            else: 
                self.angle -= min(self.rot_velocity, angle_delta)

    def update_path_point(self): 
        target = self.path[self.current_point]
        rect = pygame.Rect(self.x, self.y, self.image.get_width(), self.image.get_height())
        if rect.collidepoint(*target): 
            self.current_point += 1

    def move(self): 
        if self.current_point >= len(self.path): 
            return
        
        self.calculate_angle()
        self.update_path_point()
        super().move()

    def next_level(self, level): 
        self.reset(level)
        
#Clock: 
clock = pygame.time.Clock()
FPS = 60

class GameInfo: 
    LEVELS = 5

    def __init__(self, level=1):
        self.level = level
        self.started = False
        self.level_start_time = 0

    def next_level(self): 
        self.level += 1
        self.started = False

    def reset(self): 
        self.started = False
        self.level_start_time = 0
    
    def game_finished(self): 
        return self.level > self.LEVELS
    
    def start_level(self): 
        self.started = True
        self.level_start_time = time.time()

    def get_level_time(self): 
        if not self.started: 
            return 0
        else: 
            return round(time.time() - self.level_start_time)


player_car = PlayerCar(4, 4)
cpu_car = CPUCar(1, 2, [(70, 226), (52, 174), (46, 148), (52, 112), (88, 70), (172, 92), (180, 172), (196, 224), (228, 230), (284, 230), (284, 140), (288, 90), (350, 62), (412, 106), (464, 148), (526, 208), (552, 266), (566, 334), (566, 426), 
                        (568, 476), (550, 614), (510, 686), (468, 718), (415, 778), (254, 818), (174, 806), (122, 808), (62, 754), (112, 668), (284, 654), (390, 632), (442, 546), (456, 470), (465, 416), (432, 362), (378, 348), (306, 346), (202, 342), (230, 446), (280, 448), (320, 448), (335, 520), (170, 546), (78, 514), (74, 426), (74, 336), (70, 278)])
bg_images = [(GRASS, (0, 0)), (TRACK, (0, 0)), (FINISH_LINE, FINISH_LINE_POSITION)]

def move_player(player_car, time_since_bounce=0): 
    keys = pygame.key.get_pressed()
    moved = False
    if time_since_bounce > 500:
        if keys[pygame.K_LEFT] and player_car.velocity >0: 
            player_car.rotate(left=True)
        if keys[pygame.K_RIGHT] and player_car.velocity >0: 
            player_car.rotate(right=True)
        if keys[pygame.K_UP] and player_car.collide(TRACK_BORDER_MASK) == None: 
            moved = True
            player_car.move_forward()
        if keys[pygame.K_DOWN]: 
            moved = True
            player_car.move_backward()
        if keys[pygame.K_r]: 
            game_info.reset()
            player_car.reset(game_info.level)
            cpu_car.reset(game_info.level)

    if not moved: 
        player_car.reduce_speed()

def draw(window, images, player_car, cpu_car, game_info): 
    for image, position in images:
        window.blit(image, position)

    level_text = BODY_FONT.render(f"Level {game_info.level}", 1, (0, 0, 0))
    window.blit(level_text, (window.get_width()-window.get_width()/4.7, window.get_height() - level_text.get_height()-70))

    time_text = BODY_FONT.render(f"Time: {game_info.get_level_time()}s", 1, (0, 0, 0))
    window.blit(time_text, (window.get_width()-window.get_width()/4.7, window.get_height() - time_text.get_height()-40))

    velocity_text = BODY_FONT.render(f"Speed: {round(player_car.velocity, 1)}px/s", 1, (0, 0, 0))
    window.blit(velocity_text, (window.get_width()-window.get_width()/4.7, window.get_height() - velocity_text.get_height()-10))

    player_car.draw(window)
    cpu_car.draw(window)
    pygame.display.update()


#Event Loop:
game_info = GameInfo()
cpu_speeds_index = 1
CPU_SPEEDS = [(2, 3), (3, 6), (4, 8), (5, 10)]
time_since_bounce = 0
run = True
while run:
    dt = clock.tick(FPS) 

    draw(WINDOW, bg_images, player_car, cpu_car, game_info)

    while not game_info.started: 
        blit_text_center(WINDOW, HEADER_FONT, f"Press SPACE to start level {game_info.level}!")
        pygame.display.update()
        for event in pygame.event.get(): 
            if event.type == pygame.QUIT: 
                pygame.quit()
                break

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE: 
                    game_info.start_level()
    


    for event in pygame.event.get(): 
        if event.type == pygame.QUIT: 
            run = False
            break
             
    move_player(player_car, time_since_bounce)
    cpu_car.move()

    time_since_bounce += dt
    if time_since_bounce > 500:
        if player_car.collide(TRACK_BORDER_MASK) != None: 
            player_car.bounce()
            time_since_bounce = 0
        player_finish_line_poi_collide = player_car.collide(FINISH_LINE_MASK, *FINISH_LINE_POSITION)
        if player_finish_line_poi_collide != None:
            if player_finish_line_poi_collide[1] == 0: 
                player_car.bounce()
                time_since_bounce = 0
            else: 
                blit_text_center(WINDOW, HEADER_FONT, "You Won!")
                blit_text_abovecenter(WINDOW, SUBHEADER_FONT, f"LapTime: {game_info.get_level_time()}s")
                blit_text_subcenter(WINDOW, SUBHEADER_FONT, f"TopSpeed: {player_car.top_speed}px/s")
                pygame.display.update()
                stay_on_screen = True
                while stay_on_screen: 
                    for event in pygame.event.get(): 
                        if event.type == pygame.QUIT: 
                            pygame.quit()
                            break
                        if event.type == pygame.KEYDOWN: 
                            if event.key == pygame.K_SPACE:
                                stay_on_screen = False
                game_info.next_level()
                player_car.reset(game_info.level)
                cpu_car.reset(game_info.level)
    elif time_since_bounce>250: 
        if player_car.collide(TRACK_BORDER_MASK) != None: 
            player_car.velocity = 0

    cpu_finish_line_poi_collide = cpu_car.collide(FINISH_LINE_MASK, *FINISH_LINE_POSITION)
    if cpu_finish_line_poi_collide != None: 
        blit_text_center(WINDOW, HEADER_FONT, "You Lost.")
        pygame.display.update()
        pygame.time.wait(2500)
        game_info.reset()
        player_car.reset(game_info.level)
        cpu_car.reset(game_info.level)
    if game_info.game_finished(): 
        blit_text_center(WINDOW, HEADER_FONT, "You Won!")
        blit_text_abovecenter(WINDOW, SUBHEADER_FONT, f"LapTime: {game_info.get_level_time()}s")
        blit_text_subcenter(WINDOW, SUBHEADER_FONT, f"TopSpeed: {player_car.top_speed}px/s")
        pygame.display.update()
        stay_on_screen = True
        while stay_on_screen: 
            for event in pygame.event.get(): 
                if event.type == pygame.QUIT: 
                    pygame.quit()
                    break
                if event.type == pygame.KEYDOWN: 
                    if event.key == pygame.K_SPACE:
                        pygame.quit()
                    if event.key == pygame.K_r: 
                        game_info.level = 1
                        game_info.reset()
                        player_car.reset(game_info.level)
                        cpu_car.reset(game_info.level)
        
    

print(cpu_car.path)
pygame.quit()

