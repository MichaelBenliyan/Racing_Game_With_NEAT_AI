import neat
import pygame
import time
import math
import os.path
from utils import scale_image, blit_rotate_center, blit_text_center, blit_text_subcenter, blit_text_abovecenter
import pickle
pygame.font.init()


'''Track Background Images'''
GRASS = scale_image(pygame.image.load("images/grass.jpg"), 1.8)
TRACK = pygame.image.load("images/my_track.png")
TRACK_BORDER = pygame.image.load("images/my_track_border.png")

FINISH_LINE = pygame.image.load("images/finish_line.png")
FINISH_LINE_POSITION = (37, 300)
bg_images = [(GRASS, (0, 0)), (TRACK, (0, 0)), (FINISH_LINE, FINISH_LINE_POSITION)]


'''Masks for Pixel Perfect Collisions'''
FINISH_LINE_MASK = pygame.mask.from_surface(FINISH_LINE)
TRACK_BORDER_MASK = pygame.mask.from_surface(TRACK_BORDER)


'''Interactive Windows'''
MAIN_MENU = pygame.image.load("images/main_menu.png")
WIN_SCREEN = pygame.image.load("images/win_screen.png")
LOSE_SCREEN = pygame.image.load("images/lose_screen.png")
END_SCREEN = pygame.image.load("images/end_screen.png")


'''Countdown Graphics'''
COUNTDOWN_3 = pygame.image.load("images/countdown_3.png")
COUNTDOWN_2 = pygame.image.load("images/countdown_2.png")
COUNTDOWN_1 = pygame.image.load("images/countdown_1.png")
COUNTDOWN_GO = pygame.image.load("images/countdown_go.png")


'''Cars Images'''
PLAYER_CAR = scale_image(pygame.image.load("images/convertable_car.png"), 0.75)
AI_CAR = scale_image(pygame.image.load("images/cpu_convertable_car.png"), 0.75)


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
    def __init__(self, difficulty, level):
        self.image = self.IMAGE
        self.cur_image = self.image
        self.mask = None
        self.velocity = 0
        self.angle = 0
        self.x, self.y = self.START_POSITION
        self.cur_x, self.cur_y = self.x, self.y
        self.prev_x, self.prev_y = 0, 0
        self.time_since_bounce = 0
        self.laptime = 0

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
    
    def reset(self, difficulty, level): 
        self.x, self.y = self.START_POSITION
        self.cur_x, self.cur_y = self.START_POSITION
        self.angle = 0
        self.velocity = 0
        self.laptime = 0
        self.time_since_bounce = 0
        self.max_velocity = self.SPEEDS[difficulty][level][0]
        self.rot_velocity = self.SPEEDS[difficulty][level][1]
        self.acceleration = self.max_velocity/30
    
class PlayerCar(AbstractCar):   
    def __init__(self, difficulty, level):
        self.IMAGE = PLAYER_CAR
        self.START_POSITION = (75, 250)
        self.SPEEDS = {
            'easy': [(1.5, 3), (2, 5), (2.5, 6), (3, 6), (3.5, 7)], 
            'medium': [(2, 5), (2.5, 6), (3, 6), (3.5, 7), (4, 10)],
            'hard': [(2.5, 6), (3, 6), (3.5, 7), (4, 10), (4.5, 10)]
            }
        self.max_velocity = self.SPEEDS[difficulty][level][0]
        self.rot_velocity = self.SPEEDS[difficulty][level][1]
        self.acceleration = self.max_velocity/30
        super().__init__(difficulty, level)

    def rotate(self, left=False, right=False): 
        if left: 
            self.angle += self.rot_velocity
        elif right: 
            self.angle -= self.rot_velocity

    def reduce_speed(self): 
        if self.velocity < 0: 
            self.velocity = max(self.velocity+self.acceleration*2, -self.max_velocity)
        else: 
            self.velocity = max(self.velocity - self.acceleration/2, 0)
        self.move()

    def bounce(self): 
        if self.velocity <= 0: 
            self.velocity = 3
        else: 
            self.velocity = -3
        self.move()

