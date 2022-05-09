import neat
import pygame
import time
import math
import os.path
from utils import scale_image, blit_rotate_center, blit_text_center, blit_text_subcenter, blit_text_abovecenter
import pickle
pygame.font.init()


'''Track Background Images'''
GRASS = scale_image(pygame.image.load("images/grass.jpg"), 1.7)
TRACK = pygame.image.load("images/my_track.png")
TRACK_BORDER = pygame.image.load("images/my_track_border.png")

FINISH_LINE = pygame.image.load("images/finish_line.png")
FINISH_LINE_POSITION = (37, 300)
bg_images = [(GRASS, (0, 0)), (TRACK, (0, 0)), (FINISH_LINE, FINISH_LINE_POSITION)]


'''Masks for Pixel Perfect Collisions'''
FINISH_LINE_MASK = pygame.mask.from_surface(FINISH_LINE)
TRACK_BORDER_MASK = pygame.mask.from_surface(TRACK_BORDER)


'''Cars Images'''
PLAYER_CAR = scale_image(pygame.image.load("images/convertable_car.png"), 0.75)
CPU_CAR = scale_image(pygame.image.load("images/cpu_convertable_car.png"), 0.75)


'''Window''' 
WIDTH, HEIGHT = TRACK.get_width(), TRACK.get_height()
WINDOW = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Racing Game!")


'''Font'''
HEADER_FONT = pygame.font.SysFont("comicsans", 44)
SUBHEADER_FONT = pygame.font.SysFont("comicsans", 32)
BODY_FONT = pygame.font.SysFont("comicsans", 20)


'''Classes'''
class AbstractCar: 
    def __init__(self, max_velocity, rot_velocity):
        self.image = self.IMAGE
        self.cur_image = self.image
        self.mask = None
        self.max_velocity = max_velocity
        self.rot_velocity = rot_velocity
        self.velocity = 3
        self.acceleration = 0.2
        self.angle = 0
        self.x, self.y = self.START_POSITION
        self.cur_x, self.cur_y = self.x, self.y
        self.prev_x, self.prev_y = 0, 0
        self.time_since_update = 0
        self.laptime = 0

    def rotate(self, left=False, right=False): 
        if left: 
            self.angle += self.rot_velocity/2
        elif right: 
            self.angle -= self.rot_velocity

    def draw(self, window): 
        result = blit_rotate_center(window, self.image, (self.x, self.y), self.angle)
        self.cur_image = result[0]
        self.cur_x, self.cur_y = result[1]
        
    def move_forward(self): 
        self.velocity = min(self.velocity + self.acceleration/2, self.max_velocity)
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
        self.laptime = 0
        self.time_since_update = 0
    
    def calculate_angle(self, checkpoint): 
        target_x, target_y = checkpoint
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
        return angle_delta

    def radar_foreward(self, angle, window): 
        length = 0
        x = int(self.x)
        y = int(self.y)
        angle = (angle+360)%360

        while length < 200 and not TRACK_BORDER.get_at((round(x), round(y)))[3] != 0:  
            length += 1
            x = x - math.sin(math.radians(self.angle))
            y = y - math.cos(math.radians(self.angle))
        
        pygame.draw.line(window, (0, 0, 0), (self.x, self.y), (round(x), round(y)), 1)
        pygame.draw.circle(window, (0, 255, 0), (x, y), 3)
        pygame.display.update()
        return length

    def radar_right(self, angle, window): 
        length = 0
        x = int(self.x)
        y = int(self.y)
        angle = (angle+360)%360

        while length < 200 and not TRACK_BORDER.get_at((round(x), round(y)))[3] != 0:  
            length += 1
            x = x - math.sin(math.radians(self.angle-90))
            y = y - math.cos(math.radians(self.angle-90))
        
        pygame.draw.line(window, (0, 0, 0), (self.x, self.y), (round(x), round(y)), 1)
        pygame.draw.circle(window, (0, 255, 0), (x, y), 3)
        pygame.display.update()
        return length

    def radar_left(self, angle, window): 
        length = 0
        x = int(self.x)
        y = int(self.y)
        angle = (angle+360)%360

        while length < 200 and not TRACK_BORDER.get_at((round(x), round(y)))[3] != 0: 
            length += 1
            x = x - math.sin(math.radians(self.angle+90))
            y = y - math.cos(math.radians(self.angle+90))
        
        pygame.draw.line(window, (0, 0, 0), (self.x, self.y), (round(x), round(y)), 1)
        pygame.draw.circle(window, (0, 255, 0), (x, y), 3)
        pygame.display.update()
        return length
    
    def radar_forwardleft(self, angle, window): 
        length = 0
        x = int(self.x)
        y = int(self.y)
        angle = (angle+360)%360

        while length < 200 and not TRACK_BORDER.get_at((round(x), round(y)))[3] != 0: 
            length += 1
            x = x - math.sin(math.radians(self.angle+45))
            y = y - math.cos(math.radians(self.angle+45))
        
        pygame.draw.line(window, (0, 0, 0), (self.x, self.y), (round(x), round(y)), 1)
        pygame.draw.circle(window, (0, 255, 0), (x, y), 3)
        pygame.display.update()
        return length

    def radar_forwardright(self, angle, window): 
        length = 0
        x = int(self.x)
        y = int(self.y)
        angle = (angle+360)%360

        while length < 200 and not TRACK_BORDER.get_at((round(x), round(y)))[3] != 0: 
            length += 1
            x = x - math.sin(math.radians(self.angle-45))
            y = y - math.cos(math.radians(self.angle-45))
        
        pygame.draw.line(window, (0, 0, 0), (self.x, self.y), (round(x), round(y)), 1)
        pygame.draw.circle(window, (0, 255, 0), (x, y), 3)
        pygame.display.update()
        return length

