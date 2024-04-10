import math
from os import path, listdir

import pygame


def flip(images):
    """Flip every images in the sequence."""
    flipped_images = []
    for image in images:
        flipped_images.append(pygame.transform.flip(image, True, False))
    return flipped_images


def load_spritesheets(spritesheets_dir, width, height, scale_factor=1.0, flipped=False):
    """Function to load multiple spritesheets into a dict. For loading both left and right direction, set `flipped` to True."""
    images = [
        image
        for image in listdir(spritesheets_dir)
        if path.isfile(path.join(spritesheets_dir, image))
    ]
    spritesheets = {}
    for image in images:
        spritesheets.update(
            split_spritesheets(
                spritesheets_dir, image, width, height, scale_factor, flipped
            )
        )
    return spritesheets


def split_spritesheets(
    spritesheet_dir,
    spritesheet_name,
    width,
    height,
    scale_factor=1.0,
    flipped=False,
):
    """Split a single spritesheet based on the width specified."""
    spritesheet_path = path.join(spritesheet_dir, spritesheet_name)
    spritesheet_surface = pygame.image.load(spritesheet_path).convert_alpha()
    spritesheets = {}
    sprites = []
    for i in range(spritesheet_surface.get_width() // width):
        sprite_surface = pygame.Surface((width, height), pygame.SRCALPHA)
        sprite_rect = pygame.Rect(i * width, 0, width, height)
        sprite_surface.blit(spritesheet_surface, (0, 0), sprite_rect)
        sprites.append(pygame.transform.scale_by(sprite_surface, scale_factor))
        if flipped:
            spritesheets[f"{spritesheet_name.replace('.png', '')}_right"] = sprites
            spritesheets[f"{spritesheet_name.replace('.png', '')}_left"] = flip(sprites)
        else:
            spritesheets[spritesheet_name.replace(".png", "")] = sprites
    return spritesheets


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