class AICar(AbstractCar): 
    def __init__(self, difficulty, level):
        self.IMAGE = AI_CAR
        self.START_POSITION = (85, 250)
        self.SPEEDS = {
            'easy': [(1, 3), (1.5, 4), (2, 5), (2.5, 6), (3, 6)], 
            'medium': [(1.65, 4), (2.15, 5), (2.65, 6), (3.15, 6), (3.65, 8)],
            'hard': [(2.3, 5.5), (2.8, 6), (3.3, 6), (3.8, 8), (4.3, 10)]
            }
        self.max_velocity = self.SPEEDS[difficulty][level][0]
        self.rot_velocity = self.SPEEDS[difficulty][level][1]
        self.acceleration = self.max_velocity/30
        super().__init__(difficulty, level)
        
    def reduce_speed(self): 
        self.velocity = max(self.velocity - self.acceleration, 0)
        if self.velocity < 0: 
            self.velocity = max(self.velocity+self.acceleration, -self.max_velocity)
        self.move()

    def rotate(self, left=False, right=False): 
        if left: 
            self.angle += self.rot_velocity/2
        elif right: 
            self.angle -= self.rot_velocity
    
    def radar(self, radar_angle): 
        length = 0
        x = int(self.x)
        y = int(self.y)
        #Keep moving in the radar_angle direction until hitting a nontrasparent pixel in the Track Border
        while length < 200 and not TRACK_BORDER.get_at((round(x), round(y)))[3] != 0:  
            length += 1
            x = x - math.sin(math.radians(self.angle+radar_angle))
            y = y - math.cos(math.radians(self.angle+radar_angle))
        
        '''Show Radars'''
        pygame.draw.line(WINDOW, (0, 0, 0), (self.x, self.y), (round(x), round(y)), 1)
        pygame.draw.circle(WINDOW, (0, 255, 0), (x, y), 3)
        pygame.display.update()
        return length
        
class GameInfo: 
    def __init__(self, difficulty):
        self.levels = 4
        self.level = 0
        self.difficulty = difficulty

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


'''Helper Functions'''
def draw(window, images, ai_car, player_car=None, ): 
    for image, position in images:
        window.blit(image, position)

    if player_car is not None: 
        player_car.draw(window)
        velocity_text = BODY_FONT.render(f"Speed: {round(player_car.velocity*20, 1)}mph", 1, (0, 0, 0))
        window.blit(velocity_text, (window.get_width()-window.get_width()/4.7, window.get_height() - velocity_text.get_height()-10))
    
    ai_car.draw(window)
    pygame.display.update()

def move_player(player_car): 
    keys = pygame.key.get_pressed()
    moved = False
    '''User Controls of Car'''
    if player_car.time_since_bounce > 10:
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
    '''Reduce Car Speed Gradually if not accelerating'''
    if not moved: 
        player_car.reduce_speed()


'''Main Game Functions'''
def run_main_menu(genomes, config): 
    WINDOW.blit(GRASS, (0,0))
    WINDOW.blit(TRACK, (0,0))
    WINDOW.blit(FINISH_LINE, (FINISH_LINE_POSITION))
    WINDOW.blit(MAIN_MENU, (WIDTH/2-WIDTH/4, HEIGHT/2-HEIGHT/6)) 
    pygame.display.update()
    pygame.time.wait(500)
    main_menu=True
    while main_menu: 
        for event in pygame.event.get(): 
            if event.type == pygame.QUIT: 
                main_menu = False
                pygame.quit()
                quit()
            elif event.type == pygame.KEYDOWN: 
                if event.key == pygame.K_a: 
                    print(pygame.mouse.get_pos())
                    run_end_screen(genomes, config)

        '''Menu Options'''
        mouse = pygame.mouse.get_pos()
        if pygame.mouse.get_pressed()[0]:  
            if 196 <= mouse[0] <= 279 and 449<= mouse[1] <=483:  
                '''Easy'''
                difficulty = 'easy'
                run_setup(genomes, config, difficulty)
                pygame.quit()
                quit()
            elif 312 <= mouse[0] <= 396 and 449<= mouse[1] <=483:
                '''Medium'''
                difficulty = 'medium'
                run_setup(genomes, config, difficulty)
                pygame.quit()
                quit()
            elif 426 <= mouse[0] <= 510 and 449<= mouse[1] <=483:
                '''Hard'''
                difficulty = 'hard'
                run_setup(genomes, config, difficulty)
                pygame.quit()
                quit()