class PlayerCar(AbstractCar): 
    IMAGE = PLAYER_CAR
    START_POSITION = (75, 250)
    SPEEDS = [(3, 3), (4, 4), (5, 4), (6, 4), (7,4)]
    def reset(self, level): 
        super().reset()
        self.max_velocity = self.SPEEDS[level][0]
        self.rot_velocity = self.SPEEDS[level][1]

    def reduce_speed(self): 
        self.velocity = max(self.velocity - self.acceleration, 0)
        if self.velocity < 0: 
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
    START_POSITION = (65, 250)
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

    # def calculate_angle(self): 
    #     target_x, target_y = self.path[self.current_point]
    #     x_diff = target_x - self.x
    #     y_diff = target_y - self.y

    #     if y_diff == 0:
    #         desired_radian_angle = math.pi/2
    #     else: 
    #         desired_radian_angle = math.atan(x_diff/y_diff)

    #     if target_y > self.y: 
    #         desired_radian_angle += math.pi


    #     copy_self_angle = self.angle % 360
    #     copy_target_angle = math.degrees(desired_radian_angle)
        
    #     #Angles now positive
    #     copy_self_angle = (copy_self_angle + 360) % 360
    #     copy_target_angle = (copy_target_angle + 360) % 360
    #     angle_delta = ((copy_self_angle-copy_target_angle)%180)

    #     if copy_self_angle >= 180:
    #         if copy_target_angle > copy_self_angle or copy_target_angle < ((copy_self_angle + 180)%360): 
    #             self.angle += min(self.rot_velocity, angle_delta)
    #         else: 
    #             self.angle -= min(self.rot_velocity, angle_delta)
    #     else: 
    #         if copy_self_angle < copy_target_angle < ((copy_self_angle + 180)%360): 
    #             self.angle += min(self.rot_velocity, angle_delta)
    #         else: 
    #             self.angle -= min(self.rot_velocity, angle_delta)

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
        
class GameInfo: 
    LEVELS = 5

    def __init__(self, level=1):
        self.level = level
        self.started = True
        self.level_start_time = 0

    def next_level(self): 
        self.level += 1
        self.started = True

    def reset(self): 
        self.started = True
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


'''Functions'''
def draw(window, images, ai_cars, game_info, player_car=None, ): 
    for image, position in images:
        window.blit(image, position)

    if player_car is not None: 
        player_car.draw(window)
        velocity_text = BODY_FONT.render(f"Speed: {round(player_car.velocity, 1)}px/s", 1, (0, 0, 0))
        window.blit(velocity_text, (window.get_width()-window.get_width()/4.7, window.get_height() - velocity_text.get_height()-10))
    
    for ai_car in ai_cars:
        ai_car.draw(window)
    pygame.display.update()


