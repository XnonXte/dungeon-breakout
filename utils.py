import math
from os import path, listdir

import pygame


def flip(images):
    """Flip every images in the sequence."""
    flipped_images = []
    for image in images:
        flipped_images.append(pygame.transform.flip(image, True, False))
    return flipped_images


def load_spritesheet(spritesheet_dir, width, height, scale_factor=1.0, flipped=False):
    """Load spritesheet into a dict. For both left and right direction, set `flipped` to True."""
    images = [
        image
        for image in listdir(spritesheet_dir)
        if path.isfile(path.join(spritesheet_dir, image))
    ]
    spritesheet = {}

    # Load and split image based on the width specified.
    for image in images:
        image_path = path.join(spritesheet_dir, image)
        sprite = pygame.image.load(image_path).convert_alpha()
        sprites = []
        for i in range(sprite.get_width() // width):
            image_surface = pygame.Surface((width, height), pygame.SRCALPHA)
            image_rect = pygame.Rect(i * width, 0, width, height)
            image_surface.blit(sprite, (0, 0), image_rect)
            sprites.append(pygame.transform.scale_by(image_surface, scale_factor))

        if flipped:
            spritesheet[f"{image.replace('.png', '')}_right"] = sprites
            spritesheet[f"{image.replace('.png', '')}_left"] = flip(sprites)
        else:
            spritesheet[image.replace(".png", "")] = sprites

    return spritesheet


def check_collision_direction(left_rect, right_rect):
    """Check direction of collision between two rectangles. right_rect must be a cube for this to work properly!"""
    # Calculate distances between centers.
    dx = right_rect.centerx - left_rect.centerx
    dy = right_rect.centery - left_rect.centery
    collision_direction = pygame.math.Vector2()

    # Compare the two distances and determine if it's a horizontal or vertical collision.
    if abs(dx) > abs(dy):
        collision_direction.x = 1 if dx > 0 else -1
    elif abs(dx) < abs(dy):
        collision_direction.y = 1 if dy > 0 else -1

    return collision_direction


def calculate_distance(pos_1, pos_2):
    """Function to calculate distance between two points."""
    return math.sqrt((pos_1[0] - pos_2[0]) ** 2 + (pos_1[1] - pos_2[1]) ** 2)