def run_setup(genomes, config, difficulty): 
    '''Game Details'''
    game_info = GameInfo(difficulty)
    
    '''Setup Player Car'''
    player_car = (PlayerCar(game_info.difficulty, game_info.level)) 

    '''Setup AI Car'''
    net = neat.nn.FeedForwardNetwork.create(genomes[0][1], config)
    ai_car = (AICar(difficulty, game_info.level))

    run_countdown(genomes, config, game_info, player_car, ai_car, net)

def run_countdown(genomes, config, game_info, player_car, ai_car, net): 
    for event in pygame.event.get(): 
        if event.type == pygame.QUIT: 
            pygame.quit()
            quit()
        elif event.type == pygame.KEYDOWN: 
            if event.key == pygame.K_a: 
                print(pygame.mouse.get_pos())

    WINDOW.blit(GRASS, (0,0))
    WINDOW.blit(TRACK, (0,0))
    WINDOW.blit(FINISH_LINE, (FINISH_LINE_POSITION))
    WINDOW.blit(COUNTDOWN_3, (WIDTH/2-WIDTH/4, HEIGHT/2-HEIGHT/6)) 
    pygame.display.update()
    pygame.time.wait(1000)
    WINDOW.blit(GRASS, (0,0))
    WINDOW.blit(TRACK, (0,0))
    WINDOW.blit(FINISH_LINE, (FINISH_LINE_POSITION))
    WINDOW.blit(COUNTDOWN_2, (WIDTH/2-WIDTH/4, HEIGHT/2-HEIGHT/6))
    pygame.display.update()
    pygame.time.wait(1000)
    WINDOW.blit(GRASS, (0,0))
    WINDOW.blit(TRACK, (0,0))
    WINDOW.blit(FINISH_LINE, (FINISH_LINE_POSITION))
    WINDOW.blit(COUNTDOWN_1, (WIDTH/2-WIDTH/4, HEIGHT/2-HEIGHT/6))
    pygame.display.update()
    pygame.time.wait(1000)
    WINDOW.blit(GRASS, (0,0))
    WINDOW.blit(TRACK, (0,0))
    WINDOW.blit(FINISH_LINE, (FINISH_LINE_POSITION))
    WINDOW.blit(COUNTDOWN_GO, (WIDTH/2-WIDTH/4, HEIGHT/2-HEIGHT/6)) 
    pygame.display.update()
    pygame.time.wait(200)
    run_game(genomes, config, game_info, player_car, ai_car, net)

