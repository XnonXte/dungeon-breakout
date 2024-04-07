import pygame
from os import path, listdir


def load_spritesheets(spritesheets_dir, width, height):
    """Loading spritesheets into a dict."""
    images = [
        image
        for image in listdir(spritesheets_dir)
        if path.isfile(path.join(spritesheets_dir, image))
    ]
    spritesheets = {}

    for image in images:
        image_path = path.join(spritesheets_dir, image)
        sprite = (
            pygame.image.load(image_path).convert_alpha()
            if image_path.endswith(".png")
            else pygame.image.load(image_path).convert()
        )
        sprites = []

        for i in range(sprite.get_width() // width):
            # Split image based on the width specified.
            image_surface = pygame.Surface((width, height), pygame.SRCALPHA, 32)
            image_rect = pygame.Rect(i * width, 0, width, height)
            image_surface.blit(sprite, (0, 0), image_rect)

            sprites.append(image_surface)

        spritesheets[image.replace(".png", "")] = sprites

    return spritesheets


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
