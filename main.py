from os import path

import pygame
from pytmx import load_pygame

from config import screen, clock
from sprites import Trigger, Tile, AnimatedPursuingEnemy, Player, CameraGroup
from const import *


class Game:
    def load_tiles_and_triggers(self, tmx_data, group):
        """Helper function to load tiles and triggers into group."""
        for layer in tmx_data.layers:
            if hasattr(layer, "data"):
                for x, y, image in layer.tiles():
                    Tile((x * TILE_SIZE, y * TILE_SIZE), image, group)
        for obj in tmx_data.objects:
            if obj.name == HAZARD_TRIGGER:
                Trigger(
                    (obj.x, obj.y),
                    obj.width,
                    obj.height,
                    group,
                    HAZARD_TRIGGER,
                    HAZARD_TRIGGER_DEBUG_COLOR,
                )
            if obj.name == OBSTACLE_TRIGGER:
                Trigger(
                    (obj.x, obj.y),
                    obj.width,
                    obj.height,
                    group,
                    OBSTACLE_TRIGGER,
                    OBSTACLE_TRIGGER_DEBUG_COLOR,
                )

    def load_enemies(self, player_sprite, tmx_data, group):
        """Helper function to load enemies into group."""
        for obj in tmx_data.objects:
            if obj.type == "enemy":
                AnimatedPursuingEnemy(
                    obj.name, (obj.x, obj.y), player_sprite, group, 3, 2
                )

    def run(self):
        """Main function to run the game."""
        # Disabling cursor.
        pygame.mouse.set_visible(False)

        tmx_data = load_pygame(path.join("maps", "tmx", "open_island.tmx"))
        camera_group = CameraGroup()

        # Load tiles and triggers into the group.
        self.load_tiles_and_triggers(tmx_data, camera_group)

        player_spawn = tmx_data.get_object_by_name(PLAYER_SPAWN)
        player_sprite = Player((player_spawn.x, player_spawn.y), camera_group, 3, 2)

        # Load enemies into the group, called after player_sprite has been initiated.
        self.load_enemies(player_sprite, tmx_data, camera_group)

        # Main loop.
        running = True
        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                if event.type == pygame.MOUSEBUTTONDOWN:
                    if event.button == 1:
                        player_sprite.fire_attack()

            # Prevent frame artifact.
            screen.fill(BACKGROUND_COLOR)

            camera_group.camera_draw(player_sprite)
            camera_group.update()
            pygame.display.flip()
            clock.tick(60)

        # Exit the program.
        pygame.quit()
        quit(0)


if __name__ == "__main__":
    game = Game()
    game.run()