def run_game(genomes, config, game_info, player_car, ai_car, net):
    '''Game Clock'''
    clock = pygame.time.Clock()
    FPS = 60

    '''Game Loop'''
    game = True
    while game: 
        #Makes sure clock is consistent. Ticks FPS times per second
        clock.tick(FPS) 

        '''Update Screen'''
        #draw all background images and update window to reflect all changes
        draw(WINDOW, bg_images, ai_car, player_car=player_car)
        pygame.display.update()

        '''Pygame Commands'''
        for event in pygame.event.get(): 
            #if you close game window the game will quit
            if event.type == pygame.QUIT: 
                game = False
                pygame.quit()
                quit()
            #print (x, y) coordinate of mouse position in window. Useful for debugging.
            if event.type == pygame.KEYDOWN: 
                if event.key == pygame.K_a:
                    x, y = pygame.mouse.get_pos()
                    print(x, y)             

        '''Inriment Laptimes'''           
        #incriment laptime. Happens once per car per tick and 60 times per second. 
        ai_car.laptime += 1
        player_car.laptime += 1
        player_car.time_since_bounce += 1
            
        '''AI and Player Movement'''
        #Car is always moving forward and turning left, AI only controls when to turn right. 
        ai_car.move_forward()
        ai_car.rotate(left=True)
        move_player(player_car)
        
        '''Distance Radars for AI'''
        #Send out 5 radars so the AI knows distance from itself to walls
        radar_angles = [0, -90, 90, 45, -45]
        radars = [0, 0, 0, 0, 0]
        for i, radar_angle in enumerate(radar_angles): 
            radars[i] = ai_car.radar(radar_angle)

        '''NEAT Inputs (What information NEAT will have to make decisions)'''
        #Passing in 5 distance rays and the cars angle
        output = net.activate((radars[0], radars[1], radars[2], radars[3], radars[4], (ai_car.angle+360)%360))

        '''NEAT Outputs aka AI controling car options'''
        if output[0] > 0: 
            ai_car.rotate(right=True)

        '''Check Collisions'''
        ai_finish_line_poi_collide = ai_car.collide(FINISH_LINE_MASK, *FINISH_LINE_POSITION)
        player_finish_line_poi_collide = player_car.collide(FINISH_LINE_MASK, *FINISH_LINE_POSITION)
        
        '''AI Collide w/ Finish Line'''
        if ai_finish_line_poi_collide != None:
            #if from the correct side
            if ai_finish_line_poi_collide[1] != 0:  
                print("You Lost")
                run_lose_screen(genomes, config, game_info, player_car, ai_car, net)
                game = False
                break

        '''If Player hit a Wall or hit Finish Line'''
        if player_car.time_since_bounce > 10:
            if player_car.collide(TRACK_BORDER_MASK) != None: 
                player_car.bounce()
                player_car.time_since_bounce = 0
            if player_finish_line_poi_collide != None:
                if player_finish_line_poi_collide[1] == 0: 
                    player_car.bounce()
                    player_car.time_since_bounce = 0
                else: 
                    run_win_screen(genomes, config, game_info, player_car, ai_car, net)

def run_lose_screen(genomes, config, game_info, player_car, ai_car, net): 
    WINDOW.blit(GRASS, (0,0))
    WINDOW.blit(TRACK, (0,0))
    WINDOW.blit(FINISH_LINE, (FINISH_LINE_POSITION))
    WINDOW.blit(LOSE_SCREEN, (WIDTH/2-WIDTH/4, HEIGHT/2-HEIGHT/6)) 
    pygame.display.update()
    lose_screen = True
    while lose_screen: 
        for event in pygame.event.get(): 
            if event.type == pygame.QUIT: 
                lose_screen = False
                pygame.quit()
                quit()
            elif event.type == pygame.KEYDOWN: 
                if event.key == pygame.K_a: 
                    print(pygame.mouse.get_pos())
        '''Lose Screen Options'''
        mouse = pygame.mouse.get_pos()
        if pygame.mouse.get_pressed()[0]:  
            if 228 <= mouse[0] <= 312 and 449<= mouse[1] <=483:
                '''Repeat Level'''  
                player_car.reset(game_info.difficulty, game_info.level)
                ai_car.reset(game_info.difficulty, game_info.level)
                run_countdown(genomes, config, game_info, player_car, ai_car, net)
                lose_screen = False
                break
            elif 394 <= mouse[0] <= 478 and 449<= mouse[1] <=483:
                '''Main Menu'''
                run_main_menu(genomes, config)
                lose_screen = False
                break

