from os import path

import pygame

from utils import *
from const import *


class Trigger(pygame.sprite.Sprite):
    """
    Trigger sprite class, used for all things trigger related (e.g. determining if the player is in a certain area).
    A trigger can be identified with a name.
    """

    def __init__(self, pos, width, height, group, name=None, color="Red", z_index=1):
        super().__init__(group)
        self.screen = pygame.display.get_surface()
        self.image = pygame.Surface((width, height), pygame.SRCALPHA)
        if DEBUG_MODE:
            self.image.fill(color)
        self.rect = self.image.get_rect(topleft=pos)
        self.name = name
        self.z_index = z_index


class Tile(pygame.sprite.Sprite):
    """Tile sprite class, used for everything that utilizes tile."""

    def __init__(self, pos, image, group, z_index=1):
        super().__init__(group)
        self.image = image
        self.rect = self.image.get_rect(topleft=pos)
        self.z_index = z_index


class Shadow(pygame.sprite.Sprite):
    """Circular shadow beneath a parent sprite."""

    def __init__(
        self,
        rgba,
        parent_sprite,
        width_scale,
        height_scale,
        group,
        center_point="center",
        z_index=1,
    ):
        super().__init__(group)
        self.parent_sprite = parent_sprite
        self.image = pygame.Surface(
            (
                parent_sprite.image.get_width() // width_scale,
                parent_sprite.image.get_width() // height_scale,
            ),
            pygame.SRCALPHA,
        )
        self.rect = self.image.get_rect()
        self.center_point = center_point
        self.z_index = z_index

        # Drawing shadow as an ellipse.
        pygame.draw.ellipse(self.image, rgba, self.rect)

    def handle_movement(self):
        """Move the shadow at the specified center point."""
        match self.center_point:
            case "midbottom":
                self.rect.midbottom = self.parent_sprite.rect.midbottom
            case "center":
                self.rect.center = self.parent_sprite.rect.midbottom
            case _:
                raise NotImplementedError(self.center_point)

    def update(self):
        self.handle_movement()


class Entity(pygame.sprite.Sprite):
    """Base class for all entity sprite which contains health, shadow, etc."""

    def __init__(
        self,
        pos,
        image,
        health,
        group,
        shadow_rgba,
        shadow_width_scale,
        shadow_height_scale,
        shadow_center_point,
        z_index=1,
        shadow_z_index=1,
    ):
        super().__init__(group)
        self.image = image
        self.rect = self.image.get_rect(center=pos)
        self.mask = pygame.mask.from_surface(self.image)
        self.health = health
        self.dying = False
        self.shadow = Shadow(
            shadow_rgba,
            self,
            shadow_width_scale,
            shadow_height_scale,
            group,
            shadow_center_point,
            shadow_z_index,
        )
        self.trigger_group = pygame.sprite.Group()
        self.load_trigger_group(group, self.trigger_group)
        self.z_index = z_index

    def load_trigger_group(self, group, trigger_group):
        """Helper function to load all triggers."""
        for sprite in group:
            if sprite.__class__.__name__ == "Trigger":
                trigger_group.add(sprite)

    def get_collided_triggers(self):
        """Helper function to get the collided triggers."""
        collided_triggers = pygame.sprite.spritecollide(self, self.trigger_group, False)
        return collided_triggers

    def handle_check_hazard_collision(self):
        """Checking hazard collision, (e.g. water)"""
        for collided_trigger in self.get_collided_triggers():
            if collided_trigger.name == HAZARD_TRIGGER:
                self.dying = True

    def handle_check_obstacle_collision(self):
        """Checking if a vertical or horizontal collision occurs with an obstacle."""
        for collided_trigger in self.get_collided_triggers():
            if collided_trigger.name == OBSTACLE_TRIGGER:
                collision_direction = check_collision_direction(
                    self.rect, collided_trigger.rect
                )
                if collision_direction.y < 0:
                    self.rect.top = collided_trigger.rect.bottom
                elif collision_direction.y > 0:
                    self.rect.bottom = collided_trigger.rect.top
                elif collision_direction.x < 0:
                    self.rect.left = collided_trigger.rect.right
                elif collision_direction.x > 0:
                    self.rect.right = collided_trigger.rect.left

    def handle_dying(self):
        if self.health <= 0:
            self.dying = True

    def update(self):
        self.handle_check_hazard_collision()
        self.handle_check_obstacle_collision()
        self.handle_dying()


