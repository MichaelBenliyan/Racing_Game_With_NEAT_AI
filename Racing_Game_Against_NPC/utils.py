import pygame

def scale_image(image, factor): 
    size = round(image.get_width() * factor), round(image.get_height() * factor) 
    return pygame.transform.scale(image, size)



def blit_rotate_center(window, image, top_left, angle):
    rotated_image = pygame.transform.rotate(image, angle)
    new_rectangle = rotated_image.get_rect(center=image.get_rect(topleft = top_left).center)
    window.blit(rotated_image, new_rectangle.topleft)
    return rotated_image, new_rectangle.topleft

def blit_text_center(window, font, text): 
    render = font.render(text, 1, (255, 255, 255))
    window.blit(render, (window.get_width()/2 - render.get_width()/2, window.get_height()/2-render.get_height()/2))

def blit_text_abovecenter(window, font, text): 
    render = font.render(text, 1, (0, 0, 0))
    window.blit(render, (window.get_width()/2-render.get_width()/2 ,window.get_height()/2+185 ))

def blit_text_subcenter(window, font, text): 
    render = font.render(text, 1, (0, 0, 0))
    window.blit(render, (window.get_width()/2-render.get_width()/2 ,window.get_height()/2-125 ))
