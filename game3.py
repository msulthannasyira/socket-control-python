import pygame
import sys
import random

# **Game Configuration**
WIDTH, HEIGHT = 400, 600
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
BLUE = (135, 206, 235)
GREEN = (0, 255, 0)
RED = (255, 0, 0)
GRAVITY = 0.5
BIRD_JUMP = -10
PIPE_SPEED = 3
PIPE_GAP = 150

# Font for game
pygame.init()
font = pygame.font.SysFont("Arial", 30)

# **Game Functions**
def create_pipe():
    pipe_top = random.randint(100, HEIGHT - PIPE_GAP - 100)
    pipe_bottom = pipe_top + PIPE_GAP
    return [WIDTH, pipe_top, pipe_bottom, False]

def draw_pipes(screen, pipes):
    for pipe in pipes:
        pygame.draw.rect(screen, GREEN, (pipe[0], 0, 60, pipe[1]))
        pygame.draw.rect(screen, GREEN, (pipe[0], pipe[2], 60, HEIGHT - pipe[2]))

def move_pipes(pipes):
    for pipe in pipes:
        pipe[0] -= PIPE_SPEED
    return [pipe for pipe in pipes if pipe[0] + 60 > 0]

def check_collision(bird_x, bird_y, pipes):
    if bird_y < 0 or bird_y > HEIGHT:
        return True
    for pipe in pipes:
        if bird_x + 30 > pipe[0] and bird_x < pipe[0] + 60:
            if bird_y < pipe[1] or bird_y + 30 > pipe[2]:
                return True
    return False

def draw_button(screen, text, x, y, width, height, color, text_color):
    pygame.draw.rect(screen, color, (x, y, width, height))
    button_text = font.render(text, True, text_color)
    screen.blit(button_text, (x + (width - button_text.get_width()) // 2, y + (height - button_text.get_height()) // 2))

def is_button_pressed(mouse_pos, x, y, width, height):
    return x < mouse_pos[0] < x + width and y < mouse_pos[1] < y + height

def show_game_over(screen, score):
    retry_button_x = WIDTH // 2 - 100
    retry_button_y = HEIGHT // 2 + 50  # Moved down to avoid overlap
    exit_button_x = WIDTH // 2 - 100
    exit_button_y = HEIGHT // 2 + 150  # Added margin here between the buttons
    retry_button_width = 200
    retry_button_height = 50
    exit_button_width = 200
    exit_button_height = 50

    # Game over and instructions text
    while True:
        screen.fill(BLUE)
        game_over_text = font.render("Game Over!", True, WHITE)
        score_text = font.render(f"Skor Anda: {score}", True, WHITE)
        instruction_text = font.render("Tekan spacebar agar burung lompat", True, WHITE)

        screen.blit(game_over_text, (WIDTH // 2 - game_over_text.get_width() // 2, HEIGHT // 3))
        screen.blit(score_text, (WIDTH // 2 - score_text.get_width() // 2, HEIGHT // 3 + 50))
        screen.blit(instruction_text, (WIDTH // 2 - instruction_text.get_width() // 2, HEIGHT // 3 + 100))

        draw_button(screen, "Retry", retry_button_x, retry_button_y, retry_button_width, retry_button_height, GREEN, WHITE)
        draw_button(screen, "Exit", exit_button_x, exit_button_y, exit_button_width, exit_button_height, RED, WHITE)

        pygame.display.flip()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.MOUSEBUTTONDOWN:
                if is_button_pressed(event.pos, retry_button_x, retry_button_y, retry_button_width, retry_button_height):
                    return True
                if is_button_pressed(event.pos, exit_button_x, exit_button_y, exit_button_width, exit_button_height):
                    return False

def reset_game():
    """Resets the game state before starting a new game"""
    return 50, HEIGHT // 2, 0, [], 0  # bird_x, bird_y, bird_velocity, pipes, score

def main():
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("Flappy Bird")
    clock = pygame.time.Clock()

    # Initial Game State
    bird_x, bird_y, bird_velocity, pipes, score = reset_game()

    running = True
    while running:
        screen.fill(BLUE)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE:
                    bird_velocity = BIRD_JUMP

        bird_velocity += GRAVITY
        bird_y += bird_velocity

        if not pipes or pipes[-1][0] < WIDTH - 200:
            pipes.append(create_pipe())
        pipes = move_pipes(pipes)

        if check_collision(bird_x, bird_y, pipes):
            running = False

        for pipe in pipes:
            if pipe[0] + 60 < bird_x and not pipe[3]:
                score += 1
                pipe[3] = True

        pygame.draw.circle(screen, RED, (bird_x, bird_y), 15)
        draw_pipes(screen, pipes)

        score_text = font.render(f"Skor: {score}", True, WHITE)
        screen.blit(score_text, (10, 10))

        pygame.display.flip()
        clock.tick(60)

    # Handle Game Over screen after game ends
    if not show_game_over(screen, score):
        pygame.quit()
        sys.exit()
    else:
        # Restart game after retry
        bird_x, bird_y, bird_velocity, pipes, score = reset_game()
        main()

if __name__ == "__main__":
    main()