class PursuingEnemy(Entity):
    """Enemy base sprite class."""

    def __init__(
        self,
        pos,
        image,
        health,
        player_sprite,
        group,
        shadow_rgba,
        shadow_width_scale,
        shadow_height_scale,
        shadow_center_point="center",
        z_index=1,
        shadow_z_index=1,
    ):
        super().__init__(
            pos,
            image,
            health,
            group,
            shadow_rgba,
            shadow_width_scale,
            shadow_height_scale,
            shadow_center_point,
            z_index,
            shadow_z_index,
        )
        self.player_sprite = player_sprite
        self.distance_to_player = 0
        self.direction_to_player = pygame.math.Vector2()
        self.pursuing = False
        self.hit_countdown = 0

    def handle_alert_radius(self):
        """Checking if this sprite is in the alert radius or not."""
        self.distance_to_player = calculate_distance(
            self.player_sprite.rect.center, self.rect.center
        )

        # Check if the player is within the detection radius.
        self.pursuing = True if self.distance_to_player <= ENEMY_ALERT_RADIUS else False

    def handle_player_contact(self):
        """Handling mask collision with the player, check if the player is attacking or not."""
        if pygame.sprite.collide_mask(self, self.player_sprite):
            if self.player_sprite.attacking:
                self.rect.center += -(
                    self.direction_to_player * PLAYER_KNOCKBACK_DISTANCE
                )
                self.health -= PLAYER_SWORD_DAMAGE
                self.hit_countdown = ENEMY_FLASH_FRAMES
            else:

                # While the player is invisible, ignore contack damage.
                if self.player_sprite.invisibility_countdown > 0:
                    return

                self.player_sprite.rect.center += (
                    self.direction_to_player * ENEMY_KNOCKBACK_DISTANCE
                )
                self.player_sprite.health -= ENEMY_CONTACT_DAMANGE
                self.player_sprite.invisibility_countdown = PLAYER_INVISIBILITY_FRAMES

    def handle_movement(self):
        """Handling enemy movement, this is just a simple pursuing mechanics."""
        if not self.pursuing:
            return
        self.direction_to_player.x = self.player_sprite.rect.centerx - self.rect.centerx
        self.direction_to_player.y = self.player_sprite.rect.centery - self.rect.centery
        if self.direction_to_player.length != 0:
            try:
                self.direction_to_player.normalize_ip()
            except ValueError:
                pass
        self.rect.center += self.direction_to_player * ENEMY_VEL

    def handle_death(self):
        """Handling operations after enemy death."""
        if self.dying:
            self.shadow.kill()
            self.kill()

    def update(self):
        super().update()
        self.handle_alert_radius()
        self.handle_player_contact()
        self.handle_movement()
        self.handle_death()


