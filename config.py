import pygame

from const import SCREEN_WIDTH, SCREEN_HEIGHT, CAPTION

pygame.init()
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption(CAPTION)
clock = pygame.time.Clock()
