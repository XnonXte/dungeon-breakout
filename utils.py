import pygame
from os import path, listdir


def flip(images):
    flipped_images = []

    for image in images:
        flipped_images.append(pygame.transform.flip(image, True, False))

    return flipped_images


def load_spritesheet(spritesheet_dir, width, height, flipped=False):
    images = [
        image
        for image in listdir(spritesheet_dir)
        if path.isfile(path.join(spritesheet_dir, image))
    ]
    spritesheet = {}

    for image in images:
        image_path = path.join(spritesheet_dir, image)
        sprite = pygame.image.load(image_path).convert_alpha()
        sprites = []

        for i in range(sprite.get_width() // width):
            # Split image based on the width specified.
            image_surface = pygame.Surface((width, height), pygame.SRCALPHA)
            image_rect = pygame.Rect(i * width, 0, width, height)
            image_surface.blit(sprite, (0, 0), image_rect)

            sprites.append(image_surface)

        if flipped:
            spritesheet[image.replace(".png", "") + "_right"] = sprites
            spritesheet[image.replace(".png", "") + "_left"] = flip(sprites)
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
        collision_direction.x = (
            1 if dx > 0 else -1
        )  # Determine if it's a left or right collision.
    elif abs(dx) < abs(dy):
        collision_direction.y = (
            1 if dy > 0 else -1
        )  # Determine if it's a left or right collision.

    return collision_direction
