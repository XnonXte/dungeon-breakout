import pygame
from os import path
from pytmx import load_pygame
from config import screen, clock
from sprites import Trigger, Tile, Player, CameraGroup
from const import *


class Game:
    def main(self):
        pygame.mouse.set_visible(False)  # Disable cursor.
        tmx_data = load_pygame(path.join("maps", "tmx", "open_island.tmx"))
        camera_group = CameraGroup()
        running = True

        # Filling layers and objects into the screen.
        for layer in tmx_data.layers:
            if hasattr(layer, "data"):
                # Checks if it's a regular layer and not an object layer.
                for x, y, image in layer.tiles():
                    Tile((x * TILE_SIZE, y * TILE_SIZE), image, camera_group)

        for obj in tmx_data.objects:
            if obj.name == HAZARD_TRIGGER:
                Trigger(
                    (obj.x, obj.y),
                    obj.width,
                    obj.height,
                    camera_group,
                    HAZARD_TRIGGER,
                    HAZARD_TRIGGER_DEBUG_COLOR,
                )
            if obj.name == OBSTACLE_TRIGGER:
                Trigger(
                    (obj.x, obj.y),
                    obj.width,
                    obj.height,
                    camera_group,
                    OBSTACLE_TRIGGER,
                    OBSTACLE_TRIGGER_DEBUG_COLOR,
                )

        player_spawn = tmx_data.get_object_by_name("spawn")
        player_sprite = Player(
            (player_spawn.x, player_spawn.y), camera_group, z_index=3
        )

        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False

                if event.type == pygame.MOUSEBUTTONDOWN:
                    if event.button == 1:
                        # Mouse 1.
                        player_sprite.fire_attack()

            screen.fill(BACKGROUND_COLOR)

            camera_group.camera_draw(player_sprite)
            camera_group.update()

            pygame.display.flip()
            clock.tick(60)

        pygame.quit()
        quit(0)


if __name__ == "__main__":
    game = Game()
    game.main()