class AnimatedPursuingEnemy(PursuingEnemy):
    """Pursuing enemy sprite class."""

    def __init__(
        self, enemy_name, pos, player_sprite, group, z_index=1, shadow_z_index=1
    ):
        self.spritesheets = split_spritesheets(
            path.join("assets", "enemies"),
            f"{enemy_name}.png",
            ENEMY_SPRITE_WIDTH,
            ENEMY_SPRITE_HEIGHT,
            flipped=True,
        )
        self.animation_direction = "right"
        self.animation_index = 0
        self.sprites = self.spritesheets[f"{enemy_name}_{self.animation_direction}"]
        image = self.sprites[self.animation_index]
        super().__init__(
            pos,
            image,
            MAX_ENEMY_HEALTH,
            player_sprite,
            group,
            SHADOW_COLOR,
            ENEMY_SHADOW_WIDTH_SCALE,
            ENEMY_SHADOW_HEIGHT_SCALE,
            "center",
            z_index,
            shadow_z_index,
        )
        self.enemy_name = enemy_name

    def update_rect_and_mask(self):
        """Helper function to update rect and mask every time a change occurs."""
        self.rect = self.image.get_rect(topleft=(self.rect.x, self.rect.y))
        self.mask = pygame.mask.from_surface(self.image)

    def determine_animation_direction(self):
        """Helper function to determine which direction the enemy is currently facing"""
        if self.direction_to_player.x > 0:
            self.animation_direction = "right"
        else:
            self.animation_direction = "left"

    def handle_flash(self):
        """Handling enemy flash when hit."""
        # TODO: Implement this somehow.
        if self.hit_countdown > 0:
            if self.hit_countdown % FLASH_STEP_FRAME == 0:
                ...
            else:
                ...
        else:
            ...

    def handle_animation(self):
        """Handling enemy animation."""
        self.determine_animation_direction()
        self.animation_index += NORMAL_ANIMATION_SPEED
        if self.animation_index >= len(
            self.spritesheets[f"{self.enemy_name}_{self.animation_direction}"]
        ):
            self.animation_index = 0
        self.sprites = self.spritesheets[
            f"{self.enemy_name}_{self.animation_direction}"
        ]
        self.image = self.sprites[int(self.animation_index)]
        self.update_rect_and_mask()

    def update(self):
        super().update()
        self.handle_animation()
        self.handle_flash()