'''Main Game Function'''
def run_genomes(genomes, config):
    '''Import Globals'''
    global generation, max_fitness, max_checkpoint, checkpoints
    
    '''NEAT Requirements'''
    nets = []
    ge = []
    ai_cars = []
    
    '''Fill in NEAT Requirements'''
    for _,g in genomes: 
        net = neat.nn.FeedForwardNetwork.create(g, config)
        nets.append(net)
        ai_cars.append(PlayerCar(3, 6))
        g.fitness = 0
        ge.append(g)

    '''Game Details'''
    game_info = GameInfo()
    clock = pygame.time.Clock()
    FPS = 60
    run = True

    '''Main Game / Event Loop'''
    while run:
        '''Game Clock'''
        #Makes sure clock is consistent. Ticks FPS times per second
        clock.tick(FPS) 

        '''Update Screen'''
        #draw all background images and update window to reflect all changes
        draw(WINDOW, bg_images, ai_cars, game_info)
        pygame.display.update()

        '''Pygame Commands'''
        for event in pygame.event.get(): 
            #if you close game window the game will quit
            if event.type == pygame.QUIT: 
                run = False
                pygame.quit()
                quit()
            #print (x, y) coordinate of mouse position in window. Useful for debugging.
            if event.type == pygame.KEYDOWN: 
                if event.key == pygame.K_l:
                    x, y = pygame.mouse.get_pos()
                    print(x, y)             


        '''Loop Controlling AI'''
        #iterating backwards because we will be popping cars out of the list
        #need to ensure we don't skip looking over any car each tick
        i = len(ai_cars)-1
        while i >= 0: 
            ai_car = ai_cars[i]
            
            #incriment laptime. Happens once per car per tick and 60 times per second. 
            ai_car.laptime += 1
            
            '''Car Default Movement'''
            #Car is always moving forward and turning left, AI only controls when to turn right. 
            ai_car.move_forward()
            ai_car.rotate(left=True)
            
            '''Distance Radars'''
            #Send out 5 radars so the car knows distance from itself to walls
            distance_forward = ai_car.radar_foreward(ai_car.angle, WINDOW)
            distance_right = ai_car.radar_right(ai_car.angle, WINDOW)
            distance_left = ai_car.radar_left(ai_car.angle, WINDOW)
            distance_forwardleft = ai_car.radar_forwardleft(ai_car.angle, WINDOW)
            distance_forwardright = ai_car.radar_forwardright(ai_car.angle, WINDOW)
            
            '''NEAT Controls & Fitness'''
            
            '''NEAT Give Fitness'''
            #Give fitness for each tick the car remains alive. 
            #Important until the cars solve the track, then it is overwritten by laptime
            ge[i].fitness += 0.01

            '''NEAT Inputs (What information NEAT will have to make decisions)'''
            #Passing in 5 distance rays and the cars angle
            output = nets[i].activate((distance_forward, distance_left, distance_right, distance_forwardleft, distance_forwardright, (ai_car.angle+360)%360))
            
            '''NEAT Outputs aka AI controling car options'''
            if output[0] > 0: 
                ai_car.rotate(right=True)
            # if output[1] < 0: 
            #     ai_car.rotate(left=True)
            # if output[2] > 0: 
            #     ai_car.reduce_speed()

            '''Check if Car Should be Removed'''
            player_finish_line_poi_collide = ai_car.collide(FINISH_LINE_MASK, *FINISH_LINE_POSITION)
            
            #If hit Finish Line
            if player_finish_line_poi_collide != None:
                #if from the correct side
                if player_finish_line_poi_collide[1] != 0:  
                    #Dividing by 60 because 60 ticks per second. Dividing by 60 gives laptime in seconds.
                    print(f"Laptime: {ai_car.laptime/60}s")
                    #Overwrite previous fitness with obviously greater fitness. 
                    #Choosing a number much larger than laptime then subtracting laptime 
                    # because we want the smallest laptime to have the highest fitness.
                    ge[i].fitness = 50000 - ai_car.laptime 
                ai_car.checkpoint = 0
                ai_car.time_checkpoint = 0
                ai_car.time_since_update = 0
                ai_cars.pop(i)
                nets.pop(i)
                ge.pop(i)
                i -= 1
            #If Hit Wall
            elif ai_car.collide(TRACK_BORDER_MASK) != None: 
                ai_car.checkpoint = 0
                ai_car.time_checkpoint = 0
                ai_car.time_since_update = 0
                ai_cars.pop(i)
                nets.pop(i)
                ge.pop(i)
                i -= 1
            #If Car is staying/spinning in place
            elif ai_car.time_since_update > 30:
                if abs(ai_car.prev_x - ai_car.x) < 40 and abs(ai_car.prev_y - ai_car.y) < 40: 
                    
                    ai_car.checkpoint = 0
                    ai_car.time_checkpoint = 0
                    ai_car.time_since_update = 0
                    ai_cars.pop(i)
                    nets.pop(i)
                    ge.pop(i)
                    i -= 1
            else: 
                i -= 1

        '''Next generation if no cars left'''
        if len(ai_cars) == 0: 
            run = False
            break           



'''NEAT Setup'''
def run(config_path): 
    #Configuration for the simulation. Settings adjusted in the config file
    config = neat.config.Config(neat.DefaultGenome, neat.DefaultReproduction, neat.DefaultSpeciesSet, neat.DefaultStagnation, config_path)
    
    #Create Population
    p = neat.Population(config)
   
    #Add reporter for printing valuable generation data during sim. 
    p.add_reporter(neat.StdOutReporter(True))
    stats = neat.StatisticsReporter()
    p.add_reporter(stats)
    
    #Call to run the function (game function, # of generations to run)
    winner = p.run(run_genomes,20)

    #Save winner to winner.pkl file in game directory to be able to use later
    with open("winner.pkl", "wb") as f:
        pickle.dump(winner, f)
        f.close()

# '''Replay Genome'''
# '''Not Working'''
# def replay_genome(config_path, genome_path="winner.pkl"):
#     # Load requried NEAT config
#     config = neat.config.Config(neat.DefaultGenome, neat.DefaultReproduction, neat.DefaultSpeciesSet, neat.DefaultStagnation, config_path)

#     # Unpickle saved winner
#     with open(genome_path, "rb") as f:
#         genome = pickle.load(f)

#     # Convert loaded genome into required data structure
#     genomes = [(1, genome)]

#     # Call game with only the loaded genome
#     main(genomes, config)

if __name__ == "__main__": 
    local_dir = os.path.dirname(__file__)
    config_path = os.path.join(local_dir, "feed_forward_config.txt")
    run(config_path) 
    # replay_genome(config_path)