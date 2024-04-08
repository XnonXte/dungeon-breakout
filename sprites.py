import pygame
from os import path
from utils import load_spritesheet, check_collision_direction
from const import (
    PLAYER_SPRITE_WIDTH,
    PLAYER_SPRITE_HEIGHT,
    PLAYER_VEL,
    NORMAL_ANIMATION_SPEED,
    SCREEN_WIDTH,
    SCREEN_HEIGHT,
    INTERNAL_SCREEN_WIDTH,
    INTERNAL_SCREEN_HEIGHT,
    BACKGROUND_COLOR,
    DEFAULT_SCALE,
    SCALE_SPEED,
    MIN_SCALE,
    MAX_SCALE,
    HAZARD_TRIGGER,
    OBSTACLE_TRIGGER,
    TRIGGER_DEBUG,
    SWINGING_ANIMATION_SPEED,
)


class Trigger(pygame.sprite.Sprite):
    """
    Trigger sprite class, used for all things trigger related (e.g. determining if the player is in a certain area).
    A trigger can be identified with a name.
    """

    def __init__(self, pos, width, height, group, name=None, color="Red", z_index=1):
        super().__init__(group)
        self.screen = pygame.display.get_surface()
        self.image = pygame.Surface((width, height), pygame.SRCALPHA)

        if TRIGGER_DEBUG:
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
    def __init__(self, rgba, parent_sprite, group, z_index=1):
        super().__init__(group)
        self.parent_sprite = parent_sprite
        self.width = parent_sprite.rect.width // 4
        self.height = parent_sprite.rect.height // 6
        self.image = pygame.Surface(
            (self.width * 2, self.height * 2),
            pygame.SRCALPHA,
        )
        self.rect = self.image.get_rect()
        self.z_index = z_index

        # Drawing shadow as an ellipse.
        pygame.draw.ellipse(self.image, rgba, self.image.get_rect())

    def update(self):
        # Follow parent_sprite's midbottom pos.
        self.rect.midbottom = self.parent_sprite.rect.midbottom


class Player(pygame.sprite.Sprite):
    """Player sprite class."""

    ATTACK_SPRITES = load_spritesheet(
        path.join("assets", "player", "attack"),
        PLAYER_SPRITE_WIDTH,
        PLAYER_SPRITE_HEIGHT,
    )
    DEATH_SPRITES = load_spritesheet(
        path.join("assets", "player", "death"),
        PLAYER_SPRITE_WIDTH,
        PLAYER_SPRITE_HEIGHT,
    )
    IDLE_SPRITES = load_spritesheet(
        path.join("assets", "player", "idle"),
        PLAYER_SPRITE_WIDTH,
        PLAYER_SPRITE_HEIGHT,
    )
    RUN_SPRITES = load_spritesheet(
        path.join("assets", "player", "run"),
        PLAYER_SPRITE_WIDTH,
        PLAYER_SPRITE_HEIGHT,
    )

    def __init__(self, pos, group, z_index=1):
        super().__init__(group)

        # Essential properties.
        self.image = pygame.Surface((PLAYER_SPRITE_WIDTH, PLAYER_SPRITE_HEIGHT))
        self.rect = self.image.get_rect(center=pos)
        self.mask = pygame.mask.from_surface(self.image)

        # Logic states.
        self.direction = pygame.math.Vector2()
        self.attacked = False
        self.dead = False  #! Should be temporary!

        # Animation states.
        self.animation_state = "idle"
        self.last_frame_animation_state = self.animation_state
        self.animation_direction = "down"
        self.animation_index = 0

        # Miscellaneous.
        self.shadow = Shadow((0, 0, 0, 100), self, group, z_index=2)
        self.z_index = z_index
        self.trigger_group = pygame.sprite.Group()

        self.load_trigger_group(group, self.trigger_group)

    def load_trigger_group(self, group, trigger_group):
        """Helper function to load all triggers."""
        for sprite in group:
            if sprite.__class__.__name__ == "Trigger":
                trigger_group.add(sprite)

    def get_collided_triggers(self):
        """Helper function to get the collided triggers."""
        collided_triggers = pygame.sprite.spritecollide(self, self.trigger_group, False)
        return collided_triggers

    def update_rect_and_mask(self):
        """Helper function to update rect and mask every time a change occurs."""
        self.rect = self.image.get_rect(topleft=(self.rect.x, self.rect.y))
        self.mask = pygame.mask.from_surface(self.image)

    def determine_animation_state(self):
        """Helper function to determine which animation to play."""
        if self.dead:
            self.animation_state = "death"
        elif self.attacked:
            self.animation_state = "attack"
        elif self.direction.x != 0 or self.direction.y != 0:
            self.animation_state = "run"
        else:
            self.animation_state = "idle"

    def determine_animation_direction(self):
        """Helper function to determine which direction the player is currently facing"""

        # Don't change direction while attack or death animation is playing.
        if self.attacked or self.dead:
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
        sprites = {}

        match self.animation_state:
            case "idle":
                sprites = self.IDLE_SPRITES
            case "run":
                sprites = self.RUN_SPRITES
            case "attack":
                sprites = self.ATTACK_SPRITES
            case "death":
                sprites = self.DEATH_SPRITES
            case _:
                raise NotImplementedError(self.animation_state)

        return sprites

    def handle_check_hazard_collision(self):
        """Checking hazard collision, (e.g. water)"""
        for collided_trigger in self.get_collided_triggers():
            if collided_trigger.name == HAZARD_TRIGGER:
                self.dead = True

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
        if not self.attacked:
            self.attacked = True

    def handle_movement(self):
        """Handling player 8-directional movement with a normal diagonal speed."""
        # Don't move the player when attack or death animation is playing"
        if self.attacked or self.dead:
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
        spritesheet = self.load_animation_spritesheet()
        animation_key = f"{self.animation_state}_{self.animation_direction}_40x40"
        sprites = spritesheet[animation_key]

        # Animation logic when attacking.
        if self.attacked:
            self.animation_index += SWINGING_ANIMATION_SPEED
            if self.animation_index >= len(sprites):
                self.attacked = False
        else:
            self.animation_index += NORMAL_ANIMATION_SPEED

        # Animation logic when the player is dead.
        if self.dead and self.animation_index >= len(sprites):
            self.shadow.kill()
            self.kill()

        # Reset animation index if animation state changed or reached end of sprites.
        if (
            self.animation_state != self.last_frame_animation_state
            or self.animation_index >= len(sprites)
        ):
            self.animation_index = 0

        animation_index_int = int(self.animation_index)
        self.image = sprites[animation_index_int]
        self.update_rect_and_mask()

        # Update last frame animation state.
        self.last_frame_animation_state = self.animation_state

    def update(self):
        self.handle_check_hazard_collision()
        self.handle_check_obstacle_collision()
        self.handle_animation()
        self.handle_movement()


class CameraGroup(pygame.sprite.Group):
    """Group class which supports camera, zoom, and rendering by z-index."""

    def __init__(self):
        super().__init__()
        self.screen = pygame.display.get_surface()

        # Camera offset.
        self.offset = pygame.math.Vector2()

        # Zoom setup.
        self.zoom_scale = DEFAULT_SCALE
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
        if self.zoom_scale <= MIN_SCALE:
            self.zoom_scale = MIN_SCALE
        elif self.zoom_scale >= MAX_SCALE:
            self.zoom_scale = MAX_SCALE

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
                return 1  # Default z_index.

        self.center_target_to_camera(player_sprite)
        self.zoom_keyboard_control()
        self.internal_screen.fill(BACKGROUND_COLOR)  # Prevent frame artifact.

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