def run_win_screen(genomes, config, game_info, player_car, ai_car, net):
    WINDOW.blit(GRASS, (0,0))
    WINDOW.blit(TRACK, (0,0))
    WINDOW.blit(FINISH_LINE, (FINISH_LINE_POSITION))
    WINDOW.blit(WIN_SCREEN, (WIDTH/2-WIDTH/4, HEIGHT/2-HEIGHT/6)) 
    pygame.display.update()
    win_screen = True
    while win_screen: 
        for event in pygame.event.get(): 
            if event.type == pygame.QUIT: 
                win_screen = False
                pygame.quit()
                quit()
            elif event.type == pygame.KEYDOWN: 
                if event.key == pygame.K_a: 
                    print(pygame.mouse.get_pos())
        '''Win Screen Options'''
        mouse = pygame.mouse.get_pos()
        if pygame.mouse.get_pressed()[0]:  
            if 196 <= mouse[0] <= 279 and 449<= mouse[1] <=483:
                '''Repeat Level'''  
                player_car.reset(game_info.difficulty, game_info.level)
                ai_car.reset(game_info.difficulty, game_info.level)
                run_countdown(genomes, config, game_info, player_car, ai_car, net)
                win_screen = False
                break
            elif 312 <= mouse[0] <= 396 and 449<= mouse[1] <=483:
                '''Next Level'''
                game_info.next_level()
                if game_info.level > game_info.levels: 
                    run_end_screen(genomes, config)
                player_car.reset(game_info.difficulty, game_info.level)
                ai_car.reset(game_info.difficulty, game_info.level)
                run_countdown(genomes, config, game_info, player_car, ai_car, net)
                win_screen = False
                break
            elif 426 <= mouse[0] <= 510 and 449<= mouse[1] <=483:
                '''Main Menu'''
                print('main_menu')
                run_main_menu(genomes, config)
                win_screen = False
                break

def run_end_screen(genomes, config): 
    WINDOW.blit(GRASS, (0,0))
    WINDOW.blit(TRACK, (0,0))
    WINDOW.blit(FINISH_LINE, (FINISH_LINE_POSITION))
    WINDOW.blit(END_SCREEN, (WIDTH/2-WIDTH/4, HEIGHT/2-HEIGHT/6)) 
    pygame.display.update()    
    end_screen = True
    while end_screen: 
        for event in pygame.event.get(): 
            if event.type == pygame.QUIT: 
                end_screen = False
                pygame.quit()
                quit()
            elif event.type == pygame.KEYDOWN: 
                if event.key == pygame.K_a: 
                    print(pygame.mouse.get_pos())

        '''End Screen Options'''
        mouse = pygame.mouse.get_pos()
        if pygame.mouse.get_pressed()[0]:  
            if 228 <= mouse[0] <= 312 and 449<= mouse[1] <=483:
                '''Main Menu'''  
                run_main_menu(genomes, config)
                end_screen = False
                break
            elif 394 <= mouse[0] <= 478 and 449<= mouse[1] <=483:
                '''Quit'''
                end_screen = False
                pygame.quit()
                quit()


'''Play_Game'''
def play_game(config_path, genome_path="Prev_Winners/20_92__5_2_0042.pkl"):
    # Load requried NEAT config
    config = neat.config.Config(neat.DefaultGenome, neat.DefaultReproduction, neat.DefaultSpeciesSet, neat.DefaultStagnation, config_path)

    # Unpickle saved winner
    with open(genome_path, "rb") as f:
        genome = pickle.load(f)

    # Convert loaded genome into required data structure
    genomes = [(1, genome)]

    # Call game with only the loaded genome
    run_main_menu(genomes, config)

'''Main Call'''
if __name__ == "__main__": 
    local_dir = os.path.dirname(__file__)
    config_path = os.path.join(local_dir, "feed_forward_config.txt") 
    play_game(config_path)