class Player(Entity):
    """Player sprite class."""

    ATTACK_SPRITESHEETS = load_spritesheets(
        path.join("assets", "player", "attack"),
        PLAYER_SPRITE_WIDTH,
        PLAYER_SPRITE_HEIGHT,
    )
    DEATH_SPRITESHEETS = load_spritesheets(
        path.join("assets", "player", "death"),
        PLAYER_SPRITE_WIDTH,
        PLAYER_SPRITE_HEIGHT,
    )
    IDLE_SPRITESHEETS = load_spritesheets(
        path.join("assets", "player", "idle"),
        PLAYER_SPRITE_WIDTH,
        PLAYER_SPRITE_HEIGHT,
    )
    RUN_SPRITESHEETS = load_spritesheets(
        path.join("assets", "player", "run"),
        PLAYER_SPRITE_WIDTH,
        PLAYER_SPRITE_HEIGHT,
    )

    def __init__(self, pos, group, z_index=1, shadow_z_index=1):
        self.spritesheets = self.IDLE_SPRITESHEETS
        self.animation_state = "idle"
        self.last_frame_animation_state = self.animation_state
        self.animation_direction = "down"
        self.animation_index = 0
        self.sprites = self.spritesheets[
            f"{self.animation_state}_{self.animation_direction}_40x40"
        ]
        image = self.sprites[self.animation_index]
        super().__init__(
            pos,
            image,
            MAX_PLAYER_HEALTH,
            group,
            SHADOW_COLOR,
            PLAYER_SHADOW_WIDTH_SCALE,
            PLAYER_SHADOW_HEIGHT_SCALE,
            "midbottom",
            z_index,
            shadow_z_index,
        )
        self.direction = pygame.math.Vector2()
        self.attacking = False
        self.invisibility_countdown = 0
        self.trigger_group = pygame.sprite.Group()
        self.load_trigger_group(group, self.trigger_group)

    def update_rect_and_mask(self):
        """Helper function to update rect and mask every time a change occurs."""
        self.rect = self.image.get_rect(topleft=(self.rect.x, self.rect.y))
        self.mask = pygame.mask.from_surface(self.image)

    def determine_animation_state(self):
        """Helper function to determine which animation to play."""
        if self.dying:
            self.animation_state = "death"
        elif self.attacking:
            self.animation_state = "attack"
        elif self.direction.x != 0 or self.direction.y != 0:
            self.animation_state = "run"
        else:
            self.animation_state = "idle"

    def determine_animation_direction(self):
        """Helper function to determine which direction the player is currently facing"""

        # Don't change direction while attack or death animation is playing.
        if self.attacking or self.dying:
            return

        keys = pygame.key.get_pressed()
        if keys[pygame.K_w]:
            self.animation_direction = "up"
        elif keys[pygame.K_s]:
            self.animation_direction = "down"
        if keys[pygame.K_a]:
            self.animation_direction = "left"
        elif keys[pygame.K_d]:
            self.animation_direction = "right"

    def load_animation_spritesheet(self):
        """Helper function to handle player sprite based on the current animation state."""
        match self.animation_state:
            case "idle":
                self.spritesheets = self.IDLE_SPRITESHEETS
            case "run":
                self.spritesheets = self.RUN_SPRITESHEETS
            case "attack":
                self.spritesheets = self.ATTACK_SPRITESHEETS
            case "death":
                self.spritesheets = self.DEATH_SPRITESHEETS
            case _:
                raise NotImplementedError(self.animation_state)

    def handle_invisibility_frames(self):
        """Handling enemy flash when hit."""
        if self.invisibility_countdown > 0:
            if self.invisibility_countdown % FLASH_STEP_FRAME == 0:
                for sprite in self.sprites:
                    sprite.set_alpha(ALPHA_MAX)
            else:
                for sprite in self.sprites:
                    sprite.set_alpha(ALPHA_TRANSPARENT)
            self.invisibility_countdown -= 1
        else:
            for sprite in self.sprites:
                if sprite.get_alpha() != ALPHA_MAX:
                    sprite.set_alpha(ALPHA_MAX)

    def handle_check_hazard_collision(self):
        """Checking hazard collision, (e.g. water)"""
        for collided_trigger in self.get_collided_triggers():
            if collided_trigger.name == HAZARD_TRIGGER:
                self.dying = True

    def handle_check_obstacle_collision(self):
        """Checking if a vertical or horizontal collision occurs with an obstacle."""
        for collided_trigger in self.get_collided_triggers():
            if collided_trigger.name == OBSTACLE_TRIGGER:
                collision_direction = check_collision_direction(
                    self.rect, collided_trigger.rect
                )
                if collision_direction.y < 0:
                    self.rect.top = collided_trigger.rect.bottom
                elif collision_direction.y > 0:
                    self.rect.bottom = collided_trigger.rect.top
                elif collision_direction.x < 0:
                    self.rect.left = collided_trigger.rect.right
                elif collision_direction.x > 0:
                    self.rect.right = collided_trigger.rect.left

    def fire_attack(self):
        """Triggering an attack sequence, this method should only be called on top level event handler."""
        if not self.attacking:
            self.attacking = True

    def handle_movement(self):
        """Handling player 8-directional movement with a normal diagonal speed."""
        # Don't move the player when attack or death animation is playing"
        if self.attacking or self.dying:
            return

        keys = pygame.key.get_pressed()

        # Vertical movement.
        if keys[pygame.K_w]:
            self.direction.y = -1
        elif keys[pygame.K_s]:
            self.direction.y = 1
        else:
            self.direction.y = 0

        # Horizontal movement.
        if keys[pygame.K_a]:
            self.direction.x = -1
        elif keys[pygame.K_d]:
            self.direction.x = 1
        else:
            self.direction.x = 0

        # Normalize direction vector if moving diagonally.
        if self.direction.length() > 0:
            self.direction.normalize_ip()
        self.rect.center += self.direction * PLAYER_VEL

    def handle_animation(self):
        """Update the player's animation frame."""
        self.determine_animation_direction()
        self.determine_animation_state()
        self.load_animation_spritesheet()
        animation_key = f"{self.animation_state}_{self.animation_direction}_40x40"
        self.sprites = self.spritesheets[animation_key]

        # Animation logic when attacking.
        if self.attacking:
            self.animation_index += SWINGING_ANIMATION_SPEED
            if self.animation_index >= len(self.sprites):
                self.attacking = False
        else:
            self.animation_index += NORMAL_ANIMATION_SPEED

        # Animation logic when the player is dead.
        if self.dying and self.animation_index >= len(self.sprites):
            self.shadow.kill()
            self.kill()

        # Reset animation index if animation state changed or reached end of sprites.
        if (
            self.animation_state != self.last_frame_animation_state
            or self.animation_index >= len(self.sprites)
        ):
            self.animation_index = 0

        animation_index_int = int(self.animation_index)
        self.image = self.spritesheets[animation_key][animation_index_int]
        self.update_rect_and_mask()

        # Update last frame animation state.
        self.last_frame_animation_state = self.animation_state

    def update(self):
        super().update()
        self.handle_animation()
        self.handle_movement()
        self.handle_invisibility_frames()


class CameraGroup(pygame.sprite.Group):
    """Group class which supports camera, zoom, and rendering by z-index."""

    def __init__(self):
        super().__init__()
        self.screen = pygame.display.get_surface()

        # Camera offset.
        self.offset = pygame.math.Vector2()

        # Zoom setup.
        self.zoom_scale = DEFAULT_ZOOM_SCALE
        self.internal_screen = pygame.Surface(
            (INTERNAL_SCREEN_WIDTH, INTERNAL_SCREEN_HEIGHT), pygame.SRCALPHA
        )
        self.internal_rect = self.internal_screen.get_rect(
            center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2)
        )
        self.internal_screen_size = pygame.math.Vector2(
            (INTERNAL_SCREEN_WIDTH, INTERNAL_SCREEN_HEIGHT)
        )
        self.internal_offset = pygame.math.Vector2()
        self.internal_offset.x = INTERNAL_SCREEN_WIDTH // 2 - SCREEN_WIDTH // 2
        self.internal_offset.y = INTERNAL_SCREEN_HEIGHT // 2 - SCREEN_HEIGHT // 2

    def zoom_keyboard_control(self):
        """Changing the zoom scale by keyboard."""
        keys = pygame.key.get_pressed()
        if keys[pygame.K_q]:
            self.zoom_scale += SCALE_SPEED
        if keys[pygame.K_e]:
            self.zoom_scale -= SCALE_SPEED

        # Zoom cap.
        if self.zoom_scale <= MIN_ZOOM_SCALE:
            self.zoom_scale = MIN_ZOOM_SCALE
        elif self.zoom_scale >= MAX_ZOOM_SCALE:
            self.zoom_scale = MAX_ZOOM_SCALE

    def center_target_to_camera(self, target_sprite):
        """Center target to the middle of the screen."""
        self.offset.x = target_sprite.rect.centerx - SCREEN_WIDTH // 2
        self.offset.y = target_sprite.rect.centery - SCREEN_HEIGHT // 2

    def camera_draw(self, player_sprite):
        """Custom draw function akin to the default Group.draw() function with a slight tweak to the position to support camera movement and z-indexing."""

        def get_z_index(sprite):
            if hasattr(sprite, "z_index"):
                return sprite.z_index
            else:
                # Default z-index.
                return 1

        self.center_target_to_camera(player_sprite)
        self.zoom_keyboard_control()

        # Prevent frame artifact.
        self.internal_screen.fill(BACKGROUND_COLOR)

        for sprite in sorted(self.sprites(), key=get_z_index):
            offset_pos = sprite.rect.topleft - self.offset + self.internal_offset
            self.internal_screen.blit(sprite.image, offset_pos)

        # Apply the scaled screen into the main screen.
        scaled_screen = pygame.transform.scale(
            self.internal_screen, self.internal_screen_size * self.zoom_scale
        )
        scaled_rect = scaled_screen.get_rect(
            center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2)
        )
        self.screen.blit(scaled_screen, scaled_rect)
